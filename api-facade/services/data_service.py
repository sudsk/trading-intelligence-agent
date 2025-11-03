"""
Data Service for API Façade - CORRECTED for actual schema

Works with:
- switch_probability_history table
- alerts table (not insights)
- actions table with UUID
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
            
            query = "SELECT client_id, name, rm, sector, segment FROM clients WHERE client_id = %s"
            cursor.execute(query, (client_id,))
            row = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if row:
                return {
                    'clientId': row[0],
                    'name': row[1],
                    'rm': row[2],
                    'sector': row[3],
                    'segment': row[4]
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
            
            # Get latest switch probability from history table
            query = """
                SELECT DISTINCT ON (c.client_id)
                    c.client_id,
                    c.name,
                    c.rm,
                    c.sector,
                    c.segment,
                    sph.switch_prob as "switchProbability"
                FROM clients c
                LEFT JOIN LATERAL (
                    SELECT switch_prob
                    FROM switch_probability_history
                    WHERE client_id = c.client_id
                    ORDER BY computed_at DESC
                    LIMIT 1
                ) sph ON true
                WHERE 1=1
            """
            
            params = []
            
            if search:
                query += " AND (c.name ILIKE %s OR c.client_id ILIKE %s)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            if segment:
                query += " AND c.segment = %s"
                params.append(segment)
            
            if rm:
                query += " AND c.rm = %s"
                params.append(rm)
            
            query += " ORDER BY c.client_id, sph.switch_prob DESC NULLS LAST LIMIT %s"
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
    # Timeline & Alerts (not insights!)
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
        """
        Get recent alerts for client (using alerts table).
        
        Note: Your schema uses 'alerts' not 'insights'
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    id,
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
            rows = cursor.fetchall()
            
            insights = []
            for row in rows:
                insights.append({
                    'insightId': str(row[0]),
                    'type': 'ALERT',  # Map to insight type
                    'title': row[1],  # alert_type becomes title
                    'description': row[4],  # reason becomes description
                    'timestamp': row[7].isoformat() if row[7] else None,
                    'severity': row[5],
                    'acknowledged': row[6]
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
        action_id: str,  # Will be ignored, using UUID
        client_id: str,
        action_type: str,
        title: str,
        description: Optional[str] = None,
        products: Optional[List[str]] = None,
        rm: Optional[str] = None
    ) -> str:
        """
        Log an action to database.
        
        Returns:
            Generated UUID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Note: id is auto-generated as UUID
            query = """
                INSERT INTO actions 
                (client_id, action_type, product, description, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """
            
            # Combine products into single string (schema has single 'product' column)
            product_str = ', '.join(products) if products else None
            
            # Use title as part of description if description not provided
            full_description = description if description else title
            
            cursor.execute(query, (
                client_id,
                action_type,
                product_str,
                full_description,
                'pending'
            ))
            
            generated_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Action logged: {generated_id}")
            
            return str(generated_id)
            
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
                    id,
                    action_type,
                    product,
                    description,
                    status,
                    outcome,
                    created_at
                FROM actions
                WHERE client_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            
            cursor.execute(query, (client_id, limit))
            rows = cursor.fetchall()
            
            actions = []
            for row in rows:
                actions.append({
                    'actionId': str(row[0]),
                    'actionType': row[1],
                    'products': row[2].split(', ') if row[2] else [],
                    'description': row[3],
                    'status': row[4],
                    'outcome': row[5],
                    'timestamp': row[6].isoformat() if row[6] else None
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
        """
        Add an alert (your schema uses alerts, not insights).
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO alerts 
                (client_id, alert_type, reason, severity)
                VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                client_id,
                title,  # alert_type
                description,  # reason
                severity
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error adding alert: {e}")
            # Don't raise - alerts are nice-to-have
