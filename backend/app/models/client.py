from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Client(BaseModel):
    clientId: str
    name: str
    segment: str
    switchProb: float
    rm: str
    primaryExposure: str

class ClientProfile(BaseModel):
    clientId: str
    segment: str
    confidence: float
    switchProb: float
    drivers: List[str]
    riskFlags: List[str]
    primaryExposure: str
    rm: str

class Timeline(BaseModel):
    period: str
    segment: str
    description: str

class Insight(BaseModel):
    type: str  # SIGNAL, ACTION, OUTCOME
    severity: str  # HIGH, MEDIUM, LOW, SUCCESS
    timestamp: datetime
    message: str

class Media(BaseModel):
    pressure: str  # HIGH, MEDIUM, LOW
    headlines: List[dict]

class ActionCreate(BaseModel):
    clientId: str
    actionType: str
    product: str
    description: Optional[str] = None

class Action(ActionCreate):
    id: str
    timestamp: datetime
    status: str
