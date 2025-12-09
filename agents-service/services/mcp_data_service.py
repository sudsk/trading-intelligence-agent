"""
MCP Data Service - Unified data access via Model Context Protocol

Replaces direct database access with MCP server calls.
Agents call this service, which routes to appropriate MCP servers via HTTP.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import httpx

logger = logging.getLogger(__name__)


class MCPDataService:
    """
    Unified data access layer using MCP servers via HTTP.
    
    Replaces direct SQL queries with HTTP calls to MCP servers.
    Agents don't need to know about Oracle, Sybase, Bloomberg, etc.
    """
    
    def __init__(self):
        """Initialize HTTP client for MCP servers."""
        self.http_client = httpx.Client(timeout=30.0)
        
        # Get server URLs from environment
        self.trade_server_url = os.getenv('MCP_TRADE_SERVER_URL', 'http://localhost:3001')
        self.risk_server_url = os.getenv('MCP_RISK_SERVER_URL', 'http://localhost:3002')
        self.market_server_url = os.getenv('MCP_MARKET_SERVER_URL', 'http://localhost:3003')
        self.news_server_url = os.getenv('MCP_NEWS_SERVER_URL', 'http://localhost:3004')
        self.client_server_url = os.getenv('MCP_CLIENT_SERVER_URL', 'http://localhost:3005')
        
        # Test connectivity
        self._test_connectivity()
        
        logger.info("✅ MCP Data Service initialized with HTTP client")
    
    def _test_connectivity(self):
        """Test connectivity to MCP servers."""
        servers = {
            'Trade': self.trade_server_url,
            'Risk': self.risk_server_url,
            'Market': self.market_server_url,
            'News': self.news_server_url,
            'Client': self.client_server_url
        }
        
        for name, url in servers.items():
            try:
                response = self.http_client.get(f"{url}/health", timeout=5.0)
                if response.status_code == 200:
                    logger.info(f"   ✓ Connected to {name} MCP Server: {url}")
                else:
                    logger.warning(f"   ⚠️ {name} MCP Server responded with {response.status_code}")
            except Exception as e:
                logger.warning(f"   ⚠️ {name} MCP Server unavailable: {e}")
    
    def _call_tool(self, server_url: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on an MCP server via HTTP.
        
        Args:
            server_url: MCP server base URL
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result as dictionary
        """
        try:
            response = self.http_client.post(
                f"{server_url}/call_tool",
                json={
                    "tool_name": tool_name,
                    "arguments": arguments
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('result', {})
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling {tool_name}: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error calling {tool_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling {tool_name}: {e}")
            raise
    
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
        Get client trades via Trade MCP Server (HTTP).
        
        Behind the scenes:
        - HTTP POST to Trade MCP Server
        - MCP server queries Oracle OMS or CSV (demo)
        - Returns standardized format
        
        Args:
            client_id: Client identifier
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            DataFrame with trades
        """
        try:
            result = self._call_tool(
                server_url=self.trade_server_url,
                tool_name='get_client_trades',
                arguments={
                    'client_id': client_id,
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            )
            
            # Convert to DataFrame
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
        Get aggregated trade summary via MCP (HTTP).
        
        This might be pre-computed by the MCP server for efficiency.
        """
        try:
            result = self._call_tool(
                server_url=self.trade_server_url,
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
    
    def get_position_flips(self, client_id: str, days: int = 90) -> Dict[str, Any]:
        """Get position flip statistics via MCP (HTTP)."""
        try:
            result = self._call_tool(
                server_url=self.trade_server_url,
                tool_name='get_position_flips',
                arguments={
                    'client_id': client_id,
                    'days': days
                }
            )
            
            return result.get('flips', {})
            
        except Exception as e:
            logger.error(f"Error fetching position flips via MCP: {e}")
            return {'flip_count': 0, 'flip_rate': 0.0}
    
    # ========================================================================
    # POSITION DATA (from Sybase risk warehouse via MCP)
    # ========================================================================
    
    def get_positions(self, client_id: str) -> pd.DataFrame:
        """
        Get client positions via Risk MCP Server (HTTP).
        
        Behind the scenes:
        - HTTP POST to Risk MCP Server
        - MCP server queries Sybase risk warehouse or CSV (demo)
        """
        try:
            result = self._call_tool(
                server_url=self.risk_server_url,
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
    
    def get_risk_metrics(self, client_id: str) -> Dict[str, Any]:
        """Get risk metrics via Risk MCP Server (HTTP)."""
        try:
            result = self._call_tool(
                server_url=self.risk_server_url,
                tool_name='get_risk_metrics',
                arguments={'client_id': client_id}
            )
            
            return result.get('risk_metrics', {})
            
        except Exception as e:
            logger.error(f"Error fetching risk metrics via MCP: {e}")
            return {}
    
    def get_client_features(self, client_id: str, days: int = 90) -> Dict[str, Any]:
        """Get trading features via Risk MCP Server (HTTP)."""
        try:
            result = self._call_tool(
                server_url=self.risk_server_url,
                tool_name='get_client_features',
                arguments={
                    'client_id': client_id,
                    'days': days
                }
            )
            
            return result.get('features', {})
            
        except Exception as e:
            logger.error(f"Error fetching features via MCP: {e}")
            return {}
    
    # ========================================================================
    # MARKET DATA (from Bloomberg API via MCP)
    # ========================================================================
    
    def get_market_bars(
        self,
        instruments: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get market bars via Market MCP Server (HTTP).
        
        Behind the scenes:
        - HTTP POST to Market MCP Server
        - MCP server queries Bloomberg API or CSV (demo)
        """
        try:
            result = self._call_tool(
                server_url=self.market_server_url,
                tool_name='get_market_bars',
                arguments={
                    'instruments': instruments,
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            )
            
            bars_data = result.get('bars', [])
            df = pd.DataFrame(bars_data)
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"✅ Fetched {len(df)} market bars via MCP")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market bars via MCP: {e}")
            return pd.DataFrame()
    
    def get_current_prices(self, instruments: List[str]) -> Dict[str, float]:
        """Get current prices via Market MCP Server (HTTP)."""
        try:
            result = self._call_tool(
                server_url=self.market_server_url,
                tool_name='get_current_prices',
                arguments={'instruments': instruments}
            )
            
            return result.get('prices', {})
            
        except Exception as e:
            logger.error(f"Error fetching current prices via MCP: {e}")
            return {}
    
    def get_correlations(self, instruments: List[str], days: int = 30) -> Dict[str, Any]:
        """Get instrument correlations via Market MCP Server (HTTP)."""
        try:
            result = self._call_tool(
                server_url=self.market_server_url,
                tool_name='get_correlations',
                arguments={
                    'instruments': instruments,
                    'days': days
                }
            )
            
            return result.get('correlations', {})
            
        except Exception as e:
            logger.error(f"Error fetching correlations via MCP: {e}")
            return {}
    
    # ========================================================================
    # NEWS DATA (from Reuters/Dow Jones via MCP)
    # ========================================================================
    
    def get_headlines(
        self,
        instruments: List[str],
        hours: int = 72
    ) -> pd.DataFrame:
        """
        Get headlines via News MCP Server (HTTP).
        
        Behind the scenes:
        - HTTP POST to News MCP Server
        - MCP server queries Reuters API or CSV (demo)
        """
        try:
            result = self._call_tool(
                server_url=self.news_server_url,
                tool_name='get_headlines',
                arguments={
                    'instruments': instruments,
                    'hours': hours
                }
            )
            
            headlines_data = result.get('headlines', [])
            df = pd.DataFrame(headlines_data)
            
            if not df.empty:
                df['published_at'] = pd.to_datetime(df['published_at'])
            
            logger.info(f"✅ Fetched {len(df)} headlines via MCP")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching headlines via MCP: {e}")
            return pd.DataFrame()
    
    def get_sentiment(self, headline_ids: List[int]) -> Dict[int, float]:
        """Get headline sentiments via News MCP Server (HTTP)."""
        try:
            result = self._call_tool(
                server_url=self.news_server_url,
                tool_name='get_sentiment',
                arguments={'headline_ids': headline_ids}
            )
            
            return result.get('sentiments', {})
            
        except Exception as e:
            logger.error(f"Error fetching sentiments via MCP: {e}")
            return {}
    
    def get_macro_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get macro economic events via News MCP Server (HTTP)."""
        try:
            result = self._call_tool(
                server_url=self.news_server_url,
                tool_name='get_macro_events',
                arguments={'days': days}
            )
            
            return result.get('events', [])
            
        except Exception as e:
            logger.error(f"Error fetching macro events via MCP: {e}")
            return []
    
    # ========================================================================
    # CLIENT METADATA (from CRM/Salesforce via MCP)
    # ========================================================================
    
    def get_client_metadata(self, client_id: str) -> Dict[str, Any]:
        """
        Get client metadata via Client MCP Server (HTTP).
        
        Behind the scenes:
        - HTTP POST to Client MCP Server
        - MCP server queries Salesforce or CSV (demo)
        """
        try:
            result = self._call_tool(
                server_url=self.client_server_url,
                tool_name='get_client_metadata',
                arguments={'client_id': client_id}
            )
            
            return result.get('client', {})
            
        except Exception as e:
            logger.error(f"Error fetching client metadata via MCP: {e}")
            return {}
    
    def list_clients(
        self,
        search: Optional[str] = None,
        segment: Optional[str] = None,
        rm: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List clients via Client MCP Server (HTTP)."""
        try:
            result = self._call_tool(
                server_url=self.client_server_url,
                tool_name='list_clients',
                arguments={
                    'search': search,
                    'segment': segment,
                    'rm': rm
                }
            )
            
            return result.get('clients', [])
            
        except Exception as e:
            logger.error(f"Error listing clients via MCP: {e}")
            return []
    
    def log_action(
        self,
        client_id: str,
        action_type: str,
        title: str,
        description: Optional[str] = None
    ) -> str:
        """Log action via Client MCP Server (HTTP)."""
        try:
            result = self._call_tool(
                server_url=self.client_server_url,
                tool_name='log_action',
                arguments={
                    'client_id': client_id,
                    'action_type': action_type,
                    'title': title,
                    'description': description
                }
            )
            
            return result.get('action_id', '')
            
        except Exception as e:
            logger.error(f"Error logging action via MCP: {e}")
            return ''
    
    def __del__(self):
        """Clean up HTTP client on deletion."""
        try:
            self.http_client.close()
        except:
            pass
