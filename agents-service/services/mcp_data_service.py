"""
MCP Data Service - Unified data access via Model Context Protocol

Replaces direct database access with MCP server calls.
Agents call this service, which routes to appropriate MCP servers.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

# MCP SDK (pseudocode - adjust to actual MCP Python SDK)
from mcp import Client, ServerConnection
from mcp.types import Tool, ToolCall, ToolResult

logger = logging.getLogger(__name__)


class MCPDataService:
    """
    Unified data access layer using MCP servers.
    
    Replaces direct SQL queries with MCP tool calls to legacy systems.
    Agents don't need to know about Oracle, Sybase, Bloomberg, etc.
    """
    
    def __init__(self):
        """Initialize MCP client and connect to servers."""
        self.client = Client()
        
        # Connect to MCP servers
        self.servers = self._connect_to_servers()
        
        logger.info("✅ MCP Data Service initialized")
        logger.info(f"   Connected to {len(self.servers)} MCP servers")
    
    def _connect_to_servers(self) -> Dict[str, ServerConnection]:
        """
        Connect to all MCP servers.
        
        In production, these would be:
        - Trade server → Oracle OMS
        - Risk server → Sybase risk warehouse
        - Market server → Bloomberg API
        - News server → Reuters/Dow Jones
        - Client server → CRM system
        """
        servers = {}
        
        # Get server URLs from environment
        trade_server_url = os.getenv('MCP_TRADE_SERVER_URL', 'http://localhost:3001')
        risk_server_url = os.getenv('MCP_RISK_SERVER_URL', 'http://localhost:3002')
        market_server_url = os.getenv('MCP_MARKET_SERVER_URL', 'http://localhost:3003')
        news_server_url = os.getenv('MCP_NEWS_SERVER_URL', 'http://localhost:3004')
        client_server_url = os.getenv('MCP_CLIENT_SERVER_URL', 'http://localhost:3005')
        
        try:
            servers['trade'] = self.client.connect(trade_server_url)
            logger.info(f"   ✓ Connected to Trade MCP Server: {trade_server_url}")
        except Exception as e:
            logger.warning(f"   ⚠️ Trade MCP Server unavailable: {e}")
        
        try:
            servers['risk'] = self.client.connect(risk_server_url)
            logger.info(f"   ✓ Connected to Risk MCP Server: {risk_server_url}")
        except Exception as e:
            logger.warning(f"   ⚠️ Risk MCP Server unavailable: {e}")
        
        try:
            servers['market'] = self.client.connect(market_server_url)
            logger.info(f"   ✓ Connected to Market MCP Server: {market_server_url}")
        except Exception as e:
            logger.warning(f"   ⚠️ Market MCP Server unavailable: {e}")
        
        try:
            servers['news'] = self.client.connect(news_server_url)
            logger.info(f"   ✓ Connected to News MCP Server: {news_server_url}")
        except Exception as e:
            logger.warning(f"   ⚠️ News MCP Server unavailable: {e}")
        
        try:
            servers['client'] = self.client.connect(client_server_url)
            logger.info(f"   ✓ Connected to Client MCP Server: {client_server_url}")
        except Exception as e:
            logger.warning(f"   ⚠️ Client MCP Server unavailable: {e}")
        
        return servers
    
    # ========================================================================
    # TRADE DATA (from Oracle OMS via MCP)
    # ========================================================================
    
    def get_trades(
        self,
        client_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get client trades via Trade MCP Server.
        
        Behind the scenes:
        - MCP server queries Oracle OMS
        - Or queries Murex trading system
        - Returns standardized format
        
        Args:
            client_id: Client identifier
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            DataFrame with trades
        """
        if 'trade' not in self.servers:
            logger.warning("Trade MCP Server not available, returning empty")
            return pd.DataFrame()
        
        try:
            # Call MCP tool
            result = self.servers['trade'].call_tool(
                tool_name='get_client_trades',
                arguments={
                    'client_id': client_id,
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            )
            
            # Convert MCP result to DataFrame
            trades_data = result.get('trades', [])
            df = pd.DataFrame(trades_data)
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"✅ Fetched {len(df)} trades for {client_id} via MCP")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error fetching trades via MCP: {e}")
            return pd.DataFrame()
    
    def get_trade_summary(self, client_id: str, days: int = 90) -> Dict[str, Any]:
        """
        Get aggregated trade summary via MCP.
        
        This might be pre-computed by the MCP server for efficiency.
        """
        if 'trade' not in self.servers:
            return {'trade_count': 0, 'instruments': []}
        
        try:
            result = self.servers['trade'].call_tool(
                tool_name='get_trade_summary',
                arguments={
                    'client_id': client_id,
                    'days': days
                }
            )
            
            return result.get('summary', {})
            
        except Exception as e:
            logger.error(f"Error fetching trade summary via MCP: {e}")
            return {'trade_count': 0, 'instruments': []}
    
    # ========================================================================
    # POSITION DATA (from Sybase risk warehouse via MCP)
    # ========================================================================
    
    def get_positions(self, client_id: str) -> pd.DataFrame:
        """
        Get client positions via Risk MCP Server.
        
        Behind the scenes:
        - MCP server queries Sybase risk warehouse
        - Or queries collateral management system
        """
        if 'risk' not in self.servers:
            logger.warning("Risk MCP Server not available")
            return pd.DataFrame()
        
        try:
            result = self.servers['risk'].call_tool(
                tool_name='get_client_positions',
                arguments={'client_id': client_id}
            )
            
            positions_data = result.get('positions', [])
            df = pd.DataFrame(positions_data)
            
            logger.info(f"✅ Fetched {len(df)} positions for {client_id} via MCP")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching positions via MCP: {e}")
            return pd.DataFrame()
    
    def get_client_features(self, client_id: str) -> Optional[Dict]:
        """
        Get pre-computed features via Risk MCP Server.
        
        Features might be computed nightly by risk systems:
        - Momentum-beta
        - VAR
        - Leverage
        - etc.
        """
        if 'risk' not in self.servers:
            return None
        
        try:
            result = self.servers['risk'].call_tool(
                tool_name='get_client_risk_metrics',
                arguments={'client_id': client_id}
            )
            
            return result.get('metrics', {})
            
        except Exception as e:
            logger.error(f"Error fetching features via MCP: {e}")
            return None
    
    # ========================================================================
    # MARKET DATA (from Bloomberg via MCP)
    # ========================================================================
    
    def get_market_bars(
        self,
        instruments: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Get market OHLCV data via Market MCP Server.
        
        Behind the scenes:
        - MCP server queries Bloomberg API
        - Or queries Reuters/ICE data feeds
        """
        if 'market' not in self.servers:
            logger.warning("Market MCP Server not available")
            return pd.DataFrame()
        
        try:
            result = self.servers['market'].call_tool(
                tool_name='get_market_bars',
                arguments={
                    'instruments': instruments,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            )
            
            bars_data = result.get('bars', [])
            df = pd.DataFrame(bars_data)
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"✅ Fetched market bars for {len(instruments)} instruments via MCP")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market bars via MCP: {e}")
            return pd.DataFrame()
    
    # ========================================================================
    # NEWS/MEDIA DATA (from Reuters/Dow Jones via MCP)
    # ========================================================================
    
    def get_headlines(
        self,
        instruments: List[str],
        start_time: Optional[datetime] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get financial headlines via News MCP Server.
        
        Behind the scenes:
        - MCP server queries Reuters News API
        - Or queries Dow Jones Newswires
        - Or internal research feeds
        """
        if 'news' not in self.servers:
            logger.warning("News MCP Server not available")
            return pd.DataFrame()
        
        try:
            result = self.servers['news'].call_tool(
                tool_name='get_financial_headlines',
                arguments={
                    'instruments': instruments,
                    'start_time': start_time.isoformat() if start_time else None,
                    'limit': limit
                }
            )
            
            headlines_data = result.get('headlines', [])
            df = pd.DataFrame(headlines_data)
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"✅ Fetched {len(df)} headlines via MCP")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching headlines via MCP: {e}")
            return pd.DataFrame()
    
    # ========================================================================
    # CLIENT DATA (from CRM/Master via MCP)
    # ========================================================================
    
    def get_client_metadata(self, client_id: str) -> Optional[Dict]:
        """
        Get client metadata via Client MCP Server.
        
        Behind the scenes:
        - MCP server queries Salesforce/CRM
        - Or queries client master database (DB2/Oracle)
        """
        if 'client' not in self.servers:
            logger.warning("Client MCP Server not available")
            return None
        
        try:
            result = self.servers['client'].call_tool(
                tool_name='get_client_metadata',
                arguments={'client_id': client_id}
            )
            
            return result.get('metadata', {})
            
        except Exception as e:
            logger.error(f"Error fetching client metadata via MCP: {e}")
            return None
    
    def get_clients_list(
        self,
        search: Optional[str] = None,
        segment: Optional[str] = None,
        rm: Optional[str] = None,
        limit: int = 50
    ) -> pd.DataFrame:
        """
        Get list of clients via Client MCP Server.
        """
        if 'client' not in self.servers:
            return pd.DataFrame()
        
        try:
            result = self.servers['client'].call_tool(
                tool_name='list_clients',
                arguments={
                    'search': search,
                    'segment': segment,
                    'rm': rm,
                    'limit': limit
                }
            )
            
            clients_data = result.get('clients', [])
            df = pd.DataFrame(clients_data)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching clients list via MCP: {e}")
            return pd.DataFrame()
    
    # ========================================================================
    # TIMELINE & HISTORY (from internal systems via MCP)
    # ========================================================================
    
    def get_client_timeline(self, client_id: str, months: int = 6) -> List[Dict]:
        """Get historical regime timeline."""
        if 'client' not in self.servers:
            return []
        
        try:
            result = self.servers['client'].call_tool(
                tool_name='get_client_timeline',
                arguments={
                    'client_id': client_id,
                    'months': months
                }
            )
            
            return result.get('timeline', [])
            
        except Exception as e:
            logger.error(f"Error fetching timeline via MCP: {e}")
            return []
    
    def get_client_alerts(
        self,
        client_id: str,
        limit: int = 20,
        acknowledged: Optional[bool] = None
    ) -> List[Dict]:
        """Get recent alerts for client."""
        if 'client' not in self.servers:
            return []
        
        try:
            result = self.servers['client'].call_tool(
                tool_name='get_client_alerts',
                arguments={
                    'client_id': client_id,
                    'limit': limit,
                    'acknowledged': acknowledged
                }
            )
            
            return result.get('alerts', [])
            
        except Exception as e:
            logger.error(f"Error fetching alerts via MCP: {e}")
            return []
    
    # ========================================================================
    # WRITE OPERATIONS (actions, logs)
    # ========================================================================
    
    def log_action(
        self,
        client_id: str,
        action_type: str,
        title: str,
        description: Optional[str] = None,
        products: Optional[List[str]] = None,
        rm: Optional[str] = None
    ) -> str:
        """
        Log an action via Client MCP Server.
        
        This writes to CRM or action tracking system.
        """
        if 'client' not in self.servers:
            logger.warning("Cannot log action - Client MCP Server unavailable")
            return None
        
        try:
            result = self.servers['client'].call_tool(
                tool_name='log_action',
                arguments={
                    'client_id': client_id,
                    'action_type': action_type,
                    'title': title,
                    'description': description,
                    'products': products,
                    'rm': rm
                }
            )
            
            action_id = result.get('action_id')
            logger.info(f"✅ Action logged via MCP: {action_id}")
            return action_id
            
        except Exception as e:
            logger.error(f"Error logging action via MCP: {e}")
            return None
    
    def insert_switch_probability(
        self,
        client_id: str,
        switch_prob: float,
        confidence: float,
        segment: str,
        drivers: List[str],
        risk_flags: List[str]
    ):
        """
        Insert switch probability record via Client MCP Server.
        """
        if 'client' not in self.servers:
            return
        
        try:
            self.servers['client'].call_tool(
                tool_name='insert_switch_probability',
                arguments={
                    'client_id': client_id,
                    'switch_prob': switch_prob,
                    'confidence': confidence,
                    'segment': segment,
                    'drivers': drivers,
                    'risk_flags': risk_flags,
                    'computed_at': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"✅ Switch prob inserted via MCP for {client_id}")
            
        except Exception as e:
            logger.error(f"Error inserting switch prob via MCP: {e}")


# ============================================================================
# Factory Function (for backward compatibility)
# ============================================================================

def get_data_service() -> MCPDataService:
    """
    Get data service instance.
    
    Returns MCP-based service in production, can return direct SQL service
    for local dev/testing.
    """
    use_mcp = os.getenv('USE_MCP', 'true').lower() == 'true'
    
    if use_mcp:
        logger.info("Using MCP Data Service")
        return MCPDataService()
    else:
        logger.info("Using Direct SQL Data Service (dev mode)")
        from services.data_service import DataService
        return DataService()