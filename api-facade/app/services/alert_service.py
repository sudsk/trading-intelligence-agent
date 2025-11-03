import asyncio
from typing import List, Dict, Any
from datetime import datetime
import random

class AlertService:
    def __init__(self):
        self.alert_queue = []
        self.demo_clients = ['ACME_FX_023', 'ZEUS_COMM_019', 'TITAN_EQ_008']
    
    async def get_pending_alerts(self) -> List[Dict[str, Any]]:
        """Get any pending alerts to send via SSE"""
        alerts = self.alert_queue.copy()
        self.alert_queue.clear()
        
        # In demo mode, occasionally generate random alerts
        if random.random() < 0.1:  # 10% chance
            demo_alert = self._generate_demo_alert()
            alerts.append(demo_alert)
        
        return alerts
    
    def add_alert(self, alert: Dict[str, Any]):
        """Add an alert to the queue"""
        self.alert_queue.append(alert)
    
    def _generate_demo_alert(self) -> Dict[str, Any]:
        """Generate a random demo alert"""
        client_id = random.choice(self.demo_clients)
        old_prob = round(random.uniform(0.4, 0.6), 2)
        new_prob = round(old_prob + random.uniform(0.05, 0.15), 2)
        
        return {
            'type': 'switch_probability_alert',
            'clientId': client_id,
            'oldSwitchProb': old_prob,
            'newSwitchProb': new_prob,
            'reason': 'media-driven',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def trigger_demo_alert(self, client_id: str):
        """Manually trigger an alert for demo purposes"""
        alert = {
            'type': 'switch_probability_alert',
            'clientId': client_id,
            'oldSwitchProb': 0.53,
            'newSwitchProb': 0.64,
            'reason': 'media-driven',
            'timestamp': datetime.utcnow().isoformat()
        }
        self.add_alert(alert)
        return alert
