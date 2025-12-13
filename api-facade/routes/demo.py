"""
Demo Routes - API Façade

Demo/testing endpoints including Force Event trigger.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging
import random

from services.alert_queue import AlertQueue
from services.data_service import DataService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class ForceEventRequest(BaseModel):
    """Request to trigger demo event"""
    client_id: Optional[str] = None  # If None, pick random client
    event_type: Optional[str] = "switch_probability_alert"  # Type of alert


class ForceEventResponse(BaseModel):
    """Response after triggering event"""
    status: str
    alert: dict
    timestamp: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/trigger-alert", response_model=ForceEventResponse)
async def trigger_demo_alert(
    request: ForceEventRequest = ForceEventRequest(),
    alert_queue: AlertQueue = Depends(),
    agent_client: AgentClient = Depends(),
    data_service: DataService = Depends()
):
    """
    Force Event - Triggers real analysis and generates alert.
    
    In production, this would happen automatically via:
    - Scheduled jobs (every 30 mins)
    - Event-driven triggers (new trades, media)
    
    For demo, we manually trigger it with 🚨 Force Event" button.
    """    
    client_id = request.client_id or "ACME_FX_023"  # Default for demo
    
    logger.info(f"🚨 Force Event triggered for: {client_id}")
    
    try:
        # STEP 1: Get old value from database
        old_profile = data_service.get_client_profile_from_db(client_id)
        old_switch_prob = old_profile.get('switchProb', 0.30) if old_profile else 0.30
        
        # STEP 2: Run REAL analysis (this takes ~20s)
        logger.info(f"   Running fresh analysis...")
        profile = await agent_client.get_client_profile(client_id)
        new_switch_prob = profile.get('switch_prob')

        # STEP 3: Store new value in database
        data_service.store_client_profile(client_id, profile)
        logger.info(f"   Analysis complete: {old_switch_prob:.2f} → {new_switch_prob:.2f}")

        # STEP 4: Generate alert if significant change
        change = new_switch_prob - old_switch_prob
        
        if abs(change) >= 0.05:  # Any change ≥5% triggers alert
            # Determine reason from analysis
            media_pressure = profile.get('media', {}).get('pressure', 'LOW')
            reason = 'media-driven' if media_pressure == 'HIGH' else 'pattern-shift'
            
            severity = 'HIGH' if new_switch_prob > 0.65 else 'MEDIUM'
            
            alert = {
                'type': 'switch_probability_alert',
                'severity': severity,
                'clientId': client_id,
                'oldSwitchProb': old_switch_prob,
                'newSwitchProb': new_switch_prob,
                'change': round(change, 2),
                'reason': reason,
                'message': f"Switch probability {'increased' if change > 0 else 'decreased'} from {old_switch_prob:.0%} to {new_switch_prob:.0%}",
                'timestamp': datetime.utcnow().isoformat(),
                'actionable': True
            }
            
            # STEP 5: Send alert
            alert_queue.add(alert)
            
            logger.info(f"   🚨 Alert generated: {severity} - {reason}")
            
            return ForceEventResponse(
                status="triggered",
                alert=alert,
                timestamp=datetime.utcnow().isoformat()
            )
        else:
            # No alert needed, but analysis still ran
            logger.info(f"   ℹ️ No alert - change too small ({change:.2f})")
            
            return JSONResponse(content={
                "status": "analyzed",
                "message": f"Analysis completed but no alert triggered (change: {change:.2f})",
                "old_switch_prob": old_switch_prob,
                "new_switch_prob": new_switch_prob,
                "timestamp": datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"❌ Error in Force Event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
