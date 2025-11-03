"""
Data Service for Agents Service - CORRECTED for actual schema

Works with:
- switch_probability_history table (not clients.switch_probability column)
- alerts table (not insights table)
- features table (pre-computed)
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
        """Get client metadata (name, RM, sector, segment)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT client_id, name, rm, sector, segment, primary_exposure
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
                    'sector': row[3],
                    'segment': row[4],
                    'primaryExposure': row[5]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching client metadata: {e}")
            return None
    
    def get_latest_switch_prob(self, client_id: str) -> Optional[float]:
        """
        Get latest switch probability from history table.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Latest switch probability or None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT switch_prob
                FROM switch_probability_history
                WHERE client_id = %s
                ORDER BY computed_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, (client_id,))
            row = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return float(row[0]) if row else None
            
        except Exception as e:
            logger.error(f"Error fetching switch prob: {e}")
            return None
    
    def insert_switch_probability(
        self,
        client_id: str,
        switch_prob: float,
        confidence: float,
        segment: str,
        drivers: List[str],
        risk_flags: List[str]
    ):
        """
        Insert new switch probability record.
        
        Args:
            client_id: Client identifier
            switch_prob: Switch probability (0-1)
            confidence: Confidence score (0-1)
            segment: Client segment
            drivers: List of classification drivers
            risk_flags: List of risk flags
        """
        try:
            import json
            
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
            
            logger.info(f"✅ Switch prob inserted for {client_id}: {switch_prob:.3f}")
            
        except Exception as e:
            logger.error(f"Error inserting switch prob: {e}")
            raise
    
    def get_client_features(self, client_id: str) -> Optional[dict]:
        """
        Get pre-computed features for client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dict with features or None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    momentum_beta_1d,
                    momentum_beta_5d,
                    momentum_beta_20d,
                    holding_period_avg,
                    turnover,
                    aggressiveness,
                    lead_lag_alpha,
                    exposure_concentration,
                    computed_at
                FROM features
                WHERE client_id = %s
                ORDER BY computed_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, (client_id,))
            row = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if row:
                return {
                    'momentum_beta_1d': float(row[0]) if row[0] else 0.0,
                    'momentum_beta_5d': float(row[1]) if row[1] else 0.0,
                    'momentum_beta_20d': float(row[2]) if row[2] else 0.0,
                    'holding_period_avg': float(row[3]) if row[3] else 0.0,
                    'turnover': float(row[4]) if row[4] else 0.0,
                    'aggressiveness': float(row[5]) if row[5] else 0.0,
                    'lead_lag_alpha': float(row[6]) if row[6] else 0.0,
                    'exposure_concentration': row[7] if row[7] else {},
                    'computed_at': row[8].isoformat() if row[8] else None
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching features: {e}")
            return None
    
    def get_trades(
        self,
        client_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Get trades for a client."""
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
        """Get current positions for a client."""
        try:
            conn = self._get_connection()
            
            query = """
                SELECT 
                    client_id,
                    instrument,
                    net_position as "netPosition",
                    gross_position as "grossPosition",
                    leverage,
                    unrealized_pnl as "unrealizedPnl",
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
        """Get headlines for instruments."""
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
        Includes latest switch probability from history table.
        """
        try:
            conn = self._get_connection()
            
            # Join with latest switch probability
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
    
    def get_client_timeline(
        self,
        client_id: str,
        months: int = 6
    ) -> List[dict]:
        """Get historical regime timeline for client."""
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
    
    def get_client_alerts(
        self,
        client_id: str,
        limit: int = 20,
        acknowledged: Optional[bool] = None
    ) -> List[dict]:
        """
        Get recent alerts for client (uses alerts table, not insights).
        
        Args:
            client_id: Client identifier
            limit: Max alerts
            acknowledged: Filter by acknowledgment status
            
        Returns:
            List of alert dicts
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
            """
            
            params = [client_id]
            
            if acknowledged is not None:
                query += " AND acknowledged = %s"
                params.append(acknowledged)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append({
                    'id': row[0],
                    'alertType': row[1],
                    'oldSwitchProb': float(row[2]) if row[2] else None,
                    'newSwitchProb': float(row[3]) if row[3] else None,
                    'reason': row[4],
                    'severity': row[5],
                    'acknowledged': row[6],
                    'timestamp': row[7].isoformat() if row[7] else None
                })
            
            cursor.close()
            conn.close()
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return []
