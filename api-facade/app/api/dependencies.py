"""API dependencies and common utilities"""
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key (optional for demo)"""
    # In production, implement proper API key verification
    # For demo, we skip this
    return True
