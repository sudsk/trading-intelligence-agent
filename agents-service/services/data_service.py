"""
Data Service for Agents Service

Provides database access for agents. Simplified version focused on read operations.
"""
import os
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class DataService:
    """Database access service for agents."""
    
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
            raise
    
    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.database_url)
    
    def get_client_metadata(self, client_id: str) -> Optional[dict]:
        """
        Get client metadata (name, RM, sector).
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dict with client metadata or None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT client_id, name, rm, sector
                FROM clients
                WHERE client_id = %s
            """
            
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
    
    def get_trades(
        self,
        client_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get trades for a client.
        
        Args:
            client_id: Client identifier
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            DataFrame with trades
        """
        try:
            conn = self._get_connection()
            
            query = """
                SELECT 
                    trade_id,
                    client_id,
                    instrument,
                    side,
                    quantity,
                    price,
                    timestamp,
                    order_type as "orderType",
                    venue
                FROM trades
                WHERE client_id = %s
            """
            
            params = [client_id]
            
            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC"
            
            df = pd.read_sql(query, conn, params=params)
            conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return pd.DataFrame()
    
    def get_positions(self, client_id: str) -> pd.DataFrame:
        """
        Get current positions for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            DataFrame with positions
        """
        try:
            conn = self._get_connection()
            
            query = """
                SELECT 
                    client_id,
                    instrument,
                    net_position as "netPosition",
                    gross_position as "grossPosition",
                    average_price as "averagePrice",
                    market_value as "marketValue",
                    updated_at as "updatedAt"
                FROM positions
                WHERE client_id = %s
                AND net_position != 0
            """
            
            df = pd.read_sql(query, conn, params=[client_id])
            conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return pd.DataFrame()
    
    def get_headlines(
        self,
        instruments: List[str],
        start_time: Optional[datetime] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get headlines for instruments.
        
        Args:
            instruments: List of instrument symbols
            start_time: Start time (optional)
            limit: Max headlines to return
            
        Returns:
            DataFrame with headlines
        """
        try:
            if not instruments:
                return pd.DataFrame()
            
            conn = self._get_connection()
            
            query = """
                SELECT 
                    headline_id as "headlineId",
                    instrument,
                    title,
                    source,
                    timestamp,
                    sentiment,
                    sentiment_score as "sentimentScore"
                FROM headlines
                WHERE instrument = ANY(%s)
            """
            
            params = [instruments]
            
            if start_time:
                query += " AND timestamp >= %s"
                params.append(start_time)
            
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            df = pd.read_sql(query, conn, params=params)
            conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching headlines: {e}")
            return pd.DataFrame()
    
    def get_clients_list(
        self,
        search: Optional[str] = None,
        segment: Optional[str] = None,
        rm: Optional[str] = None,
        limit: int = 50
    ) -> pd.DataFrame:
        """
        Get list of clients with filters.
        
        Args:
            search: Search term (name or client_id)
            segment: Filter by segment
            rm: Filter by RM
            limit: Max results
            
        Returns:
            DataFrame with clients
        """
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
    
    def get_client_timeline(
        self,
        client_id: str,
        months: int = 6
    ) -> List[dict]:
        """
        Get historical regime timeline for client.
        
        Args:
            client_id: Client identifier
            months: Number of months to look back
            
        Returns:
            List of timeline events
        """
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
                WHERE client_id = %s
                AND start_date >= %s
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
        Get recent insights/actions for client.
        
        Args:
            client_id: Client identifier
            limit: Max insights
            
        Returns:
            List of insight dicts
        """
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