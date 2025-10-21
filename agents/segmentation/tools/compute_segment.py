"""
Tool: Compute client segment classification
"""

def compute_segment_tool(
    momentum_beta: float,
    holding_period: float,
    lead_lag_alpha: float,
    turnover: float
) -> dict:
    """
    Classify trading segment based on features
    
    Args:
        momentum_beta: 20-day momentum correlation
        holding_period: Average holding period in days
        lead_lag_alpha: Lead-lag alpha metric
        turnover: Portfolio turnover rate
    
    Returns:
        dict with segment and confidence
    """
    # Rule-based classification logic
    if momentum_beta > 0.7 and holding_period < 5:
        return {'segment': 'Trend Follower', 'confidence': 0.85}
    elif abs(momentum_beta) < 0.3 and holding_period < 10:
        return {'segment': 'Mean Reverter', 'confidence': 0.80}
    elif holding_period > 20:
        return {'segment': 'Hedger', 'confidence': 0.75}
    elif lead_lag_alpha > 0.1:
        return {'segment': 'Trend Setter', 'confidence': 0.78}
    else:
        return {'segment': 'Unclassified', 'confidence': 0.50}
