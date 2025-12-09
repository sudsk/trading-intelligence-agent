"""
Data Service for API Façade - CLEANED VERSION

This service handles AGENT STATE only (PostgreSQL):
- alerts (for insights feed)
- actions (for action logging and history)

Core data (clients, positions, trades) now comes from MCP servers via agents-service.
"""
import os
import psycopg2
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DataService:
    """Database access service for API façade."""
    
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
    # Insights (mapped from alerts table)
    # ========================================================================
    
    def get_client_insights(
        self,
        client_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent alerts for client (displayed as "insights" in UI).
        
        Note: Your schema uses 'alerts' table, we map it to 'insights' for UI.
        
        Args:
            client_id: Client identifier
            limit: Max number of insights
            
        Returns:
            List of insights (alerts)
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
                # Map alert fields to insight UI format
                insights.append({
                    'insightId': str(row[0]),
                    'type': 'ALERT',
                    'title': row[1],  # alert_type becomes title
                    'description': row[4],  # reason becomes description
                    'timestamp': row[7].isoformat() if row[7] else None,
                    'severity': row[5],
                    'acknowledged': row[6],
                    'metadata': {
                        'old_switch_prob': float(row[2]) if row[2] else None,
                        'new_switch_prob': float(row[3]) if row[3] else None
                    }
                })
            
            cursor.close()
            conn.close()
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Error fetching insights: {e}")
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
        Add an alert (displayed as "insight" in UI).
        
        Args:
            client_id: Client identifier
            type: Insight type (mapped to alert_type)
            title: Insight title (mapped to alert_type)
            description: Insight description (mapped to reason)
            severity: Severity level
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
            
            logger.info(f"✅ Added insight for {client_id}: {title}")
            
        except Exception as e:
            logger.error(f"❌ Error adding insight: {e}")
            # Don't raise - insights are nice-to-have
    
    # ========================================================================
    # Actions
    # ========================================================================
    
    def log_action(
        self,
        action_id: str,  # Will be ignored - PostgreSQL generates UUID
        client_id: str,
        action_type: str,
        title: str,
        description: Optional[str] = None,
        products: Optional[List[str]] = None,
        rm: Optional[str] = None
    ) -> str:
        """
        Log an action to database.
        
        Args:
            action_id: Ignored (PostgreSQL generates UUID)
            client_id: Client identifier
            action_type: Type of action
            title: Action title
            description: Action description
            products: List of products (combined into single string)
            rm: Relationship manager name
            
        Returns:
            Generated UUID as string
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Note: id is auto-generated as UUID
            # Schema has single 'product' column, not array
            query = """
                INSERT INTO actions 
                (client_id, action_type, product, description, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """
            
            # Combine products into single string
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
            
            logger.info(f"✅ Action logged: {generated_id} for {client_id}")
            
            return str(generated_id)
            
        except Exception as e:
            logger.error(f"❌ Error logging action: {e}")
            raise
    
    def get_client_actions(
        self,
        client_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get action history for client.
        
        Args:
            client_id: Client identifier
            limit: Max number of actions
            
        Returns:
            List of actions with status and outcome
        """
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
                    outcome_description,
                    created_at,
                    updated_at
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
                    'outcomeDescription': row[6],
                    'timestamp': row[7].isoformat() if row[7] else None,
                    'updatedAt': row[8].isoformat() if row[8] else None
                })
            
            cursor.close()
            conn.close()
            
            return actions
            
        except Exception as e:
            logger.error(f"❌ Error fetching actions: {e}")
            return []
    
    def update_action_outcome(
        self,
        action_id: str,
        outcome: str,
        outcome_description: Optional[str] = None
    ) -> bool:
        """
        Update action outcome (for Memory Bank learning).
        
        Args:
            action_id: Action UUID
            outcome: Outcome status (e.g., 'success', 'failed', 'pending')
            outcome_description: Optional outcome details
            
        Returns:
            Success status
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                UPDATE actions 
                SET outcome = %s,
                    outcome_description = %s,
                    updated_at = %s,
                    status = CASE 
                        WHEN %s IN ('success', 'failed') THEN 'completed'
                        ELSE status
                    END
                WHERE id = %s::uuid
            """
            
            cursor.execute(query, (
                outcome,
                outcome_description,
                datetime.utcnow(),
                outcome,
                action_id
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Updated action outcome: {action_id} -> {outcome}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating action outcome: {e}")
            return False
    
    def get_all_actions(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all actions (for admin view or Memory Bank analysis).
        
        Args:
            status: Optional status filter
            limit: Max number of actions
            
        Returns:
            List of all actions
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if status:
                query = """
                    SELECT 
                        id,
                        client_id,
                        action_type,
                        product,
                        description,
                        status,
                        outcome,
                        created_at
                    FROM actions
                    WHERE status = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(query, (status, limit))
            else:
                query = """
                    SELECT 
                        id,
                        client_id,
                        action_type,
                        product,
                        description,
                        status,
                        outcome,
                        created_at
                    FROM actions
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
            
            rows = cursor.fetchall()
            
            actions = []
            for row in rows:
                actions.append({
                    'actionId': str(row[0]),
                    'clientId': row[1],
                    'actionType': row[2],
                    'products': row[3].split(', ') if row[3] else [],
                    'description': row[4],
                    'status': row[5],
                    'outcome': row[6],
                    'timestamp': row[7].isoformat() if row[7] else None
                })
            
            cursor.close()
            conn.close()
            
            return actions
            
        except Exception as e:
            logger.error(f"❌ Error fetching all actions: {e}")
            return []
            
    def get_client_timeline(
        self,
        client_id: str,
        months: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Get historical regime timeline for client.
        
        Args:
            client_id: Client identifier
            months: Number of months of history
            
        Returns:
            List of regime periods
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            months = 12 # For demo
            
            # Query columns that actually exist in the table
            query = """
                SELECT 
                    segment,
                    period,
                    description,
                    start_date,
                    end_date
                FROM client_regimes
                WHERE client_id = %s
                  ---AND start_date > CURRENT_DATE - INTERVAL '{months} months'
                ORDER BY start_date DESC
            """
            
            cursor.execute(query, (client_id,))
            rows = cursor.fetchall()
            
            timeline = []
            for row in rows:
                timeline.append({
                    'segment': row[0],           # segment
                    'period': row[1],            # period (already formatted)
                    'description': row[2] or 'Active regime',  # description
                    'start_date': row[3].isoformat() if row[3] else None,
                    'end_date': row[4].isoformat() if row[4] else None
                })
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Retrieved {len(timeline)} timeline events")
            return timeline
            
        except Exception as e:
            logger.error(f"❌ Error fetching timeline: {e}")
            return []


    async def get_client_profile_from_db(self, client_id: str) -> Dict[str, Any]:
        """
        Get latest cached client profile from database.
        
        Returns pre-computed analysis results including:
        - segment, switchProb, confidence from switch_probability_history
        - media data from latest media analysis
        - recommendations from nba_recommendations
        - analyzed_at timestamp (computed_at field)
        """
        query = """
            WITH latest_analysis AS (
                SELECT 
                    client_id,
                    segment,
                    switch_prob,
                    confidence,
                    drivers,
                    risk_flags,
                    computed_at
                FROM switch_probability_history
                WHERE client_id = $1
                ORDER BY computed_at DESC
                LIMIT 1
            ),
            latest_media AS (
                SELECT 
                    pressure,
                    sentiment_score,
                    headlines,
                    analyzed_at
                FROM media_analysis
                WHERE client_id = $1
                ORDER BY analyzed_at DESC
                LIMIT 1
            ),
            latest_recs AS (
                SELECT 
                    recommendations,
                    generated_at
                FROM nba_recommendations
                WHERE client_id = $1
                ORDER BY generated_at DESC
                LIMIT 1
            )
            SELECT 
                la.*,
                lm.pressure as media_pressure,
                lm.sentiment_score,
                lm.headlines,
                lr.recommendations
            FROM latest_analysis la
            LEFT JOIN latest_media lm ON TRUE
            LEFT JOIN latest_recs lr ON TRUE
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, client_id)
            
            if not row:
                return None
            
            # Get client metadata from MCP
            client_data = self.mcp_service.get_client(client_id)
            
            return {
                "clientId": client_id,
                "rm": client_data.get("rm", "Unknown"),
                "segment": row["segment"],
                "switchProb": float(row["switch_prob"]),
                "confidence": float(row["confidence"]),
                "drivers": row["drivers"] or [],
                "riskFlags": row["risk_flags"] or [],
                "primaryExposure": client_data.get("primary_exposure", "N/A"),
                "analyzed_at": row["computed_at"].isoformat(),
                "media": {
                    "pressure": row["media_pressure"] or "UNKNOWN",
                    "sentiment": float(row["sentiment_score"] or 0),
                    "headlines": row["headlines"] or []
                },
                "recommendations": row["recommendations"] or []
            }
    
    
    async def store_client_profile(self, client_id: str, profile: Dict[str, Any]):
        """
        Store fresh analysis results in database.
        
        Updates:
        - switch_probability_history
        - media_analysis
        - nba_recommendations
        """
        from datetime import datetime
        
        now = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Store segmentation analysis
                await conn.execute("""
                    INSERT INTO switch_probability_history 
                    (client_id, segment, switch_prob, confidence, drivers, risk_flags, computed_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, 
                    client_id,
                    profile["segment"],
                    profile["switchProb"],
                    profile["confidence"],
                    profile.get("drivers", []),
                    profile.get("riskFlags", []),
                    now
                )
                
                # Store media analysis
                if "media" in profile:
                    await conn.execute("""
                        INSERT INTO media_analysis
                        (client_id, pressure, sentiment_score, headlines, analyzed_at)
                        VALUES ($1, $2, $3, $4, $5)
                    """,
                        client_id,
                        profile["media"].get("pressure"),
                        profile["media"].get("sentiment", 0),
                        profile["media"].get("headlines", []),
                        now
                    )
                
                # Store recommendations
                if "recommendations" in profile:
                    await conn.execute("""
                        INSERT INTO nba_recommendations
                        (client_id, recommendations, generated_at)
                        VALUES ($1, $2, $3)
                    """,
                        client_id,
                        profile.get("recommendations", []),
                        now
                    )
        
        # Add analyzed_at to profile for response
        profile["analyzed_at"] = now.isoformat()
