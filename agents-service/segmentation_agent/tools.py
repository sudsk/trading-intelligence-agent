"""
Segmentation Agent Tools

Functions that Gemini can call to gather data for analysis.
These are registered with the Gemini model as callable tools.
"""
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging
from .switch_probability import compute_switch_probability

logger = logging.getLogger(__name__)


def fetch_trades_summary(client_id: str, data_service) -> Dict[str, Any]:
    """
    Fetch aggregated trade statistics for the client.
    NOW INCLUDES: HMM/change-point switch probability calculation.
    """
    try:
        # ... existing code to fetch trades ...
        
        # Compute aggregated statistics (existing code)
        summary = {
            "trade_count": len(trades),
            "instruments": list(trades['instrument'].unique()),
            "avg_holding_days": _compute_avg_holding_period(trades),
            "position_flips": _count_position_flips(trades),
            "market_order_ratio": _compute_market_order_ratio(trades),
            "recent_trade_pattern": _describe_recent_pattern(trades),
            "trade_frequency_per_day": len(trades) / 90.0,
            "unique_instruments": len(trades['instrument'].unique())
        }
        
        # ========================================
        # NEW: Compute switch probability using HMM/change-point
        # ========================================
        logger.info(f"Computing HMM switch probability for {client_id}")
        switch_result = compute_switch_probability(
            client_id=client_id,
            data_service=data_service,
            lookback_days=90
        )
        
        # Add to summary
        summary['switch_prob'] = switch_result['switch_prob']
        summary['switch_reasoning'] = switch_result['reasoning']
        summary['switch_components'] = {
            'pattern_instability': switch_result['pattern_instability'],
            'change_point': switch_result['change_point'],
            'momentum_shift': switch_result['momentum_shift'],
            'flip_acceleration': switch_result['flip_acceleration'],
            'feature_drift': switch_result['feature_drift']
        }
        
        logger.info(
            f"HMM switch prob for {client_id}: {switch_result['switch_prob']:.2f} "
            f"(pattern={switch_result['pattern_instability']:.2f}, "
            f"cp={switch_result['change_point']:.2f})"
        )
        # ========================================
        
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching trade summary for {client_id}: {e}")
        return {
            "error": str(e),
            "trade_count": 0,
            # ... rest of error handling ...
            "switch_prob": 0.30,  # Baseline on error
            "switch_reasoning": "Error computing switch probability",
            "switch_components": {}
        }

def fetch_position_snapshot(client_id: str, data_service) -> Dict[str, float]:
    """
    Fetch current position concentrations.
    
    Returns the percentage concentration of each instrument
    in the client's current portfolio.
    
    Args:
        client_id: Client identifier
        data_service: Data service instance
        
    Returns:
        Dictionary mapping instrument to concentration percentage
    """
    try:
        positions = data_service.get_positions(client_id=client_id)
        
        if positions.empty:
            logger.warning(f"No positions found for {client_id}")
            return {}
        
        # Calculate concentrations
        total_exposure = positions['netPosition'].abs().sum()
        
        if total_exposure == 0:
            return {}
        
        concentrations = {}
        for _, row in positions.iterrows():
            instrument = row['instrument']
            concentration = abs(row['netPosition']) / total_exposure
            
            # Only include significant concentrations (>5%)
            if concentration > 0.05:
                concentrations[instrument] = round(concentration, 3)
        
        logger.info(f"Position snapshot for {client_id}: {len(concentrations)} instruments")
        return concentrations
        
    except Exception as e:
        logger.error(f"Error fetching positions for {client_id}: {e}")
        return {"error": str(e)}


# ============================================================================
# Helper Functions (not exposed as tools)
# ============================================================================

def _compute_avg_holding_period(trades: pd.DataFrame) -> float:
    """
    Compute average holding period by tracking position lifecycle.
    
    Method: Track when positions are opened/closed by instrument
    """
    if len(trades) < 2:
        return 0.0
    
    try:
        holding_periods = []
        
        # Group by instrument
        for instrument in trades['instrument'].unique():
            inst_trades = trades[trades['instrument'] == instrument].copy()
            inst_trades = inst_trades.sort_values('timestamp')
            
            # Calculate cumulative position
            inst_trades['quantity_signed'] = inst_trades.apply(
                lambda x: x['quantity'] if x['side'] == 'BUY' else -x['quantity'],
                axis=1
            )
            inst_trades['cumulative_position'] = inst_trades['quantity_signed'].cumsum()
            inst_trades['position_sign'] = inst_trades['cumulative_position'].apply(
                lambda x: 1 if x > 0 else (-1 if x < 0 else 0)
            )
            
            # Find sign changes (position flips)
            sign_changes = inst_trades[
                inst_trades['position_sign'] != inst_trades['position_sign'].shift()
            ].copy()
            
            if len(sign_changes) > 1:
                # Time between flips is holding period
                sign_changes['timestamp'] = pd.to_datetime(sign_changes['timestamp'])
                time_diffs = sign_changes['timestamp'].diff().dt.total_seconds() / 86400  # days
                holding_periods.extend(time_diffs.dropna().tolist())
        
        if holding_periods:
            return round(sum(holding_periods) / len(holding_periods), 1)
        
        # Fallback: estimate from time range
        time_range_days = (trades['timestamp'].max() - trades['timestamp'].min()).days
        if time_range_days > 0:
            return round(time_range_days / len(trades), 1)
        
        return 0.0
        
    except Exception as e:
        logger.warning(f"Error computing holding period: {e}")
        return 0.0


def _count_position_flips(trades: pd.DataFrame) -> int:
    """
    Count position direction reversals (long→short or short→long).
    
    Returns flips per 30 days.
    """
    if len(trades) < 2:
        return 0
    
    try:
        total_flips = 0
        
        for instrument in trades['instrument'].unique():
            inst_trades = trades[trades['instrument'] == instrument].copy()
            inst_trades = inst_trades.sort_values('timestamp')
            
            # Calculate cumulative position
            inst_trades['quantity_signed'] = inst_trades.apply(
                lambda x: x['quantity'] if x['side'] == 'BUY' else -x['quantity'],
                axis=1
            )
            inst_trades['cumulative_position'] = inst_trades['quantity_signed'].cumsum()
            inst_trades['position_sign'] = inst_trades['cumulative_position'].apply(
                lambda x: 1 if x > 0 else (-1 if x < 0 else 0)
            )
            
            # Count sign changes
            sign_changes = (inst_trades['position_sign'] != inst_trades['position_sign'].shift()).sum()
            total_flips += max(0, sign_changes - 1)  # Subtract initial position
        
        # Normalize to 30 days
        time_range_days = (trades['timestamp'].max() - trades['timestamp'].min()).days
        if time_range_days > 0:
            flips_per_30d = int(total_flips * 30 / time_range_days)
            return flips_per_30d
        
        return total_flips
        
    except Exception as e:
        logger.warning(f"Error counting flips: {e}")
        return 0


def _compute_market_order_ratio(trades: pd.DataFrame) -> float:
    """
    Calculate percentage of market orders vs limit orders.
    
    Market orders indicate aggressiveness/urgency.
    """
    if 'orderType' not in trades.columns or len(trades) == 0:
        return 0.5  # Unknown, assume 50%
    
    try:
        market_orders = len(trades[trades['orderType'] == 'MARKET'])
        total_orders = len(trades)
        
        return round(market_orders / total_orders, 3) if total_orders > 0 else 0.5
        
    except Exception as e:
        logger.warning(f"Error computing market order ratio: {e}")
        return 0.5


def _describe_recent_pattern(trades: pd.DataFrame) -> str:
    """
    Describe the recent trading pattern in natural language.
    
    Compares last 14 days to previous period.
    """
    if len(trades) < 10:
        return "Insufficient data"
    
    try:
        trades = trades.copy()
        trades['timestamp'] = pd.to_datetime(trades['timestamp'])
        
        # Split into recent (14d) and earlier
        cutoff = datetime.now() - timedelta(days=14)
        recent = trades[trades['timestamp'] > cutoff]
        earlier = trades[trades['timestamp'] <= cutoff]
        
        if len(recent) < 5 or len(earlier) < 5:
            return "Limited recent activity"
        
        # Compare frequencies
        recent_freq = len(recent) / 14.0
        earlier_freq = len(earlier) / (len(earlier) / (len(trades) / 90.0))
        
        if recent_freq > earlier_freq * 1.3:
            pattern = "Increasing frequency"
        elif recent_freq < earlier_freq * 0.7:
            pattern = "Decreasing frequency"
        else:
            pattern = "Stable frequency"
        
        # Compare directionality
        recent_buys = len(recent[recent['side'] == 'BUY'])
        recent_sells = len(recent[recent['side'] == 'SELL'])
        
        if recent_buys > recent_sells * 1.5:
            pattern += ", net buying"
        elif recent_sells > recent_buys * 1.5:
            pattern += ", net selling"
        else:
            pattern += ", balanced"
        
        return pattern
        
    except Exception as e:
        logger.warning(f"Error describing pattern: {e}")
        return "Normal activity"


# ============================================================================
# Tool Registry for Gemini
# ============================================================================

def get_tool_declarations():
    """
    Get tool declarations for Gemini function calling.
    
    Returns list of tool definitions in Gemini's expected format.
    """
    return [
        {
            "name": "fetch_trades_summary",
            "description": "Fetch aggregated trading statistics for a client over 90 days. Returns trade count, instruments, holding periods, flip frequency, and order aggressiveness.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Client identifier"
                    }
                },
                "required": ["client_id"]
            }
        },
        {
            "name": "fetch_position_snapshot",
            "description": "Fetch current position concentrations for a client. Returns percentage exposure by instrument.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "Client identifier"
                    }
                },
                "required": ["client_id"]
            }
        }
    ]
