"""
Orchestrator Agent

Coordinates all specialist agents to build complete client profiles.
This is NOT a Gemini agent - it's pure orchestration logic.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from agents.segmentation_agent.agent import SegmentationAgent
from agents.media_fusion_agent.agent import MediaFusionAgent
from agents.nba_agent.agent import NBAAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Orchestrator that coordinates specialist agents.
    
    Flow:
    1. Segmentation Agent analyzes trades → segment, switch prob, drivers
    2. Media Agent analyzes headlines → sentiment, pressure
    3. Adjust switch prob based on media (if high pressure)
    4. NBA Agent generates recommendations
    5. Assemble complete profile
    """
    
    def __init__(self, data_service):
        """
        Initialize orchestrator with all specialist agents.
        
        Args:
            data_service: DataService instance for database access
        """
        self.data_service = data_service
        
        # Initialize specialist agents
        logger.info("🎯 Initializing Orchestrator Agent...")
        
        self.segmentation_agent = SegmentationAgent(data_service)
        logger.info("   ✓ Segmentation Agent ready")
        
        self.media_agent = MediaFusionAgent(data_service)
        logger.info("   ✓ Media Fusion Agent ready")
        
        self.nba_agent = NBAAgent()
        logger.info("   ✓ NBA Agent ready")
        
        logger.info("✅ Orchestrator Agent initialized successfully")
    
    def get_client_profile(self, client_id: str) -> Dict[str, Any]:
        """
        Build complete client profile by coordinating all agents.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Complete profile dict
        """
        logger.info(f"🎯 Orchestrator building profile for: {client_id}")
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Segmentation analysis
            logger.info("   1️⃣ Calling Segmentation Agent...")
            segmentation = self.segmentation_agent.analyze(client_id)
            
            # Step 2: Extract exposures for media analysis
            exposures = self._extract_exposures(segmentation)
            logger.info(f"   📊 Client exposures: {exposures}")
            
            # Step 3: Media analysis
            logger.info("   2️⃣ Calling Media Fusion Agent...")
            media = self.media_agent.analyze(
                client_id=client_id,
                exposures=exposures
            )
            
            # Step 4: Adjust switch probability based on media
            base_switch_prob = segmentation.get('switch_prob', 0.3)
            adjusted_switch_prob = self._adjust_switch_prob(
                base_switch_prob=base_switch_prob,
                media_pressure=media.get('pressure', 'LOW'),
                sentiment=media.get('sentiment_avg', 0.0)
            )
            
            if adjusted_switch_prob != base_switch_prob:
                logger.info(
                    f"   📈 Switch prob adjusted: {base_switch_prob:.2f} → {adjusted_switch_prob:.2f} "
                    f"(media: {media.get('pressure')})"
                )
            
            # Step 5: Generate recommendations
            logger.info("   3️⃣ Calling NBA Agent...")
            recommendations = self.nba_agent.recommend(
                client_id=client_id,
                segment=segmentation.get('segment', 'Unclassified'),
                switch_prob=adjusted_switch_prob,
                risk_flags=segmentation.get('risk_flags', []),
                media_pressure=media.get('pressure', 'LOW'),
                primary_exposure=segmentation.get('primary_exposure', 'N/A'),
                confidence=segmentation.get('confidence', 0.5),
                sentiment=media.get('sentiment_avg', 0.0),
                drivers=segmentation.get('drivers', [])
            )
            
            # Step 6: Assemble complete profile
            profile = self._assemble_profile(
                client_id=client_id,
                segmentation=segmentation,
                media=media,
                recommendations=recommendations,
                base_switch_prob=base_switch_prob,
                adjusted_switch_prob=adjusted_switch_prob
            )
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"✅ Profile complete for {client_id} in {elapsed:.2f}s")
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Error building profile for {client_id}: {e}", exc_info=True)
            raise
    
    def _extract_exposures(self, segmentation: Dict) -> List[str]:
        """
        Extract list of instruments from segmentation data.
        
        Args:
            segmentation: Segmentation result dict
            
        Returns:
            List of instrument symbols
        """
        exposures = []
        
        # Primary exposure
        primary = segmentation.get('primary_exposure')
        if primary and primary != 'N/A':
            exposures.append(primary)
        
        # Extract from features if available
        features = segmentation.get('features', {})
        if 'instruments' in features:
            exposures.extend(features['instruments'])
        
        # Deduplicate and limit
        exposures = list(dict.fromkeys(exposures))[:5]  # Top 5
        
        return exposures if exposures else ['EURUSD']  # Default
    
    def _adjust_switch_prob(
        self,
        base_switch_prob: float,
        media_pressure: str,
        sentiment: float
    ) -> float:
        """
        Adjust switch probability based on media conditions.
        
        Logic:
        - HIGH pressure + negative sentiment → increase switch prob
        - HIGH pressure + positive sentiment → may stabilize
        - MEDIUM pressure → minor adjustment
        - LOW pressure → no change
        
        Args:
            base_switch_prob: Base probability from segmentation
            media_pressure: HIGH/MEDIUM/LOW
            sentiment: Average sentiment (-1 to +1)
            
        Returns:
            Adjusted switch probability (clamped to 0.15-0.85)
        """
        adjusted = base_switch_prob
        
        if media_pressure == 'HIGH':
            if sentiment < -0.3:
                # Negative news increases uncertainty
                adjustment = 0.10
                logger.info(f"   ⚠️ HIGH negative media pressure (+{adjustment:.2f})")
            elif sentiment > 0.3:
                # Positive news may stabilize
                adjustment = -0.05
                logger.info(f"   ℹ️ HIGH positive media pressure ({adjustment:.2f})")
            else:
                # Neutral but high volume
                adjustment = 0.05
                logger.info(f"   ℹ️ HIGH neutral media pressure (+{adjustment:.2f})")
            
            adjusted = base_switch_prob + adjustment
            
        elif media_pressure == 'MEDIUM':
            if abs(sentiment) > 0.3:
                # Some directional pressure
                adjustment = 0.05 if sentiment < 0 else -0.02
                adjusted = base_switch_prob + adjustment
        
        # Clamp to valid range
        adjusted = max(0.15, min(0.85, adjusted))
        
        return round(adjusted, 2)
    
    def _get_client_metadata_and_exposure(self, client_id: str) -> tuple:
        """
        Get client metadata (RM) and derive primary exposure.
        
        Returns:
            (rm, primary_exposure)
        """
        try:
            # Get RM from client MCP
            client_response = self.data_service.get_client_metadata(client_id)
            
            # Handle nested response structure if needed
            if isinstance(client_response, dict):
                if 'result' in client_response and 'client' in client_response['result']:
                    client_data = client_response['result']['client']
                elif 'client' in client_response:
                    client_data = client_response['client']
                else:
                    client_data = client_response
            else:
                client_data = {}
            
            rm = client_data.get('rm', 'Unknown')
            
            # Get primary exposure from positions
            try:
                positions = self.data_service.get_positions(client_id)
                primary_exposure = self._derive_primary_exposure(positions)
            except Exception as e:
                logger.warning(f"⚠️ Could not get positions for {client_id}: {e}")
                primary_exposure = 'N/A'
            
            logger.info(f"✅ Client metadata: rm={rm}, primary_exposure={primary_exposure}")
            return rm, primary_exposure
            
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch client metadata: {e}")
            return 'Unknown', 'N/A'
    
    def _derive_primary_exposure(self, positions: List[Dict]) -> str:
        """
        Derive primary exposure from positions data.
        
        Uses gross position (total capital at risk) to determine
        which instrument has the highest exposure.
        """
        try:
            if not positions:
                return 'N/A'
            
            # Find position with highest gross position (or absolute net if gross not available)
            max_position = max(
                positions,
                key=lambda p: p.get('gross_position', abs(p.get('net_position', 0)))
            )
            
            return max_position.get('instrument', 'N/A')
            
        except Exception as e:
            logger.warning(f"⚠️ Could not derive primary exposure: {e}")
            return 'N/A'

    def _assemble_profile(
        self,
        client_id: str,
        segmentation: Dict,
        media: Dict,
        recommendations: List[Dict],
        base_switch_prob: float,
        adjusted_switch_prob: float
    ) -> Dict[str, Any]:
        """Assemble complete client profile from agent outputs."""
        
        # Get client metadata for name/sector only
        client_meta = self.data_service.get_client_metadata(client_id)
        
        # ✅ Enrich with RM and primary exposure
        rm, primary_exposure = self._get_client_metadata_and_exposure(client_id)
       
        # Format media
        media_formatted = {
            'pressure': media.get('pressure', 'LOW'),
            'sentiment_avg': media.get('sentiment_avg', 0.0),
            'sentiment_velocity': media.get('sentiment_velocity', 0.0),
            'headlines': media.get('headlines', []),
            'headline_count': media.get('headline_count', 0),
            'reasoning': media.get('reasoning', '')
        }
        
        profile = {
            # Client identification
            'client_id': client_id,
            'name': client_meta.get('name', client_id) if client_meta else client_id,
            'rm': rm,
            'sector': client_meta.get('sector', 'Unknown') if client_meta else 'Unknown',
            
            # ✅ Use FRESH analysis from agents
            'segment': segmentation.get('segment', 'Unclassified'),
            'confidence': segmentation.get('confidence', 0.0),
            'switch_prob': adjusted_switch_prob,
            'base_switch_prob': base_switch_prob,
            'drivers': segmentation.get('drivers', []),
            'risk_flags': segmentation.get('risk_flags', []),
            'primary_exposure': primary_exposure,
            
            # Media analysis
            'media': media_formatted,
            
            # Recommendations
            'recommendations': recommendations,
            
            # Metadata
            'features': segmentation.get('features'),
        }
        
        return profile  
    
    def get_agent_health(self) -> Dict[str, Any]:
        """
        Check health status of all agents.
        
        Returns:
            Health status dict
        """
        health = {
            'orchestrator': 'healthy',
            'segmentation': 'healthy' if self.segmentation_agent.enabled else 'degraded',
            'media_fusion': 'healthy' if self.media_agent.sentiment_enabled else 'degraded',
            'media_fusion_gemini': 'enabled' if self.media_agent.sentiment_enabled else 'disabled',
            'nba': 'healthy' if self.nba_agent.enabled else 'degraded',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return health
