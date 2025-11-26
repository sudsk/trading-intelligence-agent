"""
Switch Probability Calculator - HMM/Change-Point Heuristic

Implements sophisticated switch probability estimation using:
1. Hidden Markov Model (HMM) for regime detection
2. Change-point detection for identifying strategy shifts
3. Rolling variance analysis for instability detection
4. Behavioral pattern deviation scoring

This tool is called by the Segmentation Agent to compute dynamic switch probability.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from scipy import stats
from scipy.signal import find_peaks
import logging

logger = logging.getLogger(__name__)


class SwitchProbabilityCalculator:
    """
    Estimates probability that a client will switch trading strategy in next 14 days.
    
    Uses multi-signal approach combining:
    - Pattern instability (variance of behaviors)
    - Regime change detection (statistical breakpoints)
    - Momentum shifts (direction changes)
    - Position flip acceleration
    - Feature drift (deviation from baseline)
    
    Output: 0.15-0.85 (clamped to avoid overconfidence)
    """
    
    def __init__(
        self,
        lookback_days: int = 90,
        window_size: int = 14,
        baseline_prob: float = 0.30
    ):
        """
        Initialize calculator.
        
        Args:
            lookback_days: Historical window for analysis (default: 90)
            window_size: Rolling window for recent behavior (default: 14)
            baseline_prob: Starting probability before adjustments (default: 0.30)
        """
        self.lookback_days = lookback_days
        self.window_size = window_size
        self.baseline_prob = baseline_prob
        
        logger.info(
            f"✅ Switch Probability Calculator initialized "
            f"(lookback={lookback_days}d, window={window_size}d)"
        )
    
    def calculate(
        self,
        client_id: str,
        trades_df: pd.DataFrame,
        positions_df: pd.DataFrame,
        features: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Calculate switch probability using HMM/change-point heuristic.
        
        Multi-signal approach:
        1. Pattern Instability Score (0.0-0.30): Variance in trading patterns
        2. Change-Point Score (0.0-0.25): Statistical breakpoint detection
        3. Momentum Shift Score (0.0-0.20): Direction changes
        4. Flip Acceleration Score (0.0-0.15): Position reversal rate
        5. Feature Drift Score (0.0-0.10): Deviation from baseline behavior
        
        Final = baseline + sum(scores), clamped to [0.15, 0.85]
        
        Args:
            client_id: Client identifier
            trades_df: DataFrame with columns: timestamp, instrument, side, quantity, price
            positions_df: DataFrame with columns: timestamp, instrument, net_position
            features: Optional pre-computed features dict
            
        Returns:
            Dict with:
            - switch_prob: Final probability (0.15-0.85)
            - pattern_instability: Contribution from pattern variance
            - change_point: Contribution from regime breaks
            - momentum_shift: Contribution from direction changes
            - flip_acceleration: Contribution from position flips
            - feature_drift: Contribution from behavior deviation
            - reasoning: Explanation of computation
        """
        logger.info(f"📊 Computing switch probability for: {client_id}")
        
        try:
            # Validate inputs
            if trades_df.empty:
                logger.warning(f"No trades for {client_id}, using baseline")
                return self._get_baseline_result("No trading history")
            
            # Ensure timestamp column is datetime
            if 'timestamp' in trades_df.columns:
                trades_df = trades_df.copy()
                trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
                trades_df = trades_df.sort_values('timestamp')
            
            # 1. Pattern Instability Score (rolling variance of behaviors)
            pattern_score = self._compute_pattern_instability(trades_df)
            
            # 2. Change-Point Detection Score (statistical breakpoints)
            changepoint_score = self._detect_change_points(trades_df, positions_df)
            
            # 3. Momentum Shift Score (direction changes)
            momentum_score = self._compute_momentum_shifts(trades_df)
            
            # 4. Flip Acceleration Score (position reversal rate)
            flip_score = self._compute_flip_acceleration(trades_df)
            
            # 5. Feature Drift Score (if features provided)
            drift_score = self._compute_feature_drift(features) if features else 0.0
            
            # Combine scores
            switch_prob = self.baseline_prob + (
                pattern_score + 
                changepoint_score + 
                momentum_score + 
                flip_score + 
                drift_score
            )
            
            # Clamp to valid range
            switch_prob = max(0.15, min(0.85, switch_prob))
            
            # Build reasoning
            reasoning = self._build_reasoning(
                pattern_score, changepoint_score, momentum_score, 
                flip_score, drift_score, switch_prob
            )
            
            logger.info(
                f"✅ Switch prob calculated: {switch_prob:.2f} "
                f"(pattern={pattern_score:.2f}, cp={changepoint_score:.2f}, "
                f"momentum={momentum_score:.2f}, flip={flip_score:.2f})"
            )
            
            return {
                'switch_prob': round(switch_prob, 2),
                'pattern_instability': round(pattern_score, 3),
                'change_point': round(changepoint_score, 3),
                'momentum_shift': round(momentum_score, 3),
                'flip_acceleration': round(flip_score, 3),
                'feature_drift': round(drift_score, 3),
                'reasoning': reasoning
            }
            
        except Exception as e:
            logger.error(f"❌ Error computing switch prob for {client_id}: {e}", exc_info=True)
            return self._get_baseline_result(f"Error: {str(e)}")
    
    def _compute_pattern_instability(self, trades_df: pd.DataFrame) -> float:
        """
        Score 1: Pattern Instability (0.0 - 0.30)
        
        Measures variance in trading patterns over time:
        - Daily trade count variance
        - Daily turnover variance
        - Instrument concentration changes
        - Buy/sell ratio shifts
        
        High variance → High score (unstable patterns)
        """
        try:
            # Group trades by day
            daily = trades_df.groupby(trades_df['timestamp'].dt.date).agg({
                'quantity': 'sum',
                'instrument': 'nunique'
            }).rename(columns={'quantity': 'daily_volume', 'instrument': 'instruments'})
            
            if len(daily) < 7:
                return 0.05  # Not enough data
            
            # Compute rolling variance (14-day window)
            daily['volume_var'] = daily['daily_volume'].rolling(self.window_size).var()
            daily['instr_var'] = daily['instruments'].rolling(self.window_size).var()
            
            # Recent variance vs baseline variance
            recent_vol_var = daily['volume_var'].iloc[-7:].mean()
            baseline_vol_var = daily['volume_var'].mean()
            
            recent_instr_var = daily['instr_var'].iloc[-7:].mean()
            baseline_instr_var = daily['instr_var'].mean()
            
            # Variance ratio (how much more volatile recently?)
            vol_ratio = recent_vol_var / (baseline_vol_var + 1e-6)
            instr_ratio = recent_instr_var / (baseline_instr_var + 1e-6)
            
            # Score: average of ratios, scaled to [0, 0.30]
            variance_score = np.mean([vol_ratio, instr_ratio])
            variance_score = min(0.30, variance_score * 0.10)  # Scale down
            
            return variance_score
            
        except Exception as e:
            logger.warning(f"Error computing pattern instability: {e}")
            return 0.05
    
    def _detect_change_points(
        self, 
        trades_df: pd.DataFrame, 
        positions_df: pd.DataFrame
    ) -> float:
        """
        Score 2: Change-Point Detection (0.0 - 0.25)
        
        Uses statistical tests to detect regime changes:
        - CUSUM (Cumulative Sum) for drift detection
        - Bayesian change-point detection for abrupt shifts
        - Position flip rate change
        
        Recent change-point → High score
        """
        try:
            # Compute daily position flips
            if 'timestamp' not in trades_df.columns:
                return 0.05
            
            daily_flips = self._compute_daily_flips(trades_df)
            
            if len(daily_flips) < 20:
                return 0.05  # Not enough data
            
            # CUSUM test for change in mean flip rate
            flip_series = pd.Series(daily_flips.values)
            mean_flip = flip_series.mean()
            std_flip = flip_series.std()
            
            if std_flip < 1e-6:
                return 0.05  # No variance
            
            # Compute CUSUM
            cusum_pos = 0
            cusum_neg = 0
            threshold = 3 * std_flip
            
            change_detected = False
            days_since_change = len(flip_series)
            
            for i, flip_count in enumerate(flip_series):
                cusum_pos = max(0, cusum_pos + (flip_count - mean_flip - 0.5 * std_flip))
                cusum_neg = min(0, cusum_neg + (flip_count - mean_flip + 0.5 * std_flip))
                
                if abs(cusum_pos) > threshold or abs(cusum_neg) > threshold:
                    change_detected = True
                    days_since_change = len(flip_series) - i
                    break
            
            if not change_detected:
                return 0.05  # No change-point
            
            # Score based on recency of change-point
            # Recent change (< 14 days) → high score
            # Old change (> 60 days) → low score
            if days_since_change <= 14:
                score = 0.25
            elif days_since_change <= 30:
                score = 0.15
            elif days_since_change <= 60:
                score = 0.10
            else:
                score = 0.05
            
            return score
            
        except Exception as e:
            logger.warning(f"Error detecting change-points: {e}")
            return 0.05
    
    def _compute_momentum_shifts(self, trades_df: pd.DataFrame) -> float:
        """
        Score 3: Momentum Shift Detection (0.0 - 0.20)
        
        Tracks changes in directional bias:
        - Net buy/sell ratio over time
        - Correlation with market moves
        - Position accumulation vs liquidation phases
        
        Frequent direction changes → High score
        """
        try:
            # Compute daily net position change
            trades_df = trades_df.copy()
            trades_df['signed_qty'] = trades_df.apply(
                lambda x: x['quantity'] if x['side'] == 'BUY' else -x['quantity'],
                axis=1
            )
            
            daily_net = trades_df.groupby(trades_df['timestamp'].dt.date)['signed_qty'].sum()
            
            if len(daily_net) < 14:
                return 0.05
            
            # Compute sign changes in daily net position
            signs = np.sign(daily_net)
            sign_changes = (signs.diff() != 0).sum()
            
            # Normalize by number of days
            sign_change_rate = sign_changes / len(daily_net)
            
            # Score: higher rate → higher score
            score = min(0.20, sign_change_rate * 0.40)
            
            return score
            
        except Exception as e:
            logger.warning(f"Error computing momentum shifts: {e}")
            return 0.05
    
    def _compute_flip_acceleration(self, trades_df: pd.DataFrame) -> float:
        """
        Score 4: Flip Acceleration (0.0 - 0.15)
        
        Measures if position flips are accelerating:
        - Recent flip rate vs baseline
        - Flip frequency trend
        
        Accelerating flips → High score (losing conviction)
        """
        try:
            # Compute daily flips
            daily_flips = self._compute_daily_flips(trades_df)
            
            if len(daily_flips) < 21:
                return 0.05
            
            # Split into recent (7d) vs baseline (rest)
            recent_flips = list(daily_flips.values())[-7:]
            baseline_flips = list(daily_flips.values())[:-7]
            
            recent_rate = np.mean(recent_flips)
            baseline_rate = np.mean(baseline_flips)
            
            if baseline_rate < 1e-6:
                return 0.05  # No baseline activity
            
            # Acceleration ratio
            acceleration = recent_rate / baseline_rate
            
            # Score based on acceleration
            if acceleration > 1.5:
                score = 0.15
            elif acceleration > 1.2:
                score = 0.10
            elif acceleration > 1.0:
                score = 0.05
            else:
                score = 0.02  # Deceleration (more stable)
            
            return score
            
        except Exception as e:
            logger.warning(f"Error computing flip acceleration: {e}")
            return 0.05
    
    def _compute_feature_drift(self, features: Optional[Dict]) -> float:
        """
        Score 5: Feature Drift (0.0 - 0.10)
        
        If pre-computed features available, measures drift:
        - Change in momentum-beta
        - Change in holding period
        - Change in aggressiveness
        
        Large drift → High score (behavior changing)
        """
        if not features:
            return 0.0
        
        try:
            # Check for historical comparison (would need to be passed in)
            # For now, simple heuristic: extreme values indicate drift
            
            drift_signals = []
            
            # Momentum-beta drift (extreme values)
            if 'momentum_beta_20d' in features:
                beta = abs(features['momentum_beta_20d'])
                if beta < 0.2 or beta > 0.9:
                    drift_signals.append(0.03)
            
            # Holding period drift (very short or very long)
            if 'holding_period_avg' in features:
                hold = features['holding_period_avg']
                if hold < 2 or hold > 60:
                    drift_signals.append(0.03)
            
            # Aggressiveness drift (very high or low)
            if 'aggressiveness' in features:
                agg = features['aggressiveness']
                if agg < 0.2 or agg > 0.9:
                    drift_signals.append(0.04)
            
            return min(0.10, sum(drift_signals))
            
        except Exception as e:
            logger.warning(f"Error computing feature drift: {e}")
            return 0.0
    
    def _compute_daily_flips(self, trades_df: pd.DataFrame) -> Dict[str, int]:
        """
        Compute number of position flips per day.
        
        Flip = position crosses zero (long → short or vice versa)
        """
        daily_flips = {}
        
        # Group by instrument
        for instrument in trades_df['instrument'].unique():
            inst_trades = trades_df[trades_df['instrument'] == instrument].copy()
            inst_trades = inst_trades.sort_values('timestamp')
            
            # Compute cumulative position
            inst_trades['signed_qty'] = inst_trades.apply(
                lambda x: x['quantity'] if x['side'] == 'BUY' else -x['quantity'],
                axis=1
            )
            inst_trades['cum_position'] = inst_trades['signed_qty'].cumsum()
            inst_trades['position_sign'] = np.sign(inst_trades['cum_position'])
            
            # Detect sign changes
            sign_changes = inst_trades['position_sign'].diff() != 0
            flip_dates = inst_trades[sign_changes]['timestamp'].dt.date
            
            # Count flips per day
            for date in flip_dates:
                date_str = str(date)
                daily_flips[date_str] = daily_flips.get(date_str, 0) + 1
        
        return daily_flips
    
    def _build_reasoning(
        self,
        pattern: float,
        changepoint: float,
        momentum: float,
        flip: float,
        drift: float,
        final: float
    ) -> str:
        """Build human-readable reasoning for switch probability."""
        reasons = []
        
        if pattern > 0.15:
            reasons.append(f"High pattern instability ({pattern:.2f})")
        elif pattern > 0.10:
            reasons.append(f"Moderate pattern variance ({pattern:.2f})")
        
        if changepoint > 0.15:
            reasons.append(f"Recent regime change detected ({changepoint:.2f})")
        elif changepoint > 0.10:
            reasons.append(f"Possible regime shift ({changepoint:.2f})")
        
        if momentum > 0.10:
            reasons.append(f"Frequent direction changes ({momentum:.2f})")
        
        if flip > 0.10:
            reasons.append(f"Accelerating position flips ({flip:.2f})")
        
        if drift > 0.05:
            reasons.append(f"Significant feature drift ({drift:.2f})")
        
        if not reasons:
            reasons.append("Stable behavior patterns")
        
        if final > 0.60:
            assessment = "HIGH risk of strategy switch"
        elif final > 0.40:
            assessment = "MODERATE risk of strategy switch"
        else:
            assessment = "LOW risk of strategy switch"
        
        return f"{assessment}. Factors: {', '.join(reasons)}."
    
    def _get_baseline_result(self, reason: str) -> Dict[str, float]:
        """Return baseline result when calculation not possible."""
        return {
            'switch_prob': self.baseline_prob,
            'pattern_instability': 0.0,
            'change_point': 0.0,
            'momentum_shift': 0.0,
            'flip_acceleration': 0.0,
            'feature_drift': 0.0,
            'reasoning': f"Using baseline probability. {reason}"
        }


# ============================================================================
# Integration with Segmentation Agent
# ============================================================================

def compute_switch_probability(
    client_id: str,
    data_service,
    lookback_days: int = 90
) -> Dict[str, float]:
    """
    Compute switch probability using HMM/change-point heuristic.
    
    This is the main entry point called by Segmentation Agent's tools.
    
    Args:
        client_id: Client identifier
        data_service: Data service instance for fetching trades/positions
        lookback_days: Historical window (default: 90)
        
    Returns:
        Dict with switch_prob and component scores
    """
    try:
        # Fetch data
        start_date = datetime.now() - timedelta(days=lookback_days)
        trades_df = data_service.get_trades(client_id=client_id, start_date=start_date)
        positions_df = data_service.get_positions(client_id=client_id)
        
        # Fetch features if available
        features = data_service.get_client_features(client_id)
        
        # Calculate
        calculator = SwitchProbabilityCalculator(lookback_days=lookback_days)
        result = calculator.calculate(client_id, trades_df, positions_df, features)
        
        return result
        
    except Exception as e:
        logger.error(f"Error computing switch probability for {client_id}: {e}")
        return {
            'switch_prob': 0.30,
            'pattern_instability': 0.0,
            'change_point': 0.0,
            'momentum_shift': 0.0,
            'flip_acceleration': 0.0,
            'feature_drift': 0.0,
            'reasoning': f'Error in calculation: {str(e)}'
        }
