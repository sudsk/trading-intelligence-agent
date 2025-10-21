from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.alert_service import AlertService
import asyncio
import json

router = APIRouter()
alert_service = AlertService()

@router.get("/stream")
async def stream_alerts():
    """SSE endpoint for real-time alerts"""
    async def event_generator():
        try:
            while True:
                # Send heartbeat every 30 seconds
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                
                # Check for new alerts
                alerts = await alert_service.get_pending_alerts()
                for alert in alerts:
                    yield f"data: {json.dumps(alert)}\n\n"
                
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            print("SSE connection closed")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
