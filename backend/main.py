from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import clients, alerts, actions
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading Intelligence API",
    version="1.0.0",
    description="Backend facade for Trading Intelligence Agent"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
app.include_router(actions.router, prefix="/api/v1/actions", tags=["actions"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])

@app.get("/")
async def root():
    return {"message": "Trading Intelligence API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
