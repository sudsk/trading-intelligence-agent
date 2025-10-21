"""
NBA (Next Best Action) Agent - Generates recommendations
"""
from typing import Dict, List, Any

class NBAAgent:
    def __init__(self):
        self.playbooks = self._load_playbooks()
    
    def recommend(
        self,
        client_id: str,
        segment: str,
        switch_prob: float,
        risk_flags: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate next best action recommendations
        """
        recommendations = []
        
        # High switch probability -> proactive outreach
        if switch_prob > 0.5:
            recommendations.append({
                'action': 'PROACTIVE_OUTREACH',
                'priority': 'HIGH',
                'message': f"Client showing {switch_prob:.0%} switch probability",
                'products': self._get_products_for_segment(segment, risk_flags)
            })
        
        # Risk flags -> hedging products
        if risk_flags:
            recommendations.append({
                'action': 'PROPOSE_HEDGE',
                'priority': 'MEDIUM',
                'message': f"Address {', '.join(risk_flags)}",
                'products': self._get_hedge_products(risk_flags)
            })
        
        return recommendations
    
    def _load_playbooks(self) -> Dict:
        """Load NBA playbooks"""
        return {
            'Trend Follower': {
                'high_switch': ['Forward strips', 'Options collars'],
                'risk_off': ['Hedging overlays', 'Structured products']
            },
            'Mean Reverter': {
                'high_switch': ['Range-bound strategies', 'Volatility products'],
                'risk_off': ['Delta-neutral trades']
            },
            'Hedger': {
                'high_switch': ['Dynamic hedging', 'Basis swaps'],
                'risk_off': ['Static hedges']
            },
            'Trend Setter': {
                'high_switch': ['Momentum products', 'Systematic strategies'],
                'risk_off': ['Alpha products']
            }
        }
    
    def _get_products_for_segment(self, segment: str, risk_flags: List[str]) -> List[str]:
        """Get relevant products for segment"""
        if risk_flags:
            return self.playbooks.get(segment, {}).get('risk_off', [])
        return self.playbooks.get(segment, {}).get('high_switch', [])
    
    def _get_hedge_products(self, risk_flags: List[str]) -> List[str]:
        """Get hedging products for risk flags"""
        products = []
        for flag in risk_flags:
            if 'EUR' in flag:
                products.append('EURUSD forward strip')
            if 'concentration' in flag:
                products.append('Diversification overlay')
            if 'leverage' in flag:
                products.append('Leverage reduction strategy')
        return products
