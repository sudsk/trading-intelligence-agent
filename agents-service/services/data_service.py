"""
Data Service for Agents Service - CLEANED VERSION

This service handles AGENT STATE only (PostgreSQL):
- switch_probability_history
- alerts

Core data (trades, positions, headlines) now comes from MCP servers via mcp_data_service.py
"""
import os
import psycopg2
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)


class DataService:
    """Database access service for agent state (PostgreSQL)."""
    
    def __init__(self):
        """Initialize database connection."""
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            logger.warning("DATABASE_URL not set, using default")
            self.database_url = 'postgresql://postgres:postgres@localhost:5432/trading_intelligence'
        
        self._test_connection()
    
    def _test_connection(self):
        """Test database connection."""
        try:
            conn = psycopg2.connect(self.database_url)
            conn.close()
            logger.info("✅ Database connection successful")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            # Don't raise - allow service to start even if DB is down
    
    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.database_url)
    
    # ========================================================================
    # Switch Probability History
    # ========================================================================
    
    def save_switch_probability(
        self,
        client_id: str,
        switch_prob: float,
        confidence: float,
        segment: str,
        drivers: List[str],
        risk_flags: List[str]
    ) -> None:
        """
        Save switch probability to history table.
        
        Args:
            client_id: Client identifier
            switch_prob: Switch probability (0.15-0.85)
            confidence: Confidence score (0.0-1.0)
            segment: Segment classification
            drivers: List of key drivers
            risk_flags: List of risk flags
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO switch_probability_history 
                (client_id, switch_prob, confidence, segment, drivers, risk_flags, computed_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
            """
            
            cursor.execute(query, (
                client_id,
                switch_prob,
                confidence,
                segment,
                json.dumps(drivers),
                json.dumps(risk_flags),
                datetime.utcnow()
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Saved switch probability for {client_id}: {switch_prob}")
            
        except Exception as e:
            logger.error(f"❌ Error saving switch probability: {e}")
            # Don't raise - this is nice-to-have
    
    def get_switch_probability_history(
        self,
        client_id: str,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get historical switch probabilities for a client.
        
        Args:
            client_id: Client identifier
            limit: Max number of records
            
        Returns:
            List of historical switch probabilities
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    switch_prob,
                    confidence,
                    segment,
                    drivers,
                    risk_flags,
                    computed_at
                FROM switch_probability_history
                WHERE client_id = %s
                ORDER BY computed_at DESC
                LIMIT %s
            """
            
            cursor.execute(query, (client_id, limit))
            rows = cursor.fetchall()
            
            history = []
            for row in rows:
                history.append({
                    'switch_prob': float(row[0]) if row[0] else None,
                    'confidence': float(row[1]) if row[1] else None,
                    'segment': row[2],
                    'drivers': row[3],  # Already JSONB
                    'risk_flags': row[4],  # Already JSONB
                    'computed_at': row[5].isoformat() if row[5] else None
                })
            
            cursor.close()
            conn.close()
            
            return history
            
        except Exception as e:
            logger.error(f"❌ Error fetching switch probability history: {e}")
            return []
    
