from fastapi import APIRouter, HTTPException
from app.models.client import Action, ActionCreate
from app.services.data_service import DataService
from datetime import datetime
import uuid

router = APIRouter()
data_service = DataService()

@router.post("/", response_model=Action)
async def create_action(action: ActionCreate):
    """Log a new action"""
    action_id = str(uuid.uuid4())
    new_action = Action(
        id=action_id,
        clientId=action.clientId,
        actionType=action.actionType,
        product=action.product,
        description=action.description,
        timestamp=datetime.utcnow(),
        status="pending"
    )
    
    # Save to data store
    data_service.save_action(new_action)
    
    return new_action

@router.get("/{action_id}", response_model=Action)
async def get_action(action_id: str):
    """Get action by ID"""
    action = data_service.get_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action
