from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.client import Client, ClientProfile, Timeline, Insight, Media
from app.services.data_service import DataService
from app.services.agent_service import AgentService

router = APIRouter()
data_service = DataService()
agent_service = AgentService()

@router.get("/", response_model=List[Client])
async def get_clients(
    search: Optional[str] = Query(None),
    segment: Optional[str] = Query(None),
    rm: Optional[str] = Query(None),
):
    """Get list of clients with optional filtering"""
    clients = data_service.get_clients(search=search, segment=segment, rm=rm)
    return clients

@router.get("/{client_id}/profile", response_model=ClientProfile)
async def get_client_profile(client_id: str):
    """Get client strategy profile"""
    # Call orchestrator agent
    profile = await agent_service.get_client_profile(client_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")
    return profile

@router.get("/{client_id}/timeline", response_model=List[Timeline])
async def get_client_timeline(client_id: str):
    """Get client timeline of regime changes"""
    timeline = data_service.get_timeline(client_id)
    return timeline

@router.get("/{client_id}/insights", response_model=List[Insight])
async def get_client_insights(client_id: str):
    """Get client insights feed"""
    insights = data_service.get_insights(client_id)
    return insights

@router.get("/{client_id}/media", response_model=Media)
async def get_client_media(client_id: str):
    """Get media intelligence for client"""
    media = await agent_service.get_media_analysis(client_id)
    return media
