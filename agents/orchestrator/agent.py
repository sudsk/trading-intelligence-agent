"""
Orchestrator Agent - Routes requests to specialist agents
"""
from vertexai.preview import reasoning_engines
from typing import Dict, Any

class OrchestratorAgent:
    def __init__(self):
        self.segmentation_agent = None  # Initialize sub-agents
        self.media_agent = None
        self.nba_agent = None
    
    def get_client_profile(self, client_id: str) -> Dict[str, Any]:
        """
        Main entry point - orchestrates specialist agents
        """
        # Step 1: Get segmentation analysis
        segmentation = self.segmentation_agent.analyze(client_id)
        
        # Step 2: Get media analysis (if relevant exposures)
        media = self.media_agent.analyze(
            client_id=client_id,
            exposures=segmentation.get('exposures', [])
        )
        
        # Step 3: Adjust switch prob based on media
        adjusted_switch_prob = self._adjust_switch_prob(
            base_prob=segmentation['switchProb'],
            media_pressure=media['pressure']
        )
        
        # Step 4: Get next best actions
        recommendations = self.nba_agent.recommend(
            client_id=client_id,
            segment=segmentation['segment'],
            switch_prob=adjusted_switch_prob,
            risk_flags=segmentation['riskFlags']
        )
        
        return {
            **segmentation,
            'switchProb': adjusted_switch_prob,
            'media': media,
            'recommendations': recommendations
        }
    
    def _adjust_switch_prob(self, base_prob: float, media_pressure: str) -> float:
        """Adjust switch probability based on media pressure"""
        adjustments = {'HIGH': 0.1, 'MEDIUM': 0.05, 'LOW': 0.0}
        return min(0.99, base_prob + adjustments.get(media_pressure, 0.0))
