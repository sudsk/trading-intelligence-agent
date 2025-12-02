"""
Trade MCP Server - Mock Implementation

Returns realistic trade data from CSV files.
In production, replace CSV reading with Oracle/Murex queries.
"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from typing import Dict, Any, Optional
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

class MockTradeMCPServer:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.trades_df = self._load_or_generate_trades()
        logger.info(f"✅ Loaded {len(self.trades_df)} trades")
    
    def _load_or_generate_trades(self) -> pd.DataFrame:
        trades_file = self.data_dir / "trades.csv"
        if trades_file.exists():
            df = pd.read_csv(trades_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        else:
            raise FileNotFoundError(
                f"trades.csv not found in {self.data_dir}. "
            )
    
    def _generate_trades(self) -> pd.DataFrame:
        import random
        clients = ['ACME_FX_023', 'ZEUS_COMM_019', 'TITAN_EQ_008', 'ATLAS_BOND_012']
        instruments = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF']
        sides = ['BUY', 'SELL']
        order_types = ['MARKET', 'LIMIT']
        venues = ['LMAX', 'EBS', 'Hotspot', 'Currenex']
        
        trades = []
        base_date = datetime.now() - timedelta(days=90)
        
        for i in range(2000):
            trade = {
                'trade_id': f"TRD{i+1:06d}",
                'client_id': random.choice(clients),
                'instrument': random.choice(instruments),
                'side': random.choice(sides),
                'quantity': random.randint(100000, 5000000),
                'price': round(random.uniform(1.0, 1.5), 5),
                'timestamp': (base_date + timedelta(
                    days=random.randint(0, 90),
                    hours=random.randint(0, 23)
                )).isoformat(),
                'order_type': random.choice(order_types),
                'venue': random.choice(venues)
            }
            trades.append(trade)
        
        df = pd.DataFrame(trades)
        df.to_csv(self.data_dir / "trades.csv", index=False)
        logger.info(f"Generated {len(df)} mock trades")
        return df
    
    def get_client_trades(self, client_id: str, start_date: Optional[str] = None, 
                         end_date: Optional[str] = None) -> Dict[str, Any]:
        try:
            trades = self.trades_df[self.trades_df['client_id'] == client_id].copy()
            if start_date:
                trades = trades[trades['timestamp'] >= pd.to_datetime(start_date)]
            if end_date:
                trades = trades[trades['timestamp'] <= pd.to_datetime(end_date)]
            
            trades_list = trades.to_dict('records')
            for trade in trades_list:
                if isinstance(trade['timestamp'], pd.Timestamp):
                    trade['timestamp'] = trade['timestamp'].isoformat()
            
            return {'trades': trades_list, 'count': len(trades_list)}
        except Exception as e:
            return {'error': str(e), 'trades': [], 'count': 0}
    
    def get_trade_summary(self, client_id: str, days: int = 90) -> Dict[str, Any]:
        try:
            cutoff = datetime.now() - timedelta(days=days)
            trades = self.trades_df[
                (self.trades_df['client_id'] == client_id) &
                (self.trades_df['timestamp'] >= cutoff)
            ].copy()
            
            if trades.empty:
                return {'summary': {'trade_count': 0, 'unique_instruments': 0}}
            
            summary = {
                'trade_count': len(trades),
                'unique_instruments': trades['instrument'].nunique(),
                'instruments': trades['instrument'].unique().tolist(),
                'market_order_ratio': (trades['order_type'] == 'MARKET').mean(),
                'avg_quantity': float(trades['quantity'].mean()),
                'total_volume': float(trades['quantity'].sum())
            }
            return {'summary': summary}
        except Exception as e:
            return {'error': str(e), 'summary': {}}
    
    def get_position_flips(self, client_id: str, days: int = 90) -> Dict[str, Any]:
        try:
            cutoff = datetime.now() - timedelta(days=days)
            trades = self.trades_df[
                (self.trades_df['client_id'] == client_id) &
                (self.trades_df['timestamp'] >= cutoff)
            ].copy()
            
            if trades.empty:
                return {'flips': {'total_flips': 0, 'flip_rate': 0.0}}
            
            trades = trades.sort_values('timestamp')
            flips = (trades['side'] != trades['side'].shift()).sum() - 1
            
            return {
                'flips': {
                    'total_flips': int(flips),
                    'days_analyzed': days,
                    'flip_rate': float(flips / days) if days > 0 else 0.0
                }
            }
        except Exception as e:
            return {'error': str(e), 'flips': {'total_flips': 0}}

app = FastAPI(title="Trade MCP Server", version="1.0.0")
server = MockTradeMCPServer()

@app.post("/call_tool", response_model=ToolResponse)
async def call_tool(request: ToolRequest):
    try:
        if request.tool_name == "get_client_trades":
            result = server.get_client_trades(**request.arguments)
        elif request.tool_name == "get_trade_summary":
            result = server.get_trade_summary(**request.arguments)
        elif request.tool_name == "get_position_flips":
            result = server.get_position_flips(**request.arguments)
        else:
            raise HTTPException(404, f"Tool not found: {request.tool_name}")
        return ToolResponse(result=result)
    except Exception as e:
        return ToolResponse(result={}, error=str(e))

@app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {"name": "get_client_trades", "description": "Get individual trades"},
            {"name": "get_trade_summary", "description": "Get trade statistics"},
            {"name": "get_position_flips", "description": "Count position reversals"}
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "trades_loaded": len(server.trades_df)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
