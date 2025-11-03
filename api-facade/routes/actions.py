"""
Actions Routes - API Façade

Handles logging of relationship manager actions.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

from services.data_service import DataService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class ActionRequest(BaseModel):
    """Request to log an action"""
    client_id: str
    action_type: str  # e.g., "PROACTIVE_OUTREACH", "PROPOSE_HEDGE"
    title: str
    description: Optional[str] = None
    products: Optional[List[str]] = None
    rm: Optional[str] = None


class ActionResponse(BaseModel):
    """Response after logging action"""
    action_id: str
    client_id: str
    timestamp: str
    status: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/", response_model=ActionResponse)
async def log_action(
    request: ActionRequest,
    data_service: DataService = Depends()
):
    """
    Log a relationship manager action.
    
    This endpoint is called when:
    - RM clicks "Propose Product" in UI
    - RM takes any recommended action
    - System automatically logs certain events
    
    The action is:
    1. Inserted into the database
    2. Added to the client's insights feed
    3. Available for future NBA learning (Memory Bank)
    
    Args:
        request: Action details
        
    Returns:
        Confirmation with action_id
    """
    logger.info(
        f"📝 Logging action: {request.action_type} for {request.client_id} "
        f"by {request.rm}"
    )
    
    try:
        # Generate action_id
        action_id = f"ACT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{request.client_id}"
        
        # Log to database
        data_service.log_action(
            action_id=action_id,
            client_id=request.client_id,
            action_type=request.action_type,
            title=request.title,
            description=request.description,
            products=request.products,
            rm=request.rm or 'System'
        )
        
        # Also add to insights feed
        data_service.add_insight(
            client_id=request.client_id,
            type='ACTION',
            title=request.title,
            description=request.description or f"Action taken: {request.action_type}",
            severity='INFO'
        )
        
        logger.info(f"✅ Action logged: {action_id}")
        
        return ActionResponse(
            action_id=action_id,
            client_id=request.client_id,
            timestamp=datetime.utcnow().isoformat(),
            status="logged"
        )
        
    except Exception as e:
        logger.error(f"❌ Error logging action: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to log action: {str(e)}"
        )


@router.get("/{client_id}")
async def get_client_actions(
    client_id: str,
    limit: int = 20,
    data_service: DataService = Depends()
):
    """
    Get action history for a client.
    
    Returns all logged actions for analysis and Memory Bank.
    
    Args:
        client_id: Client identifier
        limit: Max number of actions to return
        
    Returns:
        List of actions with outcomes (if available)
    """
    logger.info(f"📋 Getting actions for: {client_id}")
    
    try:
        actions = data_service.get_client_actions(
            client_id=client_id,
            limit=limit
        )
        
        logger.info(f"✅ Retrieved {len(actions)} actions")
        
        return {
            "clientId": client_id,
            "actions": actions,
            "count": len(actions)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting actions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve actions: {str(e)}"
        )