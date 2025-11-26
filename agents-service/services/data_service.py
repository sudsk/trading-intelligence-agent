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
    
    # ========================================================================
    # Alerts
    # ========================================================================
    
    def create_alert(
        self,
        client_id: str,
        alert_type: str,
        old_switch_prob: Optional[float] = None,
        new_switch_prob: Optional[float] = None,
        reason: str = "",
        severity: str = "INFO"
    ) -> None:
        """
        Create an alert.
        
        Args:
            client_id: Client identifier
            alert_type: Type of alert
            old_switch_prob: Previous switch probability
            new_switch_prob: New switch probability
            reason: Alert reason/description
            severity: Severity level (INFO, WARNING, CRITICAL)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO alerts 
                (client_id, alert_type, old_switch_prob, new_switch_prob, reason, severity)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                client_id,
                alert_type,
                old_switch_prob,
                new_switch_prob,
                reason,
                severity
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Created alert for {client_id}: {alert_type}")
            
        except Exception as e:
            logger.error(f"❌ Error creating alert: {e}")
            # Don't raise - alerts are nice-to-have
    
    def get_recent_alerts(
        self,
        client_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent alerts.
        
        Args:
            client_id: Optional client filter
            limit: Max number of alerts
            
        Returns:
            List of recent alerts
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if client_id:
                query = """
                    SELECT 
                        id,
                        client_id,
                        alert_type,
                        old_switch_prob,
                        new_switch_prob,
                        reason,
                        severity,
                        acknowledged,
                        created_at
                    FROM alerts
                    WHERE client_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(query, (client_id, limit))
            else:
                query = """
                    SELECT 
                        id,
                        client_id,
                        alert_type,
                        old_switch_prob,
                        new_switch_prob,
                        reason,
                        severity,
                        acknowledged,
                        created_at
                    FROM alerts
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
            
            rows = cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append({
                    'id': row[0],
                    'client_id': row[1],
                    'alert_type': row[2],
                    'old_switch_prob': float(row[3]) if row[3] else None,
                    'new_switch_prob': float(row[4]) if row[4] else None,
                    'reason': row[5],
                    'severity': row[6],
                    'acknowledged': row[7],
                    'created_at': row[8].isoformat() if row[8] else None
                })
            
            cursor.close()
            conn.close()
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error fetching alerts: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: int) -> bool:
        """
        Mark an alert as acknowledged.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Success status
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                UPDATE alerts 
                SET acknowledged = TRUE
                WHERE id = %s
            """
            
            cursor.execute(query, (alert_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Acknowledged alert: {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error acknowledging alert: {e}")
            return False
