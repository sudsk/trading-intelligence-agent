"""
News MCP Server - Mock Implementation
"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class ToolResponse(BaseModel):
    result: Dict[str, Any]
    error: Optional[str] = None

class MockNewsMCPServer:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.headlines_df = self._load_or_generate_headlines()
        logger.info(f"✅ Loaded {len(self.headlines_df)} headlines")
    
    def _load_or_generate_headlines(self) -> pd.DataFrame:
        file = self.data_dir / "headlines.csv"
        if file.exists():
            df = pd.read_csv(file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        else:
            raise FileNotFoundError(
                f"headlines.csv not found in {self.data_dir}. "
            )  
    
    def get_headlines(self, instruments: List[str], hours: int = 72) -> Dict[str, Any]:
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            headlines = self.headlines_df[
                (self.headlines_df['instrument'].isin(instruments)) &
                (self.headlines_df['timestamp'] >= cutoff)
            ].copy()
            
            headlines_list = headlines.to_dict('records')
            for headline in headlines_list:
                if isinstance(headline['timestamp'], pd.Timestamp):
                    headline['timestamp'] = headline['timestamp'].isoformat()
                headline['published_at'] = headline['timestamp']  
            
            return {'headlines': headlines_list, 'count': len(headlines_list)}
        except Exception as e:
            return {'error': str(e), 'headlines': []}
    
    def get_sentiment(self, headline_ids: List[str]) -> Dict[str, Any]:
        try:
            headlines = self.headlines_df[
                self.headlines_df['headline_id'].isin(headline_ids)
            ]
            
            sentiments = {}
            for _, row in headlines.iterrows():
                sentiments[row['headline_id']] = {
                    'sentiment': row['sentiment'],
                    'score': float(row['sentiment_score'])
                }
            
            return {'sentiments': sentiments}
        except Exception as e:
            return {'error': str(e), 'sentiments': {}}
    
    def get_macro_events(self, days: int = 7) -> Dict[str, Any]:
        import random
        try:
            events = [
                {'date': (datetime.now() + timedelta(days=i)).isoformat(),
                 'event': random.choice(['Fed Meeting', 'ECB Decision', 'NFP', 'CPI Release']),
                 'importance': random.choice(['HIGH', 'MEDIUM', 'LOW'])}
                for i in range(days)
            ]
            return {'events': events}
        except Exception as e:
            return {'error': str(e), 'events': []}

app = FastAPI(title="News MCP Server", version="1.0.0")
server = MockNewsMCPServer()

@app.post("/call_tool", response_model=ToolResponse)
async def call_tool(request: ToolRequest):
    try:
        if request.tool_name == "get_headlines":
            result = server.get_headlines(**request.arguments)
        elif request.tool_name == "get_sentiment":
            result = server.get_sentiment(**request.arguments)
        elif request.tool_name == "get_macro_events":
            result = server.get_macro_events(**request.arguments)
        else:
            raise HTTPException(404, f"Tool not found: {request.tool_name}")
        return ToolResponse(result=result)
    except Exception as e:
        return ToolResponse(result={}, error=str(e))

@app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {"name": "get_headlines", "description": "Get recent headlines"},
            {"name": "get_sentiment", "description": "Get sentiment scores"},
            {"name": "get_macro_events", "description": "Get upcoming macro events"}
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "headlines_loaded": len(server.headlines_df)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3004"))
    uvicorn.run(app, host="0.0.0.0", port=port)
