"""
Data Service for API Façade

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
import httpx, json

logger = logging.getLogger(__name__)


class DataService:
    """Database access service for API façade."""
    
    def __init__(self):
        """Initialize database connection."""
        self.client_server_url = os.getenv('MCP_CLIENT_SERVER_URL', 'http://localhost:3005')
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
    # Insights 
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
                    type,
                    severity,
                    title,
                    reason,
                    old_switch_prob,
                    new_switch_prob,
                    action_type,
                    products,
                    rm,
                    action_id,
                    outcome_status,
                    acknowledged,
                    created_at
                FROM insights
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
                    'type': row[1],  # SIGNAL, ACTION, OUTCOME, ALERT
                    'severity': row[2],
                    'title': row[3],
                    'description': row[4],  # reason column
                    'timestamp': row[13].isoformat() if row[13] else None,
                    'acknowledged': row[12],
                    'metadata': {
                        'old_switch_prob': float(row[5]) if row[5] else None,
                        'new_switch_prob': float(row[6]) if row[6] else None,
                        'action_type': row[7],
                        'products': row[8],
                        'rm': row[9],
                        'action_id': row[10],
                        'outcome_status': row[11]
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
        severity: str = 'INFO',
        action_type: str = None,
        products: List[str] = None,
        rm: str = None
    ) -> None:
        """Add an insight (SIGNAL, ACTION, OUTCOME, or ALERT)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Convert products list to comma-separated string
            products_str = ', '.join(products) if products else None
        
            query = """
                INSERT INTO insights 
                (client_id, type, severity, title, reason, action_type, products, rm)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            cursor.execute(query, (
                client_id,
                type,
                severity,
                title[:200] if title else None,  # Truncate to 200
                description[:1000] if description else None,  # Truncate
                action_type,
                products_str[:500] if products_str else None,  # Truncate
                rm
            ))

            insight_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Added insight for {client_id}: {title}")
            return insight_id
            
        except Exception as e:
            logger.error(f"❌ Error adding insight: {e}")
            return None
    
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

    def _call_mcp_server(self, server_url: str, tool_name: str, arguments: dict) -> dict:
        """Call MCP server directly via HTTP"""
       
        try:
            request_body = {
                "tool_name": tool_name,
                "arguments": arguments
            }
            
            #logger.info(f"🔗 MCP Request to {server_url}/call_tool")
            #logger.info(f"📤 Request body: {json.dumps(request_body, indent=2)}")
            
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    f"{server_url}/call_tool",
                    json=request_body
                )
                
                logger.info(f"📥 Response status: {response.status_code}")
                
                response.raise_for_status()
                result = response.json()
                
                #logger.info(f"✅ Full response structure: {json.dumps(result, indent=2)}")
                
                if 'result' in result and 'client' in result['result']:
                    client_data = result['result']['client']
                    logger.info(f"✅ Extracted client data: {client_data}")
                    return client_data
                
                # Fallback: return full result
                logger.warning(f"⚠️ Unexpected response structure, returning full result")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ MCP HTTP error: {e}")
            logger.error(f"❌ Response body: {e.response.text}")
            return {}
        except Exception as e:
            logger.error(f"❌ MCP call failed: {e}", exc_info=True)
            return {}
        
    def get_client_profile_from_db(self, client_id: str) -> Dict[str, Any]:
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
                    primary_exposure,  
                    rm,
                    computed_at
                FROM switch_probability_history
                WHERE client_id = %s
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
                WHERE client_id = %s
                ORDER BY analyzed_at DESC
                LIMIT 1
            ),
            latest_recs AS (
                SELECT 
                    recommendations,
                    generated_at
                FROM nba_recommendations
                WHERE client_id = %s
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
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Pass client_id three times for the three WHERE clauses
            cursor.execute(query, (client_id, client_id, client_id))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            row_dict = dict(zip(columns, row))
            
            # Get client metadata from MCP
            try:
                client_response = self._call_mcp_server(
                    server_url=self.client_server_url,  
                    tool_name='get_client_metadata',
                    arguments={'client_id': client_id}
                )
                rm = client_response.get('rm', 'Unknown')
                primary_exposure = client_response.get('primary_exposure', 'N/A')
            except Exception as e:
                logger.warning(f"Could not fetch client metadata from MCP: {e}")
                rm = "Unknown"
                primary_exposure = "N/A"
            
            # SIMPLIFIED - drivers is already an array from Gemini
            drivers = row_dict.get("drivers") or []
            if not isinstance(drivers, list):
                drivers = []  # Fallback only
            
            # Ensure other JSONB fields are proper arrays
            risk_flags = row_dict.get("risk_flags")
            if not isinstance(risk_flags, list):
                risk_flags = []
            
            headlines = row_dict.get("headlines")
            if not isinstance(headlines, list):
                headlines = []
            
            recommendations = row_dict.get("recommendations")
            if not isinstance(recommendations, list):
                recommendations = []
            
            return {
                "clientId": client_id,
                "rm": row_dict.get("rm") or "Unknown",
                "segment": row_dict["segment"],
                "switchProb": float(row_dict["switch_prob"]) if row_dict["switch_prob"] else 0.0,
                "confidence": float(row_dict["confidence"]) if row_dict["confidence"] else 0.0,
                "drivers": drivers,  
                "riskFlags": risk_flags,
                "primaryExposure": row_dict.get("primary_exposure") or "N/A",
                "analyzed_at": row_dict["computed_at"].isoformat() if row_dict["computed_at"] else None,
                "media": {
                    "pressure": row_dict["media_pressure"] or "UNKNOWN",
                    "sentiment": float(row_dict["sentiment_score"]) if row_dict["sentiment_score"] else 0.0,
                    "headlines": headlines
                },
                "recommendations": recommendations
            }
            
        finally:
            cursor.close()
            conn.close()
    
    
    def store_client_profile(self, client_id: str, profile: Dict[str, Any]):
        """
        Store complete analysis results in database.
        
        Everything comes from profile - no need to fetch metadata separately.
        """
        from datetime import datetime
        from psycopg2.extras import Json
        
        now = datetime.utcnow()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Store segmentation analysis
            cursor.execute("""
                INSERT INTO switch_probability_history 
                (client_id, segment, switch_prob, confidence, drivers, risk_flags, rm, primary_exposure, computed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                client_id,
                profile["segment"],
                profile["switch_prob"],
                profile["confidence"],
                Json(profile.get("drivers", [])),
                Json(profile.get("risk_flags", [])),
                profile.get('rm', 'Unknown'),
                profile.get('primary_exposure', 'N/A'),
                now
            ))
            
            # Store media analysis if present
            if "media" in profile:
                cursor.execute("""
                    INSERT INTO media_analysis
                    (client_id, pressure, sentiment_score, headlines, analyzed_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    client_id,
                    profile["media"].get("pressure"),
                    profile["media"].get("sentiment", 0),
                    Json(profile["media"].get("headlines", [])),
                    now
                ))
            
            # Store recommendations if present
            if "recommendations" in profile:
                cursor.execute("""
                    INSERT INTO nba_recommendations
                    (client_id, recommendations, generated_at)
                    VALUES (%s, %s, %s)
                """, (
                    client_id,
                    Json(profile.get("recommendations", [])),
                    now
                ))
            
            conn.commit()
            
            # Add analyzed_at to profile for response
            profile["analyzed_at"] = now.isoformat()
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()


    def create_alert(
        self,
        client_id: str,
        alert_type: str,
        old_switch_prob: Optional[float] = None,
        new_switch_prob: Optional[float] = None,
        reason: str = "",
        severity: str = "INFO"
    ) -> None:
        """Create an alert in insights table."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO insights 
                (client_id, type, severity, title, reason, old_switch_prob, new_switch_prob)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                client_id,
                'ALERT',  # type
                severity,
                alert_type[:200],  # title (truncated)
                reason[:1000],  # reason (truncated)
                old_switch_prob,
                new_switch_prob
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Created alert in insights for {client_id}: {alert_type}")
            
        except Exception as e:
            logger.error(f"❌ Error creating alert: {e}")
