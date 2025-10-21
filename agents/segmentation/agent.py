"""
Segmentation Agent - Analyzes client trading behavior
"""
import pandas as pd
from typing import Dict, Any, List

class SegmentationAgent:
    def __init__(self, data_service):
        self.data_service = data_service
    
    def analyze(self, client_id: str) -> Dict[str, Any]:
        """
        Analyze client and determine segment
        """
        # Fetch data
        trades = self.data_service.get_trades(client_id)
        positions = self.data_service.get_positions(client_id)
        
        # Compute features
        features = self._compute_features(trades, positions)
        
        # Determine segment
        segment, confidence = self._classify_segment(features)
        
        # Identify drivers
        drivers = self._identify_drivers(features, segment)
        
        # Calculate switch probability
        switch_prob = self._estimate_switch_prob(features)
        
        # Flag risks
        risk_flags = self._flag_risks(positions, features)
        
        return {
            'clientId': client_id,
            'segment': segment,
            'confidence': confidence,
            'switchProb': switch_prob,
            'drivers': drivers,
            'riskFlags': risk_flags,
            'features': features
        }
    
    def _compute_features(self, trades: pd.DataFrame, positions: pd.DataFrame) -> Dict:
        """Compute trading features"""
        return {
            'momentum_beta_20d': self._compute_momentum_beta(trades, window=20),
            'holding_period_avg': self._compute_avg_holding_period(trades),
            'lead_lag_alpha': self._compute_lead_lag_alpha(trades),
            'turnover': self._compute_turnover(trades),
            'aggressiveness': self._compute_aggressiveness(trades),
            'exposure_concentration': self._compute_concentration(positions)
        }
    
    def _classify_segment(self, features: Dict) -> tuple:
        """Classify client into segment"""
        # Simple rule-based classification (replace with ML model)
        momentum = features.get('momentum_beta_20d', 0)
        holding = features.get('holding_period_avg', 0)
        
        if momentum > 0.7 and holding < 5:
            return 'Trend Follower', 0.85
        elif abs(momentum) < 0.3:
            return 'Mean Reverter', 0.80
        elif holding > 20:
            return 'Hedger', 0.75
        else:
            return 'Trend Setter', 0.70
    
    def _estimate_switch_prob(self, features: Dict) -> float:
        """Estimate probability of strategy switch"""
        # Simple heuristic (replace with HMM/change-point detection)
        volatility = features.get('feature_volatility', 0.1)
        return min(0.9, 0.3 + volatility * 2)
    
    def _identify_drivers(self, features: Dict, segment: str) -> List[str]:
        """Identify key drivers of segment classification"""
        drivers = []
        if features.get('momentum_beta_20d', 0) > 0.6:
            drivers.append("High 20-day momentum-beta")
        if features.get('holding_period_avg', 0) < 5:
            drivers.append("Shorter hold times")
        if features.get('lead_lag_alpha', 0) > 0:
            drivers.append("Positive lead-lag alpha")
        return drivers[:3]  # Top 3
    
    def _flag_risks(self, positions: pd.DataFrame, features: Dict) -> List[str]:
        """Flag risk concerns"""
        flags = []
        concentration = features.get('exposure_concentration', {})
        for instrument, pct in concentration.items():
            if pct > 0.6:
                flags.append(f"{instrument} concentration")
        return flags
    
    def _compute_momentum_beta(self, trades: pd.DataFrame, window: int) -> float:
        """Compute momentum beta"""
        # Placeholder - implement actual calculation
        return 0.75
    
    def _compute_avg_holding_period(self, trades: pd.DataFrame) -> float:
        """Compute average holding period in days"""
        # Placeholder
        return 3.5
    
    def _compute_lead_lag_alpha(self, trades: pd.DataFrame) -> float:
        """Compute lead-lag alpha"""
        # Placeholder
        return 0.05
    
    def _compute_turnover(self, trades: pd.DataFrame) -> float:
        """Compute portfolio turnover"""
        # Placeholder
        return 0.8
    
    def _compute_aggressiveness(self, trades: pd.DataFrame) -> float:
        """Compute trading aggressiveness (market orders, participation rate)"""
        # Placeholder
        return 0.6
    
    def _compute_concentration(self, positions: pd.DataFrame) -> Dict:
        """Compute exposure concentration by instrument"""
        if positions.empty:
            return {}
        total = positions['netPosition'].abs().sum()
        return {
            row['instrument']: abs(row['netPosition']) / total
            for _, row in positions.iterrows()
        }
