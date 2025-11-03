"""
Shared contracts between API Façade and Agents Service

These Pydantic models define the interface contract.
Both services import this to ensure type safety and consistency.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============================================================================
# REQUEST MODELS (Façade → Agents Service)
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request to analyze a client's trading profile"""
    client_id: str = Field(..., description="Client identifier")
    include_media: bool = Field(default=True, description="Include media analysis")
    include_recommendations: bool = Field(default=True, description="Include NBA recommendations")


class RecommendRequest(BaseModel):
    """Request for NBA recommendations only"""
    client_id: str
    segment: Optional[str] = None
    switch_prob: Optional[float] = None
    risk_flags: Optional[List[str]] = None
    media_pressure: Optional[str] = None
    primary_exposure: Optional[str] = None


class SegmentRequest(BaseModel):
    """Request for segmentation analysis only"""
    client_id: str


class MediaRequest(BaseModel):
    """Request for media analysis only"""
    client_id: str
    exposures: List[str] = Field(default_factory=list)


class HealthRequest(BaseModel):
    """Health check request"""
    detailed: bool = Field(default=False, description="Include detailed agent status")


# ============================================================================
# RESPONSE MODELS (Agents Service → Façade)
# ============================================================================

class SegmentationResult(BaseModel):
    """Segmentation agent output"""
    client_id: str
    segment: str = Field(..., description="One of: Trend Follower, Mean Reverter, Hedger, Trend Setter")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    switch_prob: float = Field(..., ge=0.0, le=1.0, description="14-day switch probability")
    drivers: List[str] = Field(..., description="Top 3 key drivers of classification")
    risk_flags: List[str] = Field(default_factory=list, description="Risk concerns")
    primary_exposure: str = Field(..., description="Primary instrument exposure")
    reasoning: Optional[str] = Field(None, description="Gemini's reasoning (for debugging)")
    features: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Raw features computed")


class HeadlineItem(BaseModel):
    """Single headline"""
    headline_id: str
    title: str
    sentiment: str = Field(..., description="positive, neutral, or negative")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    timestamp: str
    instrument: str
    source: str


class MediaAnalysisResult(BaseModel):
    """Media fusion agent output"""
    pressure: str = Field(..., description="HIGH, MEDIUM, or LOW")
    sentiment_avg: float = Field(..., ge=-1.0, le=1.0, description="Average sentiment score")
    sentiment_velocity: float = Field(..., description="Rate of sentiment change")
    headlines: List[HeadlineItem] = Field(default_factory=list, description="Top headlines")
    headline_count: int = Field(..., ge=0, description="Total headlines analyzed")
    reasoning: Optional[str] = Field(None, description="Gemini's reasoning")


class RecommendationItem(BaseModel):
    """Single NBA recommendation"""
    action: str = Field(..., description="Action type (e.g., PROACTIVE_OUTREACH)")
    priority: str = Field(..., description="HIGH, MEDIUM, or LOW")
    urgency: Optional[str] = Field(None, description="urgent, high, medium, low")
    message: str = Field(..., description="Human-readable recommendation message")
    products: List[str] = Field(default_factory=list, description="Suggested products")
    suggested_actions: List[str] = Field(default_factory=list, description="Specific action steps")
    reasoning: str = Field(..., description="Why this recommendation")
    timestamp: str


class NBAResult(BaseModel):
    """NBA agent output"""
    recommendations: List[RecommendationItem]
    reasoning: Optional[str] = Field(None, description="Gemini's overall reasoning")


class AnalyzeResponse(BaseModel):
    """Complete client profile analysis"""
    # Client identification
    client_id: str
    name: str
    rm: str
    sector: str
    
    # Segmentation results
    segment: str
    confidence: float
    switch_prob: float
    base_switch_prob: float = Field(..., description="Pre-media adjustment")
    drivers: List[str]
    risk_flags: List[str]
    primary_exposure: str
    
    # Media analysis
    media: MediaAnalysisResult
    
    # Recommendations
    recommendations: List[RecommendationItem]
    
    # Features (optional, for debugging)
    features: Optional[Dict[str, Any]] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata (timing, versions, etc.)"
    )


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="healthy, degraded, or unhealthy")
    orchestrator: str
    segmentation: str
    media_fusion: str
    nba: str
    gemini_enabled: bool
    timestamp: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# ERROR MODELS
# ============================================================================

class AgentError(BaseModel):
    """Standard error response"""
    error: str
    error_type: str = Field(..., description="e.g., validation_error, agent_error, timeout_error")
    client_id: Optional[str] = None
    timestamp: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# VALIDATION SCHEMAS
# ============================================================================

VALID_SEGMENTS = {"Trend Follower", "Mean Reverter", "Hedger", "Trend Setter"}
VALID_PRIORITIES = {"HIGH", "MEDIUM", "LOW"}
VALID_PRESSURES = {"HIGH", "MEDIUM", "LOW"}
VALID_SENTIMENTS = {"positive", "neutral", "negative"}
VALID_ACTIONS = {
    "PROACTIVE_OUTREACH",
    "ENHANCED_MONITORING",
    "PROPOSE_HEDGE",
    "SEND_MARKET_UPDATE",
    "SUGGEST_OPPORTUNITY"
}


def validate_segmentation_result(result: Dict[str, Any]) -> SegmentationResult:
    """Validate and parse segmentation result from Gemini"""
    if result.get("segment") not in VALID_SEGMENTS:
        raise ValueError(f"Invalid segment: {result.get('segment')}")
    
    if not 0.0 <= result.get("confidence", 0) <= 1.0:
        raise ValueError(f"Invalid confidence: {result.get('confidence')}")
    
    if not 0.0 <= result.get("switch_prob", 0) <= 1.0:
        raise ValueError(f"Invalid switch_prob: {result.get('switch_prob')}")
    
    return SegmentationResult(**result)


def validate_media_result(result: Dict[str, Any]) -> MediaAnalysisResult:
    """Validate and parse media analysis result from Gemini"""
    if result.get("pressure") not in VALID_PRESSURES:
        raise ValueError(f"Invalid pressure: {result.get('pressure')}")
    
    if not -1.0 <= result.get("sentiment_avg", 0) <= 1.0:
        raise ValueError(f"Invalid sentiment_avg: {result.get('sentiment_avg')}")
    
    return MediaAnalysisResult(**result)


def validate_nba_result(result: Dict[str, Any]) -> NBAResult:
    """Validate and parse NBA result from Gemini"""
    recommendations = result.get("recommendations", [])
    
    for rec in recommendations:
        if rec.get("action") not in VALID_ACTIONS:
            raise ValueError(f"Invalid action: {rec.get('action')}")
        
        if rec.get("priority") not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority: {rec.get('priority')}")
    
    return NBAResult(**result)
