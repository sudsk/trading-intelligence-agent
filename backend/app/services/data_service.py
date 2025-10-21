import pandas as pd
from pathlib import Path
from app.config import settings
from typing import List, Optional

class DataService:
    def __init__(self):
        self.data_path = Path(settings.DATA_PATH)
        self._load_data()
    
    def _load_data(self):
        """Load mock data from CSV files"""
        self.clients_df = pd.read_csv(self.data_path / "clients.csv")
        self.trades_df = pd.read_csv(self.data_path / "trades.csv")
        self.positions_df = pd.read_csv(self.data_path / "positions.csv")
        self.headlines_df = pd.read_csv(self.data_path / "headlines.csv")
    
    def get_clients(self, search: Optional[str] = None, segment: Optional[str] = None, rm: Optional[str] = None):
        """Get filtered client list"""
        df = self.clients_df.copy()
        
        if search:
            df = df[df['clientId'].str.contains(search, case=False)]
        if segment:
            df = df[df['segment'] == segment]
        if rm:
            df = df[df['rm'] == rm]
        
        # Sort by switch probability descending
        df = df.sort_values('switchProb', ascending=False)
        
        return df.to_dict('records')
    
    def get_timeline(self, client_id: str):
        """Get client timeline"""
        # Mock timeline data
        return [
            {
                "period": "October 2025 - Present",
                "segment": "Trend Follower",
                "description": "Increasing switch risk"
            },
            {
                "period": "July 2025 - October 2025",
                "segment": "Trend Follower",
                "description": "Post-payrolls flip"
            }
        ]
    
    def get_insights(self, client_id: str):
        """Get insights feed"""
        return [
            {
                "type": "SIGNAL",
                "severity": "HIGH",
                "timestamp": "2025-10-20T10:42:00Z",
                "message": "Switch probability crossed 0.50 threshold"
            }
        ]
    
    def save_action(self, action):
        """Save action to data store"""
        # In demo mode, just log it
        print(f"Action saved: {action}")
        return action
    
    def get_action(self, action_id: str):
        """Get action by ID"""
        # Mock implementation
        return None
