"""
Trade MCP Server - Mock for Demo/PoC

Returns realistic trade data from CSV files.
In production, replace with Oracle OMS queries.
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


# ============================================================================
# Data Models
# ============================================================================

class ToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


class ToolResponse(BaseModel):
    result: Dict[str, Any]
    error: Optional[str] = None


# ============================================================================
# Mock Trade MCP Server
# ============================================================================

class MockTradeMCPServer:
    """Mock MCP server that reads trade data from CSV files"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Load or generate mock data
        self.trades_df = self._load_or_generate_trades()
        
        logger.info(f"✅ Trade MCP Server initialized ({len(self.trades_df)} trades)")
    
    def _load_or_generate_trades(self) -> pd.DataFrame:
        """Load trades from CSV or generate if not exists"""
        trades_file = self.data_dir / "trades.csv"
        
        if trades_file.exists():
            df = pd.read_csv(trades_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        else:
            logger.info("Generating mock trades...")
            trades = self._generate_mock_trades()
            df = pd.DataFrame(trades)
            df.to_csv(trades_file, index=False)
            logger.info(f"✅ Generated {len(df)} mock trades")
            return df
    
    def _generate_mock_trades(self) -> List[Dict]:
        """Generate realistic mock trades"""
        import random
        
        clients = ['ACME_FX_023', 'ZEUS_COMM_019', 'TITAN_EQ_008', 'ATLAS_BOND_012']
        instruments = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF']
        sides = ['BUY', 'SELL']
        order_types = ['MARKET', 'LIMIT', 'STOP']
        venues = ['LMAX', 'EBS', 'Hotspot', 'Currenex']
        
        trades = []
        base_date = datetime.now() - timedelta(days=90)
        
        for i in range(2000):
            client = random.choice(clients)
            instrument = random.choice(instruments)
            
            trade = {
                'trade_id': f"TRD{i+1:06d}",
                'client_id': client,
                'instrument': instrument,
                'side': random.choice(sides),
                'quantity': random.randint(100000, 5000000),
                'price': round(random.uniform(1.0, 1.5), 5),
                'timestamp': (base_date + timedelta(
                    days=random.randint(0, 90),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )).isoformat(),
                'order_type': random.choice(order_types),
                'venue': random.choice(venues)
            }
            trades.append(trade)
        
        return trades
    
    # ========================================================================
    # MCP Tools
    # ========================================================================
    
    def get_client_trades(
        self,
        client_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get individual trades for a client"""
        logger.info(f"📊 get_client_trades: {client_id}")
        
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
            
            logger.info(f"✅ Returning {len(trades_list)} trades")
            
            return {
                'trades': trades_list,
                'count': len(trades_list)
            }
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return {'error': str(e), 'trades': [], 'count': 0}
    
    def get_trade_summary(
        self,
        client_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """Get aggregated trade statistics"""
        logger.info(f"📊 get_trade_summary: {client_id}, {days} days")
        
        try:
            cutoff = datetime.now() - timedelta(days=days)
            trades = self.trades_df[
                (self.trades_df['client_id'] == client_id) &
                (self.trades_df['timestamp'] >= cutoff)
            ].copy()
            
            if trades.empty:
                return {
                    'summary': {
                        'trade_count': 0,
                        'unique_instruments': 0,
                        'instruments': [],
                        'market_order_ratio': 0.0
                    }
                }
            
            summary = {
                'trade_count': len(trades),
                'unique_instruments': trades['instrument'].nunique(),
                'instruments': trades['instrument'].unique().tolist(),
                'market_order_ratio': (trades['order_type'] == 'MARKET').mean(),
                'avg_quantity': float(trades['quantity'].mean()),
                'total_volume': float(trades['quantity'].sum())
            }
            
            logger.info(f"✅ Summary: {summary['trade_count']} trades")
            return {'summary': summary}
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return {'error': str(e), 'summary': {}}
    
    def get_position_flips(
        self,
        client_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """Count position direction reversals"""
        logger.info(f"📊 get_position_flips: {client_id}")
        
        try:
            cutoff = datetime.now() - timedelta(days=days)
            trades = self.trades_df[
                (self.trades_df['client_id'] == client_id) &
                (self.trades_df['timestamp'] >= cutoff)
            ].copy()
            
            if trades.empty:
                return {'flips': {'total_flips': 0, 'daily_flips': []}}
            
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
            logger.error(f"❌ Error: {e}")
            return {'error': str(e), 'flips': {'total_flips': 0}}


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Trade MCP Server (Mock)",
    description="Mock MCP server for demo - returns realistic trade data from CSV",
    version="1.0.0"
)

server = MockTradeMCPServer(data_dir="./data")


@app.post("/call_tool", response_model=ToolResponse)
async def call_tool(request: ToolRequest):
    """MCP tool call endpoint"""
    logger.info(f"🔧 Tool called: {request.tool_name}")
    
    try:
        if request.tool_name == "get_client_trades":
            result = server.get_client_trades(**request.arguments)
        elif request.tool_name == "get_trade_summary":
            result = server.get_trade_summary(**request.arguments)
        elif request.tool_name == "get_position_flips":
            result = server.get_position_flips(**request.arguments)
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Tool not found: {request.tool_name}"
            )
        
        return ToolResponse(result=result)
        
    except Exception as e:
        logger.error(f"❌ Tool error: {e}")
        return ToolResponse(result={}, error=str(e))


@app.get("/tools")
async def list_tools():
    """List available tools"""
    return {
        "tools": [
            {
                "name": "get_client_trades",
                "description": "Get individual trades for a client",
                "parameters": {
                    "client_id": "string (required)",
                    "start_date": "string (optional, ISO format)",
                    "end_date": "string (optional, ISO format)"
                }
            },
            {
                "name": "get_trade_summary",
                "description": "Get aggregated trade statistics",
                "parameters": {
                    "client_id": "string (required)",
                    "days": "integer (optional, default 90)"
                }
            },
            {
                "name": "get_position_flips",
                "description": "Count position direction reversals",
                "parameters": {
                    "client_id": "string (required)",
                    "days": "integer (optional, default 90)"
                }
            }
        ]
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "server": "Trade MCP Server (Mock)",
        "trades_loaded": len(server.trades_df)
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Trade MCP Server (Mock)",
        "version": "1.0.0",
        "description": "Mock MCP server for demo/PoC",
        "endpoints": {
            "call_tool": "POST /call_tool",
            "list_tools": "GET /tools",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3001"))
    logger.info(f"🚀 Starting Trade MCP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")