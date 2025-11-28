"""
Clients Routes - API Façade

Handles all client-related endpoints by proxying to agents-service or Client MCP.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging
import httpx
import os

from services.agent_client import AgentClient
from services.data_service import DataService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_clients(
    search: Optional[str] = Query(None, description="Search by name or client_id"),
    segment: Optional[str] = Query(None, description="Filter by segment"),
    rm: Optional[str] = Query(None, description="Filter by relationship manager"),
    limit: int = Query(50, ge=1, le=100, description="Max results")
):
    """
    Get list of clients with optional filters.
    
    Calls Client MCP server directly for client metadata.
    
    Query Parameters:
    - search: Search term for name or client_id
    - segment: Filter by segment (Trend Follower, Mean Reverter, etc.)
    - rm: Filter by relationship manager
    - limit: Max number of results (1-100)
    
    Returns:
        List of client summaries
    """
    logger.info(f"📋 Listing clients: search={search}, segment={segment}, rm={rm}")
    
    try:
        # Get Client MCP server URL
        client_mcp_url = os.getenv('MCP_CLIENT_SERVER_URL', 'http://client-mcp:3005')
        
        # Call Client MCP server
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{client_mcp_url}/call_tool",
                json={
                    "tool_name": "list_clients",
                    "arguments": {
                        "search": search,
                        "segment": segment,
                        "rm": rm
                    }
                }
            )
            response.raise_for_status()
            
            result = response.json()
            clients = result.get('result', {}).get('clients', [])
            
            # Apply limit
            clients = clients[:limit]
        
        logger.info(f"✅ Retrieved {len(clients)} clients from Client MCP")
        
        return {
            "clients": clients,
            "count": len(clients),
            "filters": {
                "search": search,
                "segment": segment,
                "rm": rm
            }
        }
        
    except httpx.HTTPError as e:
        logger.error(f"❌ HTTP error calling Client MCP: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Client MCP server unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Error listing clients: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve clients: {str(e)}"
        )


@router.get("/{client_id}/profile")
async def get_client_profile(
    client_id: str,
    agent_client: AgentClient = Depends()
):
    """
    Get complete client profile (main endpoint).
    
    This calls the agents-service orchestrator which:
    1. Runs segmentation analysis
    2. Analyzes media sentiment
    3. Adjusts switch probability
    4. Generates recommendations
    
    Args:
        client_id: Client identifier
        
    Returns:
        Complete client profile with all analysis
    """
    logger.info(f"👤 Getting profile for: {client_id}")
    
    try:
        # Call agents-service (orchestrator endpoint)
        profile = await agent_client.get_client_profile(client_id)
        
        logger.info(
            f"✅ Profile retrieved: {client_id} "
            f"(segment={profile.get('segment')}, "
            f"switchProb={profile.get('switchProb')})"
        )
        
        return profile
        
    except HTTPException:
        # Re-raise HTTP exceptions from agent_client
        raise
    except Exception as e:
        logger.error(f"❌ Error getting profile for {client_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve profile: {str(e)}"
        )


@router.get("/{client_id}/timeline")
async def get_client_timeline(
    client_id: str,
    months: int = Query(6, ge=1, le=24, description="Months of history"),
    data_service: DataService = Depends()
):
    """
    Get historical regime timeline for client.
    
    Shows how the client's segment classification has changed over time.
    Uses database for historical agent state (client_regimes table).
    
    Args:
        client_id: Client identifier
        months: Number of months of history (1-24)
        
    Returns:
        List of regime periods with start/end dates
    """
    logger.info(f"📅 Getting timeline for: {client_id} ({months} months)")
    
    try:
        # Check if client_regimes table exists and has method
        # If not implemented, return empty timeline
        try:
            timeline = data_service.get_client_timeline(
                client_id=client_id,
                months=months
            )
        except AttributeError:
            logger.warning("get_client_timeline not implemented, returning empty")
            timeline = []
        
        logger.info(f"✅ Retrieved {len(timeline)} timeline events")
        
        return {
            "clientId": client_id,
            "timeline": timeline,
            "months": months
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting timeline for {client_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve timeline: {str(e)}"
        )


@router.get("/{client_id}/insights")
async def get_client_insights(
    client_id: str,
    limit: int = Query(20, ge=1, le=100, description="Max insights"),
    data_service: DataService = Depends()
):
    """
    Get recent insights/actions for client.
    
    Returns feed of signals, actions, and outcomes from database (alerts table).
    
    Args:
        client_id: Client identifier
        limit: Max number of insights (1-100)
        
    Returns:
        List of insight items (signals, actions, outcomes)
    """
    logger.info(f"💡 Getting insights for: {client_id}")
    
    try:
        # Get insights from database (alerts table)
        insights = data_service.get_client_insights(
            client_id=client_id,
            limit=limit
        )
        
        logger.info(f"✅ Retrieved {len(insights)} insights")
        
        return {
            "clientId": client_id,
            "insights": insights,
            "count": len(insights)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting insights for {client_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve insights: {str(e)}"
        )


@router.get("/{client_id}/media")
async def get_client_media(
    client_id: str,
    agent_client: AgentClient = Depends()
):
    """
    Get media analysis for client.
    
    Returns recent headlines and sentiment analysis for client's exposures.
    Calls agents-service which uses News MCP server.
    
    Args:
        client_id: Client identifier
        
    Returns:
        Media analysis with headlines and pressure assessment
    """
    logger.info(f"📰 Getting media for: {client_id}")
    
    try:
        # Get client metadata from Client MCP to find exposures
        client_mcp_url = os.getenv('MCP_CLIENT_SERVER_URL', 'http://client-mcp:3005')
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get client metadata
            response = await client.post(
                f"{client_mcp_url}/call_tool",
                json={
                    "tool_name": "get_client_metadata",
                    "arguments": {"client_id": client_id}
                }
            )
            response.raise_for_status()
            result = response.json()
            client_meta = result.get('result', {}).get('client', {})
        
        # Default exposures based on sector or use defaults
        sector = client_meta.get('sector', 'FX')
        if sector == 'FX':
            exposures = ['EURUSD', 'GBPUSD', 'USDJPY']
        elif sector == 'Commodities':
            exposures = ['GOLD', 'OIL', 'COPPER']
        elif sector == 'Equities':
            exposures = ['SPX', 'NASDAQ', 'FTSE']
        else:
            exposures = ['EURUSD', 'GBPUSD']
        
        # Call agents-service for media analysis
        media = await agent_client.get_media_analysis(
            client_id=client_id,
            exposures=exposures[:5]  # Top 5
        )
        
        logger.info(
            f"✅ Media analysis complete: {client_id} "
            f"(pressure={media.get('pressure')}, "
            f"headlines={media.get('headlineCount')})"
        )
        
        return {
            "clientId": client_id,
            "exposures": exposures[:5],
            **media
        }
        
    except httpx.HTTPError as e:
        logger.error(f"❌ HTTP error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"MCP server unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Error getting media for {client_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve media: {str(e)}"
        )
