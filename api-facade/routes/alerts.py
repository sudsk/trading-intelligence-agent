"""
Alerts Routes - API Façade

Handles Server-Sent Events (SSE) streaming for real-time alerts.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
from datetime import datetime

from services.alert_queue import AlertQueue

logger = logging.getLogger(__name__)

router = APIRouter()


def get_alert_queue_from_request(request: Request) -> AlertQueue:
    """Get alert queue from app state via request"""
    return request.app.state.alert_queue


@router.get("/stream")
async def stream_alerts(
    request: Request
):
    """
    SSE endpoint for streaming alerts to frontend.
    
    The frontend opens a persistent connection to this endpoint
    and receives alerts as they occur:
    - Switch probability changes
    - Media pressure spikes
    - Risk flag triggers
    - System notifications
    
    Returns:
        StreamingResponse with text/event-stream
    """
    logger.info("📡 Client connected to alert stream")
    
    # Get alert queue from app state
    alert_queue = request.app.state.alert_queue
    
    async def event_generator():
        """Generate SSE events with proper keepalive timing."""
        try:
            # Send initial connection message
            initial_message = {
                "type": "connection",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to alert stream"
            }
            yield f"data: {json.dumps(initial_message)}\n\n"
            
            last_keepalive = datetime.utcnow()
            poll_count = 0
            
            # Keep connection alive and send alerts
            while True:
                poll_count += 1
                
                # Check for pending alerts
                alerts = alert_queue.get_pending()
                
                # DEBUG: Log when we find alerts
                if len(alerts) > 0:
                    logger.info(f"🎯 FOUND {len(alerts)} PENDING ALERTS IN QUEUE!")
                
                for alert in alerts:
                    logger.info(f"📤 Sending alert via SSE: {alert.get('type')} for {alert.get('clientId')}")
                    yield f"data: {json.dumps(alert)}\n\n"
                
                # Send keepalive every 30 seconds regardless of alerts
                now = datetime.utcnow()
                if (now - last_keepalive).seconds >= 30:
                    keepalive = {
                        "type": "keepalive",
                        "timestamp": now.isoformat()
                    }
                    yield f"data: {json.dumps(keepalive)}\n\n"
                    last_keepalive = now
                
                # Poll every 1 second for faster alerts
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("📡 Client disconnected from alert stream")
            raise
        except Exception as e:
            logger.error(f"❌ Error in alert stream: {e}", exc_info=True)
            error_message = {
                "type": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "message": str(e)
            }
            yield f"data: {json.dumps(error_message)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )


@router.get("/history")
async def get_alert_history(
    request: Request,
    limit: int = 50
):
    """
    Get recent alert history.
    
    Returns alerts from the last 24 hours (stored in memory).
    
    Args:
        limit: Max number of alerts to return
        
    Returns:
        List of recent alerts
    """
    logger.info(f"📜 Getting alert history (limit={limit})")
    
    alert_queue = request.app.state.alert_queue
    
    try:
        history = alert_queue.get_history(limit=limit)
        
        return {
            "alerts": history,
            "count": len(history),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting alert history: {e}")
        return {
            "alerts": [],
            "count": 0,
            "error": str(e)
        }
