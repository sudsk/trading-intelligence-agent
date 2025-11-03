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
    data_service: DataService = Depends()
):
    """
    Manually trigger a demo alert (for presentations).
    
    This is the endpoint called by the "🚨 Force Event" button in the UI.
    
    Creates a synthetic alert that:
    1. Shows elevated switch probability
    2. Flows through SSE stream
    3. Displays AlertBanner in UI
    4. Allows user to "Take Action"
    
    Args:
        request: Optional client_id and event_type
        
    Returns:
        Confirmation with alert details
    """
    logger.info(f"🚨 Force Event triggered: type={request.event_type}")
    
    try:
        # Select client
        if request.client_id:
            client_id = request.client_id
            logger.info(f"   Using specified client: {client_id}")
        else:
            # Pick a random client from database
            clients_df = data_service.get_clients_list(limit=10)
            if not clients_df.empty:
                client_id = random.choice(clients_df['client_id'].tolist())
                logger.info(f"   Selected random client: {client_id}")
            else:
                client_id = "ACME_FX_023"  # Default
                logger.info(f"   Using default client: {client_id}")
        
        # Create alert based on type
        if request.event_type == "switch_probability_alert":
            alert = _create_switch_prob_alert(client_id)
        elif request.event_type == "media_pressure_alert":
            alert = _create_media_alert(client_id)
        elif request.event_type == "risk_flag_alert":
            alert = _create_risk_alert(client_id)
        else:
            alert = _create_switch_prob_alert(client_id)  # Default
        
        # Add to alert queue (will be sent via SSE)
        alert_queue.add(alert)
        
        logger.info(f"✅ Alert triggered: {alert['type']} for {client_id}")
        
        return ForceEventResponse(
            status="triggered",
            alert=alert,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Error triggering alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger alert: {str(e)}"
        )


@router.post("/reset-demo")
async def reset_demo(
    alert_queue: AlertQueue = Depends()
):
    """
    Reset demo state (clear alert queue).
    
    Useful for restarting demos cleanly.
    """
    logger.info("🔄 Resetting demo state")
    
    try:
        alert_queue.clear()
        
        return {
            "status": "reset",
            "message": "Demo state cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error resetting demo: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset demo: {str(e)}"
        )


# ============================================================================
# Alert Generators
# ============================================================================

def _create_switch_prob_alert(client_id: str) -> dict:
    """
    Create switch probability increase alert.
    
    Simulates scenario where client's strategy instability has increased.
    """
    old_prob = round(random.uniform(0.35, 0.55), 2)
    new_prob = old_prob + round(random.uniform(0.08, 0.15), 2)
    
    reasons = [
        "media-driven",
        "position-volatility",
        "pattern-instability",
        "risk-exposure-change"
    ]
    
    return {
        "type": "switch_probability_alert",
        "severity": "HIGH" if new_prob > 0.65 else "MEDIUM",
        "clientId": client_id,
        "oldSwitchProb": old_prob,
        "newSwitchProb": min(0.85, new_prob),
        "change": round(new_prob - old_prob, 2),
        "reason": random.choice(reasons),
        "message": f"Switch probability increased from {old_prob:.0%} to {min(0.85, new_prob):.0%}",
        "timestamp": datetime.utcnow().isoformat(),
        "actionable": True
    }


def _create_media_alert(client_id: str) -> dict:
    """
    Create media pressure spike alert.
    
    Simulates scenario where sudden negative news affects client's exposures.
    """
    instruments = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
    
    return {
        "type": "media_pressure_alert",
        "severity": "MEDIUM",
        "clientId": client_id,
        "instrument": random.choice(instruments),
        "oldPressure": "LOW",
        "newPressure": "HIGH",
        "sentiment": round(random.uniform(-0.7, -0.4), 2),
        "headlineCount": random.randint(15, 30),
        "message": f"Media pressure spike detected on {random.choice(instruments)}",
        "timestamp": datetime.utcnow().isoformat(),
        "actionable": True
    }


def _create_risk_alert(client_id: str) -> dict:
    """
    Create risk flag alert.
    
    Simulates scenario where new risk concern has been identified.
    """
    risk_types = [
        "concentration-risk",
        "leverage-increase",
        "volatility-spike",
        "correlation-breakdown"
    ]
    
    return {
        "type": "risk_flag_alert",
        "severity": "HIGH",
        "clientId": client_id,
        "riskType": random.choice(risk_types),
        "message": f"New risk flag: {random.choice(risk_types).replace('-', ' ').title()}",
        "details": "Automated risk monitoring detected new concern",
        "timestamp": datetime.utcnow().isoformat(),
        "actionable": True
    }