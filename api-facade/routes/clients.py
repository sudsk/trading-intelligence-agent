"""
Clients Routes - API Façade

Handles all client-related endpoints by proxying to agents-service or database.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging

from services.agent_client import AgentClient
from services.data_service import DataService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_clients(
    search: Optional[str] = Query(None, description="Search by name or client_id"),
    segment: Optional[str] = Query(None, description="Filter by segment"),
    rm: Optional[str] = Query(None, description="Filter by relationship manager"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    data_service: DataService = Depends()
):
    """
    Get list of clients with optional filters.
    
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
        clients_df = data_service.get_clients_list(
            search=search,
            segment=segment,
            rm=rm,
            limit=limit
        )
        
        # Convert to list of dicts
        clients = clients_df.to_dict('records')
        
        logger.info(f"✅ Retrieved {len(clients)} clients")
        
        return {
            "clients": clients,
            "count": len(clients),
            "filters": {
                "search": search,
                "segment": segment,
                "rm": rm
            }
        }
        
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
    
    Args:
        client_id: Client identifier
        months: Number of months of history (1-24)
        
    Returns:
        List of regime periods with start/end dates
    """
    logger.info(f"📅 Getting timeline for: {client_id} ({months} months)")
    
    try:
        timeline = data_service.get_client_timeline(
            client_id=client_id,
            months=months
        )
        
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
    
    Returns feed of signals, actions, and outcomes.
    
    Args:
        client_id: Client identifier
        limit: Max number of insights (1-100)
        
    Returns:
        List of insight items (signals, actions, outcomes)
    """
    logger.info(f"💡 Getting insights for: {client_id}")
    
    try:
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
    agent_client: AgentClient = Depends(),
    data_service: DataService = Depends()
):
    """
    Get media analysis for client.
    
    Returns recent headlines and sentiment analysis for client's exposures.
    
    Args:
        client_id: Client identifier
        
    Returns:
        Media analysis with headlines and pressure assessment
    """
    logger.info(f"📰 Getting media for: {client_id}")
    
    try:
        # First get client's exposures
        client_meta = data_service.get_client_metadata(client_id)
        
        # Get exposures from positions
        positions_df = data_service.get_positions(client_id)
        exposures = positions_df['instrument'].tolist() if not positions_df.empty else ['EURUSD']
        
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
        
    except Exception as e:
        logger.error(f"❌ Error getting media for {client_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve media: {str(e)}"
        )