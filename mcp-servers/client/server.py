"""
Client MCP Server - 20 Clients with Database Cache

Returns client metadata enriched with latest switch probability from database.
"""
import os
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
import psycopg2
from typing import Dict, Any, Optional, List
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
        
        # Database connection for switch probability cache
        self.database_url = os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@db:5432/trading_intelligence'
        )
        
        logger.info(f"✅ Loaded {len(self.clients_df)} clients")
    
    def _get_db_connection(self):
        """Get database connection."""
        try:
            return psycopg2.connect(self.database_url)
        except Exception as e:
            logger.warning(f"⚠️ Database connection failed: {e}")
            return None
    
    def _get_latest_switch_probs(self, client_ids: List[str] = None) -> Dict[str, Dict]:
        """
        Get latest switch probabilities from database.
        
        Returns dict: {client_id: {switch_prob, computed_at, segment}}
        """
        conn = self._get_db_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Get latest switch probability for each client
            query = """
                SELECT DISTINCT ON (client_id)
                    client_id,
                    switch_prob,
                    segment,
                    computed_at
                FROM switch_probability_history
                WHERE 1=1
            """
            
            params = []
            if client_ids:
                query += " AND client_id = ANY(%s)"
                params.append(client_ids)
            
            query += " ORDER BY client_id, computed_at DESC"
            
            cursor.execute(query, params if params else None)
            rows = cursor.fetchall()
            
            result = {}
            for row in rows:
                result[row[0]] = {
                    'switch_prob': float(row[1]) if row[1] else None,
                    'segment': row[2],
                    'computed_at': row[3].isoformat() if row[3] else None
                }
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Retrieved switch probs for {len(result)} clients from cache")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error fetching switch probs: {e}")
            if conn:
                conn.close()
            return {}
    
    def _load_or_generate_clients(self) -> pd.DataFrame:
        clients_file = self.data_dir / "clients.csv"
        if clients_file.exists():
            return pd.read_csv(clients_file)
        else:
            return self._generate_clients()
    
    def _generate_clients(self) -> pd.DataFrame:
        """Generate 20 mock clients with diverse profiles"""
        clients = [
            # Tier 1 - North America
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
                'client_id': 'PHOENIX_CAPITAL_031',
                'name': 'Phoenix Capital Partners',
                'rm': 'Michael Torres',
                'sector': 'Private Equity',
                'region': 'North America',
                'tier': 'Tier 1',
                'onboarding_date': '2019-06-20'
            },
            {
                'client_id': 'APEX_TRADING_089',
                'name': 'Apex Trading Group',
                'rm': 'Sarah Chen',
                'sector': 'Prop Trading',
                'region': 'North America',
                'tier': 'Tier 1',
                'onboarding_date': '2021-02-10'
            },
            {
                'client_id': 'PINNACLE_WEALTH_064',
                'name': 'Pinnacle Wealth Management',
                'rm': 'James Wong',
                'sector': 'Wealth Management',
                'region': 'North America',
                'tier': 'Tier 1',
                'onboarding_date': '2018-09-05'
            },
            
            # Tier 1 - Europe
            {
                'client_id': 'ATLAS_BOND_012',
                'name': 'Atlas Fixed Income',
                'rm': 'James Wong',
                'sector': 'Asset Management',
                'region': 'Europe',
                'tier': 'Tier 1',
                'onboarding_date': '2018-11-05'
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
                'client_id': 'STERLING_FX_041',
                'name': 'Sterling FX Solutions',
                'rm': 'Emma Richardson',
                'sector': 'FX Trading',
                'region': 'Europe',
                'tier': 'Tier 1',
                'onboarding_date': '2020-04-18'
            },
            {
                'client_id': 'HORIZON_GLOBAL_056',
                'name': 'Horizon Global Macro',
                'rm': 'Michael Torres',
                'sector': 'Hedge Fund',
                'region': 'Europe',
                'tier': 'Tier 1',
                'onboarding_date': '2019-12-08'
            },
            
            # Tier 1 - Asia
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
                'client_id': 'QUANTUM_FINANCE_015',
                'name': 'Quantum Finance Corp',
                'rm': 'James Wong',
                'sector': 'Investment Bank',
                'region': 'Asia',
                'tier': 'Tier 1',
                'onboarding_date': '2017-05-22'
            },
            {
                'client_id': 'NEXUS_CAPITAL_017',
                'name': 'Nexus Capital Asia',
                'rm': 'Emma Richardson',
                'sector': 'Venture Capital',
                'region': 'Asia',
                'tier': 'Tier 1',
                'onboarding_date': '2020-08-14'
            },
            
            # Tier 2 - Diverse
            {
                'client_id': 'OLYMPUS_VENTURES_024',
                'name': 'Olympus Ventures',
                'rm': 'Sarah Chen',
                'sector': 'Private Equity',
                'region': 'Europe',
                'tier': 'Tier 2',
                'onboarding_date': '2021-03-12'
            },
            {
                'client_id': 'CORNERSTONE_INV_033',
                'name': 'Cornerstone Investments',
                'rm': 'Michael Torres',
                'sector': 'Asset Management',
                'region': 'North America',
                'tier': 'Tier 2',
                'onboarding_date': '2020-11-20'
            },
            {
                'client_id': 'NOVA_MACRO_045',
                'name': 'Nova Macro Fund',
                'rm': 'Emma Richardson',
                'sector': 'Hedge Fund',
                'region': 'North America',
                'tier': 'Tier 2',
                'onboarding_date': '2021-06-30'
            },
            {
                'client_id': 'SUMMIT_ADVISORS_051',
                'name': 'Summit Financial Advisors',
                'rm': 'James Wong',
                'sector': 'Financial Services',
                'region': 'Europe',
                'tier': 'Tier 2',
                'onboarding_date': '2019-10-15'
            },
            {
                'client_id': 'MERIDIAN_FUND_052',
                'name': 'Meridian Opportunity Fund',
                'rm': 'Sarah Chen',
                'sector': 'Hedge Fund',
                'region': 'Asia',
                'tier': 'Tier 2',
                'onboarding_date': '2020-02-28'
            },
            {
                'client_id': 'SENTINEL_ASSETS_067',
                'name': 'Sentinel Asset Management',
                'rm': 'Michael Torres',
                'sector': 'Asset Management',
                'region': 'North America',
                'tier': 'Tier 2',
                'onboarding_date': '2021-07-05'
            },
            {
                'client_id': 'VANGUARD_MARKETS_078',
                'name': 'Vanguard Markets Ltd',
                'rm': 'Emma Richardson',
                'sector': 'Market Maker',
                'region': 'Europe',
                'tier': 'Tier 2',
                'onboarding_date': '2020-09-12'
            },
            {
                'client_id': 'ROCKFORD_TRUST_088',
                'name': 'Rockford Trust Company',
                'rm': 'James Wong',
                'sector': 'Trust Services',
                'region': 'Asia',
                'tier': 'Tier 2',
                'onboarding_date': '2019-04-18'
            },
            {
                'client_id': 'ECLIPSE_PARTNERS_092',
                'name': 'Eclipse Trading Partners',
                'rm': 'Sarah Chen',
                'sector': 'Prop Trading',
                'region': 'Europe',
                'tier': 'Tier 2',
                'onboarding_date': '2021-05-25'
            }
        ]
        
        df = pd.DataFrame(clients)
        df.to_csv(self.data_dir / "clients.csv", index=False)
        logger.info(f"Generated {len(df)} mock clients")
        return df
    
    def list_clients(
        self,
        search: Optional[str] = None,
        segment: Optional[str] = None,
        rm: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List clients with optional filters.
        
        Returns clients enriched with latest switch probability from cache.
        """
        try:
            df = self.clients_df.copy()
            
            # Apply filters
            if search:
                mask = (
                    df['name'].str.contains(search, case=False, na=False) |
                    df['client_id'].str.contains(search, case=False, na=False)
                )
                df = df[mask]
            
            if rm:
                df = df[df['rm'] == rm]
            
            # Get latest switch probabilities from database
            client_ids = df['client_id'].tolist()
            switch_probs = self._get_latest_switch_probs(client_ids)
            
            # Enrich clients with switch probability data
            clients = []
            for _, row in df.iterrows():
                client = row.to_dict()
                client_id = client['client_id']
                
                # Add cached switch probability data
                if client_id in switch_probs:
                    client['switch_prob'] = switch_probs[client_id]['switch_prob']
                    client['segment'] = switch_probs[client_id]['segment']
                    client['last_analyzed'] = switch_probs[client_id]['computed_at']
                else:
                    client['switch_prob'] = None
                    client['segment'] = None
                    client['last_analyzed'] = None
                
                clients.append(client)
            
            # Apply segment filter after enrichment
            if segment:
                clients = [c for c in clients if c.get('segment') == segment]
            
            # Sort by switch_prob descending (nulls last)
            clients.sort(
                key=lambda x: (x['switch_prob'] is None, -(x['switch_prob'] or 0))
            )
            
            return {"clients": clients}
            
        except Exception as e:
            logger.error(f"Error listing clients: {e}")
            raise
    
    def get_client_metadata(self, client_id: str) -> Dict[str, Any]:
        """Get metadata for specific client with cached switch probability"""
        try:
            client_row = self.clients_df[
                self.clients_df['client_id'] == client_id
            ]
            
            if client_row.empty:
                return {"error": f"Client {client_id} not found"}
            
            client = client_row.iloc[0].to_dict()
            
            # Enrich with cached switch probability
            switch_probs = self._get_latest_switch_probs([client_id])
            if client_id in switch_probs:
                client['switch_prob'] = switch_probs[client_id]['switch_prob']
                client['segment'] = switch_probs[client_id]['segment']
                client['last_analyzed'] = switch_probs[client_id]['computed_at']
            else:
                client['switch_prob'] = None
                client['segment'] = None
                client['last_analyzed'] = None
            
            return {"client": client}
            
        except Exception as e:
            logger.error(f"Error fetching client metadata: {e}")
            raise
    
    def log_action(
        self,
        client_id: str,
        action_type: str,
        title: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log an action (stored in database via api-facade)"""
        return {
            "action_id": f"ACT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{client_id}",
            "status": "logged",
            "timestamp": datetime.utcnow().isoformat()
        }

# Create FastAPI app
app = FastAPI(title="Client MCP Server")

# Initialize server
server = MockClientMCPServer()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "client-mcp"}

@app.get("/tools")
async def list_tools():
    """List available tools"""
    return {
        "tools": [
            {
                "name": "list_clients",
                "description": "List clients with optional filters, enriched with cached switch probability",
                "parameters": {
                    "search": "Optional search term",
                    "segment": "Optional segment filter",
                    "rm": "Optional relationship manager filter"
                }
            },
            {
                "name": "get_client_metadata",
                "description": "Get metadata for specific client with cached switch probability",
                "parameters": {
                    "client_id": "Client identifier"
                }
            },
            {
                "name": "log_action",
                "description": "Log a relationship manager action",
                "parameters": {
                    "client_id": "Client identifier",
                    "action_type": "Type of action",
                    "title": "Action title",
                    "description": "Optional description"
                }
            }
        ]
    }

@app.post("/call_tool")
async def call_tool(request: ToolRequest):
    """Execute a tool"""
    try:
        if request.tool_name == "list_clients":
            result = server.list_clients(**request.arguments)
        elif request.tool_name == "get_client_metadata":
            result = server.get_client_metadata(**request.arguments)
        elif request.tool_name == "log_action":
            result = server.log_action(**request.arguments)
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Tool {request.tool_name} not found"
            )
        
        return ToolResponse(result=result)
        
    except Exception as e:
        logger.error(f"Error executing tool {request.tool_name}: {e}")
        return ToolResponse(
            result={},
            error=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3005))
    uvicorn.run(app, host="0.0.0.0", port=port)
