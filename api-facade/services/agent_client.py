"""
Agent Client - HTTP client for calling agents-service

Abstracts communication with the agents-service backend.
"""
import httpx
import os
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class AgentClient:
    """
    HTTP client for agents-service.
    
    This abstracts the agents-service API, making it easy to swap
    from Cloud Run to Agent Engine in the future.
    """
    
    def __init__(self):
        """Initialize agent client"""
        self.base_url = os.getenv(
            'AGENTS_SERVICE_URL',
            'http://localhost:8001'
        )
        self.timeout = 90.0  # Gemini calls can take time
        
        logger.info(f"🔗 Agent Client initialized: {self.base_url}")
    
    async def get_client_profile(self, client_id: str) -> Dict[str, Any]:
        """
        Get complete client profile (main endpoint).
        
        Args:
            client_id: Client identifier
            
        Returns:
            Complete profile dict
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/analyze",
                    json={"client_id": client_id},
                    timeout=90.0  # ← Explicit 90 second timeout
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error(f"Timeout calling agents-service for {client_id}")
            raise HTTPException(
                status_code=504,
                detail="Agent service timeout"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from agents-service: {e.response.status_code}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Agent service error: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Error calling agents-service: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to communicate with agents service: {str(e)}"
            )
    
    async def get_segmentation(self, client_id: str) -> Dict[str, Any]:
        """
        Get segmentation only.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Segmentation result
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/segment",
                    json={"client_id": client_id}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting segmentation: {e}")
            raise
    
    async def get_media_analysis(
        self,
        client_id: str,
        exposures: list
    ) -> Dict[str, Any]:
        """
        Get media analysis only.
        
        Args:
            client_id: Client identifier
            exposures: List of instruments
            
        Returns:
            Media analysis result
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/media",
                    json={
                        "client_id": client_id,
                        "exposures": exposures
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting media analysis: {e}")
            raise
    
    async def get_recommendations(
        self,
        client_id: str,
        segment: str,
        switch_prob: float,
        risk_flags: list,
        media_pressure: str,
        primary_exposure: str
    ) -> Dict[str, Any]:
        """
        Get NBA recommendations only.
        
        Args:
            client_id: Client identifier
            segment: Client segment
            switch_prob: Switch probability
            risk_flags: Risk flags
            media_pressure: Media pressure level
            primary_exposure: Primary instrument
            
        Returns:
            Recommendations result
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/recommend",
                    json={
                        "client_id": client_id,
                        "segment": segment,
                        "switch_prob": switch_prob,
                        "risk_flags": risk_flags,
                        "media_pressure": media_pressure,
                        "primary_exposure": primary_exposure
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            raise
    
    async def check_health(self, detailed: bool = False) -> Dict[str, Any]:
        """
        Check agents service health.
        
        Args:
            detailed: Include detailed agent status
            
        Returns:
            Health status dict
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.base_url}/health",
                    json={"detailed": detailed}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error checking agent health: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# For future Agent Engine migration, this class would change to:
"""
class AgentEngineClient:
    def __init__(self):
        self.client = AgentEngineSDK(...)
    
    async def get_client_profile(self, client_id: str):
        return await self.client.invoke(
            agent="orchestrator-agent",
            input={"client_id": client_id}
        )
"""
