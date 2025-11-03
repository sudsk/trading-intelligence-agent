"""
Data Service for API Façade

Handles database operations for actions, insights, and client queries.
"""
import os
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class DataService:
    """Database access service for API façade."""
    
    def __init__(self):
        """Initialize database connection."""
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            logger.warning("DATABASE_URL not set, using default")
            self.database_url = 'postgresql://postgres:password@localhost:5432/trading_intelligence'
        
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
    # Client Queries
    # ========================================================================
    
    def get_client_metadata(self, client_id: str) -> Optional[dict]:
        """Get client metadata."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT client_id, name, rm, sector FROM clients WHERE client_id = %s"
            cursor.execute(query, (client_id,))
            row = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if row:
                return {
                    'clientId': row[0],
                    'name': row[1],
                    'rm': row[2],
                    'sector': row[3]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error fetching client metadata: {e}")
            return None
    
    def get_clients_list(
        self,
        search: Optional[str] = None,
        segment: Optional[str] = None,
        rm: Optional[str] = None,
        limit: int = 50
    ) -> pd.DataFrame:
        """Get list of clients with filters."""
        try:
            conn = self._get_connection()
            
            query = """
                SELECT 
                    client_id,
                    name,
                    rm,
                    sector,
                    segment,
                    switch_probability as "switchProbability"
                FROM clients
                WHERE 1=1
            """
            
            params = []
            
            if search:
                query += " AND (name ILIKE %s OR client_id ILIKE %s)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            if segment:
                query += " AND segment = %s"
                params.append(segment)
            
            if rm:
                query += " AND rm = %s"
                params.append(rm)
            
            query += " ORDER BY switch_probability DESC LIMIT %s"
            params.append(limit)
            
            df = pd.read_sql(query, conn, params=params if params else None)
            conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching clients list: {e}")
            return pd.DataFrame()
    
    def get_positions(self, client_id: str) -> pd.DataFrame:
        """Get current positions for a client."""
        try:
            conn = self._get_connection()
            
            query = """
                SELECT 
                    instrument,
                    net_position as "netPosition",
                    gross_position as "grossPosition"
                FROM positions
                WHERE client_id = %s AND net_position != 0
            """
            
            df = pd.read_sql(query, conn, params=[client_id])
            conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return pd.DataFrame()
    
    # ========================================================================
    # Timeline & Insights
    # ========================================================================
    
    def get_client_timeline(
        self,
        client_id: str,
        months: int = 6
    ) -> List[dict]:
        """Get historical regime timeline."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now() - timedelta(days=months * 30)
            
            query = """
                SELECT 
                    regime_id,
                    segment,
                    start_date,
                    end_date,
                    confidence,
                    notes
                FROM client_regimes
                WHERE client_id = %s AND start_date >= %s
                ORDER BY start_date ASC
            """
            
            cursor.execute(query, (client_id, start_date))
            rows = cursor.fetchall()
            
            timeline = []
            for row in rows:
                timeline.append({
                    'regimeId': row[0],
                    'segment': row[1],
                    'startDate': row[2].isoformat() if row[2] else None,
                    'endDate': row[3].isoformat() if row[3] else None,
                    'confidence': float(row[4]) if row[4] else 0.0,
                    'notes': row[5]
                })
            
            cursor.close()
            conn.close()
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error fetching timeline: {e}")
            return []
    
    def get_client_insights(
        self,
        client_id: str,
        limit: int = 20
    ) -> List[dict]:
        """Get recent insights/actions."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    insight_id,
                    type,
                    title,
                    description,
                    timestamp,
                    severity
                FROM insights
                WHERE client_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            
            cursor.execute(query, (client_id, limit))
            rows = cursor.fetchall()
            
            insights = []
            for row in rows:
                insights.append({
                    'insightId': row[0],
                    'type': row[1],
                    'title': row[2],
                    'description': row[3],
                    'timestamp': row[4].isoformat() if row[4] else None,
                    'severity': row[5]
                })
            
            cursor.close()
            conn.close()
            
            return insights
            
        except Exception as e:
            logger.error(f"Error fetching insights: {e}")
            return []
    
    # ========================================================================
    # Actions
    # ========================================================================
    
    def log_action(
        self,
        action_id: str,
        client_id: str,
        action_type: str,
        title: str,
        description: Optional[str] = None,
        products: Optional[List[str]] = None,
        rm: Optional[str] = None
    ) -> None:
        """
        Log an action to database.
        
        Args:
            action_id: Unique action identifier
            client_id: Client identifier
            action_type: Type of action (PROACTIVE_OUTREACH, etc.)
            title: Action title
            description: Detailed description
            products: List of products proposed
            rm: Relationship manager who took action
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO actions 
                (action_id, client_id, action_type, title, description, products, rm, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            products_str = ','.join(products) if products else None
            
            cursor.execute(query, (
                action_id,
                client_id,
                action_type,
                title,
                description,
                products_str,
                rm,
                datetime.utcnow()
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Action logged: {action_id}")
            
        except Exception as e:
            logger.error(f"Error logging action: {e}")
            raise
    
    def get_client_actions(
        self,
        client_id: str,
        limit: int = 20
    ) -> List[dict]:
        """Get action history for client."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    action_id,
                    action_type,
                    title,
                    description,
                    products,
                    rm,
                    timestamp,
                    outcome
                FROM actions
                WHERE client_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            
            cursor.execute(query, (client_id, limit))
            rows = cursor.fetchall()
            
            actions = []
            for row in rows:
                actions.append({
                    'actionId': row[0],
                    'actionType': row[1],
                    'title': row[2],
                    'description': row[3],
                    'products': row[4].split(',') if row[4] else [],
                    'rm': row[5],
                    'timestamp': row[6].isoformat() if row[6] else None,
                    'outcome': row[7]
                })
            
            cursor.close()
            conn.close()
            
            return actions
            
        except Exception as e:
            logger.error(f"Error fetching actions: {e}")
            return []
    
    def add_insight(
        self,
        client_id: str,
        type: str,
        title: str,
        description: str,
        severity: str = 'INFO'
    ) -> None:
        """Add an insight to the feed."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO insights 
                (client_id, type, title, description, severity, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                client_id,
                type,
                title,
                description,
                severity,
                datetime.utcnow()
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error adding insight: {e}")
            # Don't raise - insights are nice-to-have