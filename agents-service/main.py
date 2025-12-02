"""
Agents Service - Pure Gemini ADK Agents

This service hosts all trading intelligence agents and exposes them via FastAPI.
Designed to run on Cloud Run now, easily migrate to Agent Engine later.
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from datetime import datetime

# Import shared contracts
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.agent_contracts import (
    AnalyzeRequest, AnalyzeResponse,
    SegmentRequest, SegmentationResult,
    MediaRequest, MediaAnalysisResult,
    RecommendRequest, NBAResult,
    HealthRequest, HealthResponse,
    AgentError
)

from agents.orchestrator_agent.agent import OrchestratorAgent
from services.data_service import DataService
from services.mcp_data_service import MCPDataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agents on startup, cleanup on shutdown"""
    logger.info("🚀 Starting Agents Service...")
    
    # Initialize data service
    app.state.data_service = MCPDataService()
    
    # Initialize orchestrator (which initializes all specialist agents)
    app.state.orchestrator = OrchestratorAgent(
        data_service=app.state.data_service
    )
    
    logger.info("✅ All agents initialized successfully")
    logger.info(f"   - Orchestrator: Ready")
    logger.info(f"   - Segmentation Agent: Ready")
    logger.info(f"   - Media Fusion Agent: Ready")
    logger.info(f"   - NBA Agent: Ready")
    
    # Check Gemini availability
    gemini_status = "enabled" if app.state.orchestrator.media_agent.sentiment_enabled else "disabled"
    logger.info(f"   - Gemini Flash 2.5: {gemini_status}")
    
    yield
    
    logger.info("🛑 Shutting down Agents Service...")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Trading Intelligence Agents Service",
    description="Pure Gemini ADK agents for trading intelligence analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Dependency Injection
# ============================================================================

def get_orchestrator() -> OrchestratorAgent:
    """Get orchestrator agent instance"""
    return app.state.orchestrator

# Dependency for database data service (agent state)
def get_data_service() -> DataService:
    """Get data service instance"""
    return app.state.data_service

# Dependency for MCP data service
def get_mcp_data_service() -> MCPDataService:
    return app.state.mcp_data_service

# ============================================================================
# Agent Endpoints
# ============================================================================
@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_client(
    request: AnalyzeRequest,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Complete client profile analysis"""
    logger.info(f"📊 Analyzing client: {request.client_id}")
    
    try:
        start_time = datetime.utcnow()
        
        # Call orchestrator
        profile = orchestrator.get_client_profile(
            client_id=request.client_id
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Add metadata
        profile['metadata'] = {
            'execution_time_seconds': round(execution_time, 2),
            'timestamp': datetime.utcnow().isoformat(),
            'agents_called': ['orchestrator', 'segmentation', 'media_fusion', 'nba'],
            'service': 'agents-service',
            'version': '1.0.0'
        }
        
        # Validate against contract before returning
        try:
            from shared.agent_contracts import AnalyzeResponse
            validated = AnalyzeResponse(**profile)
            return validated.model_dump()  # Return dict that matches contract
        except Exception as validation_error:
            logger.error(f"Response validation error: {validation_error}")
            logger.error(f"Profile keys: {profile.keys()}")
            logger.error(f"Media keys: {profile.get('media', {}).keys()}")
            raise HTTPException(
                status_code=500,
                detail=f"Response validation failed: {str(validation_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing {request.client_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_type": "agent_error",
                "client_id": request.client_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.post("/segment", response_model=SegmentationResult)
async def segment_client(
    request: SegmentRequest,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """
    Segmentation analysis only.
    
    Returns segment classification without media or recommendations.
    Useful for batch processing or debugging.
    """
    logger.info(f"🎯 Segmenting client: {request.client_id}")
    
    try:
        result = orchestrator.segmentation_agent.analyze(request.client_id)
        logger.info(f"✅ Segmented {request.client_id}: {result.get('segment')}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error segmenting {request.client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/media", response_model=MediaAnalysisResult)
async def analyze_media(
    request: MediaRequest,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """
    Media analysis only.
    
    Returns media sentiment and pressure without full profile.
    """
    logger.info(f"📰 Analyzing media for client: {request.client_id}")
    
    try:
        result = orchestrator.media_agent.analyze(
            client_id=request.client_id,
            exposures=request.exposures
        )
        logger.info(
            f"✅ Media analyzed for {request.client_id}: "
            f"pressure={result.get('pressure')}, "
            f"headlines={result.get('headlineCount')}"
        )
        return result
        
    except Exception as e:
        logger.error(f"❌ Error analyzing media for {request.client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend", response_model=NBAResult)
async def get_recommendations(
    request: RecommendRequest,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """
    NBA recommendations only.
    
    Returns action recommendations given context.
    """
    logger.info(f"💡 Generating recommendations for: {request.client_id}")
    
    try:
        recommendations = orchestrator.nba_agent.recommend(
            client_id=request.client_id,
            segment=request.segment or "Unclassified",
            switch_prob=request.switch_prob or 0.3,
            risk_flags=request.risk_flags or [],
            media_pressure=request.media_pressure or "LOW",
            primary_exposure=request.primary_exposure
        )
        
        logger.info(
            f"✅ Generated {len(recommendations)} recommendations "
            f"for {request.client_id}"
        )
        
        return {"recommendations": recommendations}
        
    except Exception as e:
        logger.error(f"❌ Error generating recommendations for {request.client_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/health", response_model=HealthResponse)
async def health_check(
    request: HealthRequest = HealthRequest(),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """
    Health check with optional detailed agent status.
    """
    try:
        health = orchestrator.get_agent_health()
        
        # Determine overall status
        agent_statuses = [
            health.get('orchestrator'),
            health.get('segmentation'),
            health.get('media_fusion'),
            health.get('nba')
        ]
        
        if all(status == 'healthy' for status in agent_statuses):
            overall_status = 'healthy'
        elif any(status == 'healthy' for status in agent_statuses):
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        response = HealthResponse(
            status=overall_status,
            orchestrator=health.get('orchestrator', 'unknown'),
            segmentation=health.get('segmentation', 'unknown'),
            media_fusion=health.get('media_fusion', 'unknown'),
            nba=health.get('nba', 'unknown'),
            gemini_enabled=health.get('media_fusion_gemini') == 'enabled',
            timestamp=health.get('timestamp', datetime.utcnow().isoformat()),
            details=health if request.detailed else None
        )
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return HealthResponse(
            status='unhealthy',
            orchestrator='error',
            segmentation='error',
            media_fusion='error',
            nba='error',
            gemini_enabled=False,
            timestamp=datetime.utcnow().isoformat(),
            details={"error": str(e)}
        )


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Trading Intelligence Agents Service",
        "version": "1.0.0",
        "description": "Pure Gemini ADK agents for trading intelligence",
        "endpoints": {
            "analyze": "POST /analyze - Complete client profile",
            "segment": "POST /segment - Segmentation only",
            "media": "POST /media - Media analysis only",
            "recommend": "POST /recommend - NBA recommendations only",
            "health": "POST /health - Health check"
        },
        "agents": [
            "Orchestrator",
            "Segmentation (Gemini Flash 2.5)",
            "Media Fusion (Gemini Flash 2.5)",
            "NBA (Gemini Flash 2.5)"
        ]
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler"""
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        log_level="info"
    )
