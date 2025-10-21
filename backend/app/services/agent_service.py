from google.cloud import aiplatform
from app.config import settings
import json

class AgentService:
    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.region = settings.GCP_REGION
        aiplatform.init(project=self.project_id, location=self.region)
    
    async def get_client_profile(self, client_id: str):
        """Call orchestrator agent to get client profile"""
        if settings.DEMO_MODE:
            # Return mock data for demo
            return self._get_mock_profile(client_id)
        
        # TODO: Call Vertex AI Agent Engine
        # endpoint = aiplatform.Endpoint(settings.VERTEX_AI_AGENT_ENDPOINT)
        # response = endpoint.predict(instances=[{"client_id": client_id}])
        # return response.predictions[0]
        
        return self._get_mock_profile(client_id)
    
    async def get_media_analysis(self, client_id: str):
        """Call media fusion agent"""
        if settings.DEMO_MODE:
            return self._get_mock_media(client_id)
        
        # TODO: Call media fusion agent
        return self._get_mock_media(client_id)
    
    def _get_mock_profile(self, client_id: str):
        # Mock implementation
        return {
            "clientId": client_id,
            "segment": "Trend Follower",
            "confidence": 0.82,
            "switchProb": 0.53,
            "drivers": [
                "High 20-day momentum-beta",
                "Shorter hold times",
                "Positive lead-lag alpha"
            ],
            "riskFlags": ["EUR concentration", "Leverage drift"],
            "primaryExposure": "EUR/USD",
            "rm": "Sarah Chen"
        }
    
    def _get_mock_media(self, client_id: str):
        return {
            "pressure": "HIGH",
            "headlines": [
                {
                    "title": "ECB Signals Unexpected Rate Hold",
                    "sentiment": "negative",
                    "timestamp": "2025-10-20T08:00:00Z"
                }
            ]
        }
