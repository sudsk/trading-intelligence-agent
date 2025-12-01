"""
API Facade - Thin routing layer

Proxies requests to agents-service and provides SSE streaming for alerts.
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException

from contextlib import asynccontextmanager
import logging
import os
import asyncio
import json
from datetime import datetime

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.agent_client import AgentClient
from services.alert_queue import AlertQueue
from services.data_service import DataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown"""
    logger.info("Starting API Facade...")
    
    # Initialize services
    app.state.agent_client = AgentClient()
    app.state.alert_queue = AlertQueue()
    app.state.data_service = DataService()
    
    logger.info("API Facade initialized successfully")
    logger.info(f"   - Agents Service URL: {app.state.agent_client.base_url}")
    
    yield
    
    logger.info("Shutting down API Facade...")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Trading Intelligence API",
    description="API facade for trading intelligence agents",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# Exception Handlers - MUST BE BEFORE MIDDLEWARE
# ============================================================================

@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    """Custom handler to ensure HTTPExceptions return JSONResponse"""
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_type": "unexpected_error",
            "timestamp": datetime.utcnow().isoformat(),
            "details": str(exc) if os.getenv("DEBUG") else None
        }
    )

# ============================================================================
# CORS Middleware
# ============================================================================
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ============================================================================
# Dependencies
# ============================================================================

def get_agent_client() -> AgentClient:
    """Get agent client instance"""
    return app.state.agent_client


def get_alert_queue() -> AlertQueue:
    """Get alert queue instance"""
    return app.state.alert_queue


def get_data_service() -> DataService:
    """Get data service instance"""
    return app.state.data_service


# ============================================================================
# Import Routes
# ============================================================================

from routes import clients, actions, alerts, demo

app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
app.include_router(actions.router, prefix="/api/v1/actions", tags=["actions"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(demo.router, prefix="/api/v1/demo", tags=["demo"])


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(content={
        "service": "Trading Intelligence API Facade",
        "version": "1.0.0",
        "description": "Thin routing layer to agents service",
        "endpoints": {
            "clients": "/api/v1/clients",
            "profile": "/api/v1/clients/{id}/profile",
            "timeline": "/api/v1/clients/{id}/timeline",
            "insights": "/api/v1/clients/{id}/insights",
            "media": "/api/v1/clients/{id}/media",
            "actions": "/api/v1/actions",
            "alerts": "/alerts/stream",
            "demo": "/api/v1/demo/trigger-alert"
        }
    })


@app.get("/health")
async def health_check(agent_client: AgentClient = Depends(get_agent_client)):
    """
    Health check - includes agents service health
    """
    try:
        # Check agents service
        agents_health = await agent_client.check_health()
        
        return JSONResponse(content={
            "status": "healthy",
            "facade": "healthy",
            "agents_service": agents_health.get("status", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "facade": "healthy",
                "agents_service": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level="info"
    )
