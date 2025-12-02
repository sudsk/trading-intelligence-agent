"""
Market MCP Server - Mock Implementation
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

class MockMarketMCPServer:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.market_bars_df = self._load_or_generate_market_bars()
        logger.info(f"✅ Loaded {len(self.market_bars_df)} market bars")
    
    def _load_or_generate_market_bars(self) -> pd.DataFrame:
        file = self.data_dir / "market_bars.csv"
        if file.exists():
            df = pd.read_csv(file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        else:
            raise FileNotFoundError(
                f"market_bars.csv not found in {self.data_dir}. "
            )

    def get_market_bars(self, instruments: List[str], start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> Dict[str, Any]:
        try:
            bars = self.market_bars_df[self.market_bars_df['instrument'].isin(instruments)].copy()
            
            if start_date:
                bars = bars[bars['timestamp'] >= pd.to_datetime(start_date)]
            if end_date:
                bars = bars[bars['timestamp'] <= pd.to_datetime(end_date)]
            
            bars_list = bars.to_dict('records')
            for bar in bars_list:
                if isinstance(bar['timestamp'], pd.Timestamp):
                    bar['timestamp'] = bar['timestamp'].isoformat()
            
            return {'bars': bars_list, 'count': len(bars_list)}
        except Exception as e:
            return {'error': str(e), 'bars': []}
    
    def get_current_prices(self, instruments: List[str]) -> Dict[str, Any]:
        try:
            latest_bars = self.market_bars_df[
                self.market_bars_df['instrument'].isin(instruments)
            ].groupby('instrument').last()
            
            prices = {}
            for inst in instruments:
                if inst in latest_bars.index:
                    prices[inst] = float(latest_bars.loc[inst, 'close'])
            
            return {'prices': prices}
        except Exception as e:
            return {'error': str(e), 'prices': {}}
    
    def get_correlations(self, instruments: List[str], days: int = 30) -> Dict[str, Any]:
        import random
        try:
            corr_matrix = {}
            for inst1 in instruments:
                corr_matrix[inst1] = {}
                for inst2 in instruments:
                    if inst1 == inst2:
                        corr_matrix[inst1][inst2] = 1.0
                    else:
                        corr_matrix[inst1][inst2] = round(random.uniform(-0.5, 0.9), 3)
            
            return {'correlations': corr_matrix}
        except Exception as e:
            return {'error': str(e), 'correlations': {}}

app = FastAPI(title="Market MCP Server", version="1.0.0")
server = MockMarketMCPServer()

@app.post("/call_tool", response_model=ToolResponse)
async def call_tool(request: ToolRequest):
    try:
        if request.tool_name == "get_market_bars":
            result = server.get_market_bars(**request.arguments)
        elif request.tool_name == "get_current_prices":
            result = server.get_current_prices(**request.arguments)
        elif request.tool_name == "get_correlations":
            result = server.get_correlations(**request.arguments)
        else:
            raise HTTPException(404, f"Tool not found: {request.tool_name}")
        return ToolResponse(result=result)
    except Exception as e:
        return ToolResponse(result={}, error=str(e))

@app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {"name": "get_market_bars", "description": "Get OHLCV bars"},
            {"name": "get_current_prices", "description": "Get latest prices"},
            {"name": "get_correlations", "description": "Get correlation matrix"}
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "bars_loaded": len(server.market_bars_df)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3003"))
    uvicorn.run(app, host="0.0.0.0", port=port)
