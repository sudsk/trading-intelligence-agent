"""
Client MCP Server - Mock Implementation
"""
import os
import logging
from datetime import datetime
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

class MockClientMCPServer:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.clients_df = self._load_or_generate_clients()
        self.actions_df = self._load_or_generate_actions()
        logger.info(f"✅ Loaded {len(self.clients_df)} clients")
    
    def _load_or_generate_clients(self) -> pd.DataFrame:
        file = self.data_dir / "clients.csv"
        if file.exists():
            return pd.read_csv(file)
        
        clients = [
            {
                'client_id': 'ACME_FX_023',
                'name': 'ACME Corporation',
                'rm': 'Sarah Chen',
                'sector': 'Technology',
                'region': 'North America',
                'tier': 'Tier 1',
                'onboarding_date': '2020-03-15'
            },
            {
                'client_id': 'ZEUS_COMM_019',
                'name': 'Zeus Commodities',
                'rm': 'Michael Torres',
                'sector': 'Commodities',
                'region': 'Europe',
                'tier': 'Tier 1',
                'onboarding_date': '2019-07-22'
            },
            {
                'client_id': 'TITAN_EQ_008',
                'name': 'Titan Equity Fund',
                'rm': 'Sarah Chen',
                'sector': 'Asset Management',
                'region': 'Asia',
                'tier': 'Tier 2',
                'onboarding_date': '2021-01-10'
            },
            {
                'client_id': 'ATLAS_BOND_012',
                'name': 'Atlas Fixed Income',
                'rm': 'James Wong',
                'sector': 'Asset Management',
                'region': 'Europe',
                'tier': 'Tier 1',
                'onboarding_date': '2018-11-05'
            }
        ]
        
        df = pd.DataFrame(clients)
        df.to_csv(file, index=False)
        return df
    
    def _load_or_generate_actions(self) -> pd.DataFrame:
        file = self.data_dir / "actions.csv"
        if file.exists():
            return pd.read_csv(file)
        
        return pd.DataFrame(columns=[
            'action_id', 'client_id', 'action_type', 'title', 
            'description', 'timestamp', 'status'
        ])
    
    def get_client_metadata(self, client_id: str) -> Dict[str, Any]:
        try:
            client = self.clients_df[self.clients_df['client_id'] == client_id]
            if client.empty:
                return {'metadata': {}}
            return {'metadata': client.iloc[0].to_dict()}
        except Exception as e:
            return {'error': str(e), 'metadata': {}}
    
    def list_clients(self, search: Optional[str] = None, segment: Optional[str] = None,
                    rm: Optional[str] = None) -> Dict[str, Any]:
        try:
            clients = self.clients_df.copy()
            
            if search:
                clients = clients[
                    clients['name'].str.contains(search, case=False, na=False) |
                    clients['client_id'].str.contains(search, case=False, na=False)
                ]
            
            if rm:
                clients = clients[clients['rm'] == rm]
            
            return {'clients': clients.to_dict('records'), 'count': len(clients)}
        except Exception as e:
            return {'error': str(e), 'clients': []}
    
    def log_action(self, client_id: str, action_type: str, title: str,
                  description: Optional[str] = None) -> Dict[str, Any]:
        try:
            action_id = f"ACT{len(self.actions_df)+1:06d}"
            new_action = {
                'action_id': action_id,
                'client_id': client_id,
                'action_type': action_type,
                'title': title,
                'description': description or '',
                'timestamp': datetime.now().isoformat(),
                'status': 'PENDING'
            }
            
            self.actions_df = pd.concat([
                self.actions_df,
                pd.DataFrame([new_action])
            ], ignore_index=True)
            
            self.actions_df.to_csv(self.data_dir / "actions.csv", index=False)
            
            return {'action': new_action, 'success': True}
        except Exception as e:
            return {'error': str(e), 'success': False}

app = FastAPI(title="Client MCP Server", version="1.0.0")
server = MockClientMCPServer()

@app.post("/call_tool", response_model=ToolResponse)
async def call_tool(request: ToolRequest):
    try:
        if request.tool_name == "get_client_metadata":
            result = server.get_client_metadata(**request.arguments)
        elif request.tool_name == "list_clients":
            result = server.list_clients(**request.arguments)
        elif request.tool_name == "log_action":
            result = server.log_action(**request.arguments)
        else:
            raise HTTPException(404, f"Tool not found: {request.tool_name}")
        return ToolResponse(result=result)
    except Exception as e:
        return ToolResponse(result={}, error=str(e))

@app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {"name": "get_client_metadata", "description": "Get client details"},
            {"name": "list_clients", "description": "Search/list clients"},
            {"name": "log_action", "description": "Log RM action"}
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "clients_loaded": len(server.clients_df)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3005"))
    uvicorn.run(app, host="0.0.0.0", port=port)
