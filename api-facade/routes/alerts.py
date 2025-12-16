"""
Alerts Routes - API Façade - ULTRA DEBUG VERSION

Handles Server-Sent Events (SSE) streaming for real-time alerts.
"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
from datetime import datetime

from services.alert_queue import AlertQueue

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stream")
async def stream_alerts(
    request: Request
):
    """
    SSE endpoint for streaming alerts to frontend.
    """
    logger.info("📡 ===== CLIENT CONNECTED TO ALERT STREAM =====")
    
    # Get alert queue from app state
    alert_queue = request.app.state.alert_queue
    logger.info(f"📡 Alert queue instance: {id(alert_queue)}")
    
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
            logger.info("📡 Sent initial connection message")
            
            last_keepalive = datetime.utcnow()
            poll_count = 0
            
            # Keep connection alive and send alerts
            while True:
                poll_count += 1
                
                # LOG EVERY SINGLE POLL
                # logger.info(f"🔄 POLL #{poll_count} - Checking queue at {datetime.utcnow().isoformat()}")
                
                # Check for pending alerts
                alerts = alert_queue.get_pending()
                
                # LOG RESULT OF EVERY POLL
                # logger.info(f"🔍 POLL #{poll_count} RESULT: Found {len(alerts)} alerts")
                
                if len(alerts) > 0:
                    logger.info(f"🎯 ===== FOUND {len(alerts)} PENDING ALERTS IN QUEUE! =====")
                    for i, alert in enumerate(alerts):
                        logger.info(f"🎯 Alert {i+1}: {json.dumps(alert, indent=2)}")
                
                for alert in alerts:
                    logger.info(f"📤 Sending alert via SSE: {alert.get('type')} for {alert.get('clientId')}")
                    yield f"data: {json.dumps(alert)}\n\n"
                    logger.info(f"✅ Alert sent successfully")
                
                # Send keepalive every 30 seconds regardless of alerts
                now = datetime.utcnow()
                seconds_since_keepalive = (now - last_keepalive).seconds
                
                if seconds_since_keepalive >= 30:
                    keepalive = {
                        "type": "keepalive",
                        "timestamp": now.isoformat()
                    }
                    logger.info(f"💓 Sending keepalive (poll #{poll_count}, {seconds_since_keepalive}s since last)")
                    yield f"data: {json.dumps(keepalive)}\n\n"
                    last_keepalive = now
                
                # Poll every 1 second for faster alerts
                # logger.info(f"😴 POLL #{poll_count} COMPLETE - Sleeping 1 second...")
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("📡 ===== CLIENT DISCONNECTED FROM ALERT STREAM =====")
            raise
        except Exception as e:
            logger.error(f"❌ ===== ERROR IN ALERT STREAM: {e} =====", exc_info=True)
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
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/history")
async def get_alert_history(
    request: Request,
    limit: int = 50
):
    """Get recent alert history."""
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
