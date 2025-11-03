from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Trading Intelligence API"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]
    
    # GCP
    GCP_PROJECT_ID: str
    GCP_REGION: str = "us-central1"
    VERTEX_AI_AGENT_ENDPOINT: str = ""
    
    # Data
    DATA_PATH: str = "./data/raw"
    
    # Demo mode
    DEMO_MODE: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
