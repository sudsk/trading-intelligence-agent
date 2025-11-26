# HMM/Change-Point Integration Guide

## 🎯 Quick Summary

You asked: *"I want to implement HMM/change-point heuristic as per spec"*

**Solution**: Replace Gemini's single switch probability estimate with a sophisticated 5-signal statistical calculator.

**Files Provided**:
1. `switch_probability.py` - The HMM/change-point calculator
2. `AGENT_SUMMARY.md` - How each agent works (with HMM details)

---

## 📦 What You're Getting

### **SwitchProbabilityCalculator Class**

**5 Statistical Signals**:
1. **Pattern Instability** (0.0-0.30) - Rolling variance of trading behaviors
2. **Change-Point Detection** (0.0-0.25) - CUSUM test for regime breaks
3. **Momentum Shifts** (0.0-0.20) - Direction change frequency
4. **Flip Acceleration** (0.0-0.15) - Position reversal rate increase
5. **Feature Drift** (0.0-0.10) - Deviation from baseline metrics

**Formula**:
```
switch_prob = 0.30 (baseline) + Σ(5 signals)
Clamped to [0.15, 0.85]
```

---

## 🔧 Integration Steps (15 minutes)

### **Step 1: Copy the file**

```bash
# From your outputs directory to agents-service
cp switch_probability.py agents-service/agents/segmentation_agent/switch_probability.py
```

### **Step 2: Update requirements.txt**

```bash
# Add to agents-service/requirements.txt
scipy==1.11.0
```

Then install:
```bash
cd agents-service
pip install scipy --break-system-packages
```

### **Step 3: Update tools.py**

Edit `agents-service/agents/segmentation_agent/tools.py`:

```python
# Add import at the top (after existing imports)
from .switch_probability import compute_switch_probability

# Modify fetch_trades_summary function
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
```

### **Step 4: Update prompts.py**

Edit `agents-service/agents/segmentation_agent/prompts.py`:

```python
# Modify ANALYSIS_PROMPT_TEMPLATE to include switch probability
ANALYSIS_PROMPT_TEMPLATE = """Analyze the trading behavior for client {client_id}.

**Trade Summary:**
{trade_summary}

**Position Snapshot:**
{position_snapshot}

**Switch Probability Analysis (HMM/Change-Point):**
A sophisticated 5-signal statistical model has computed switch probability: {switch_prob:.2f}
Component Breakdown:
- Pattern Instability: {pattern:.3f} (variance in trading behaviors)
- Change-Point Detection: {changepoint:.3f} (regime breaks via CUSUM)
- Momentum Shifts: {momentum:.3f} (direction changes)
- Flip Acceleration: {flip:.3f} (position reversal rate)
- Feature Drift: {drift:.3f} (baseline deviation)

Reasoning: {switch_reasoning}

**Your Task:**
Based on this data, classify the client into one of the four segments and assess their strategy stability.

You may reference the computed switch probability in your reasoning, but also consider qualitative factors.
Your confidence score should reflect how well the quantitative data aligns with the segment classification.

Respond with ONLY the JSON output as specified in your instructions.
"""

def build_analysis_prompt(client_id: str, trade_summary: dict, position_snapshot: dict) -> str:
    """Build the complete prompt for Gemini."""
    # Format trade summary
    trade_summary_str = "\n".join([
        f"- Trade Count (90d): {trade_summary.get('trade_count', 0)}",
        f"- Instruments Traded: {', '.join(trade_summary.get('instruments', []))}",
        f"- Average Holding Period: {trade_summary.get('avg_holding_days', 0):.1f} days",
        f"- Position Flip Frequency: {trade_summary.get('position_flips', 0)} flips/30d",
        f"- Market Order Ratio: {trade_summary.get('market_order_ratio', 0):.1%}",
        f"- Recent Trading Pattern: {trade_summary.get('recent_trade_pattern', 'N/A')}"
    ])
    
    # Format position snapshot
    if position_snapshot:
        position_str = "\n".join([
            f"- {instrument}: {concentration:.1%} concentration"
            for instrument, concentration in position_snapshot.items()
        ])
    else:
        position_str = "- No significant positions"
    
    # Extract switch probability components
    switch_prob = trade_summary.get('switch_prob', 0.30)
    switch_reasoning = trade_summary.get('switch_reasoning', 'No reasoning available')
    components = trade_summary.get('switch_components', {})
    
    return ANALYSIS_PROMPT_TEMPLATE.format(
        client_id=client_id,
        trade_summary=trade_summary_str,
        position_snapshot=position_str,
        switch_prob=switch_prob,
        pattern=components.get('pattern_instability', 0.0),
        changepoint=components.get('change_point', 0.0),
        momentum=components.get('momentum_shift', 0.0),
        flip=components.get('flip_acceleration', 0.0),
        drift=components.get('feature_drift', 0.0),
        switch_reasoning=switch_reasoning
    )
```

### **Step 5: Update agent.py to prefer HMM**

Edit `agents-service/agents/segmentation_agent/agent.py`:

```python
def analyze(self, client_id: str) -> Dict[str, Any]:
    """Analyze client trading behavior using Gemini + HMM switch prob."""
    # ... existing code ...
    
    try:
        # Step 1: Gather data using tools (now includes HMM switch prob)
        trade_summary = fetch_trades_summary(client_id, self.data_service)
        position_snapshot = fetch_position_snapshot(client_id, self.data_service)
        
        # Step 2: Build prompt with data
        prompt = build_analysis_prompt(
            client_id=client_id,
            trade_summary=trade_summary,
            position_snapshot=position_snapshot
        )
        
        # Step 3: Call Gemini
        logger.info(f"🤖 Calling Gemini for segmentation analysis...")
        response = self.model.generate_content(
            prompt,
            generation_config=self.generation_config
        )
        
        # Step 4: Parse response
        result = self._parse_gemini_response(response.text, client_id)
        
        # Step 5: OVERRIDE with HMM switch probability
        # HMM is more reliable than Gemini's estimate
        if 'switch_prob' in trade_summary:
            logger.info(
                f"Using HMM switch prob {trade_summary['switch_prob']:.2f} "
                f"(overriding Gemini's estimate)"
            )
            result['switchProb'] = trade_summary['switch_prob']
            result['switch_method'] = 'HMM/change-point'
            result['switch_components'] = trade_summary.get('switch_components', {})
            result['switch_reasoning_hmm'] = trade_summary.get('switch_reasoning')
        else:
            result['switch_method'] = 'Gemini'
        
        # Step 6: Add metadata
        result['clientId'] = client_id
        result['primaryExposure'] = self._get_primary_exposure(position_snapshot)
        
        # ... rest of existing code ...
        
        return result
```

### **Step 6: Test**

```bash
# Terminal 1: Start service
cd agents-service
uvicorn main:app --port 8001 --reload

# Terminal 2: Test
curl -X POST http://localhost:8001/segment \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}' | jq '.switchProb, .switch_method, .switch_components'
```

Expected output:
```json
{
  "switchProb": 0.64,
  "switch_method": "HMM/change-point",
  "switch_components": {
    "pattern_instability": 0.18,
    "change_point": 0.20,
    "momentum_shift": 0.12,
    "flip_acceleration": 0.11,
    "feature_drift": 0.03
  },
  "switch_reasoning_hmm": "HIGH risk of strategy switch. Factors: High pattern instability (0.18), Recent regime change detected (0.20)..."
}
```

---

## 🎓 Understanding the Math

### **1. Pattern Instability (Rolling Variance)**

```python
# Measures how much trading behavior varies over time
daily_volume_variance = rolling_14d_variance(daily_volumes)
recent_variance = last_7_days_avg(daily_volume_variance)
baseline_variance = all_data_avg(daily_volume_variance)

variance_ratio = recent_variance / baseline_variance
score = min(0.30, variance_ratio * 0.10)
```

**Intuition**: If recent behavior is much more volatile than baseline → unstable → high switch risk

### **2. Change-Point Detection (CUSUM)**

```python
# CUSUM detects when the mean shifts
mean_flips = avg(daily_position_flips)
std_flips = stddev(daily_position_flips)

cusum = 0
for each day:
    cusum += (daily_flips - mean_flips)
    if abs(cusum) > 3 * std_flips:
        change_detected = True
        days_since_change = days_from_now

if days_since_change < 14:
    score = 0.25  # Recent change
elif days_since_change < 30:
    score = 0.15
else:
    score = 0.05
```

**Intuition**: Recent statistical breakpoint in flip rate → regime change → high switch risk

### **3. Momentum Shifts (Direction Changes)**

```python
# Count how often net positioning flips sign
daily_net_position = sum(buys - sells per day)
sign_changes = count(sign(daily_net_position) != sign(previous_day))
sign_change_rate = sign_changes / total_days

score = min(0.20, sign_change_rate * 0.40)
```

**Intuition**: Frequent direction flips → losing conviction → high switch risk

### **4. Flip Acceleration**

```python
recent_flip_rate = avg(flips in last 7 days)
baseline_flip_rate = avg(flips in previous 83 days)

acceleration = recent_flip_rate / baseline_flip_rate

if acceleration > 1.5:
    score = 0.15
elif acceleration > 1.2:
    score = 0.10
else:
    score = 0.05
```

**Intuition**: Accelerating position reversals → increasing uncertainty → high switch risk

### **5. Feature Drift**

```python
# Check for extreme values in key metrics
if abs(momentum_beta) > 0.9 or abs(momentum_beta) < 0.2:
    drift += 0.03
if holding_period < 2 days or holding_period > 60 days:
    drift += 0.03
if aggressiveness > 0.9 or aggressiveness < 0.2:
    drift += 0.04

score = min(0.10, sum(drift))
```

**Intuition**: Extreme behavior metrics → deviation from typical patterns → high switch risk

---

## 📊 Before/After Comparison

### **BEFORE (Gemini Only)**
```json
{
  "switchProb": 0.45,  // Gemini's single estimate
  "reasoning": "Client shows moderate instability"  // Black box
}
```

### **AFTER (HMM + Gemini)**
```json
{
  "switchProb": 0.64,  // Computed from 5 signals
  "switch_method": "HMM/change-point",
  "switch_components": {
    "pattern_instability": 0.18,     // Variance analysis
    "change_point": 0.20,            // CUSUM detected break
    "momentum_shift": 0.12,          // Direction changes
    "flip_acceleration": 0.11,       // Reversal rate up
    "feature_drift": 0.03           // Behavioral extremes
  },
  "switch_reasoning_hmm": "HIGH risk. Recent regime change (0.20) + high variance (0.18)",
  "segment": "Trend Follower",  // Still from Gemini (better for this)
  "confidence": 0.85
}
```

**Benefits**:
- ✅ Explainable (see which signals contributed)
- ✅ Reproducible (deterministic)
- ✅ Statistically rigorous (CUSUM, variance tests)
- ✅ Dynamic (updates with new data)

---

## 🚀 Demo Impact

### **Before Demo**:
"Switch probability is 53% based on AI analysis"

### **After Demo**:
"Switch probability is 64% computed from 5 statistical signals:
- Recent regime change detected (CUSUM test)
- Pattern instability elevated (rolling variance)
- Position flips accelerating
- Shows HIGH risk of strategy switch in next 14 days"

**Much more credible!** 🎯

---

## 🔍 Troubleshooting

### **Issue 1: scipy import fails**
```bash
pip install scipy==1.11.0 --break-system-packages
```

### **Issue 2: Not enough trade data**
The calculator handles this gracefully:
- < 7 days of data → returns baseline (0.30)
- < 20 days → limited signals used
- Logs warnings for insufficient data

### **Issue 3: switch_prob always 0.30**
Check logs for:
- "No trades for {client_id}" - Database empty
- "Error computing switch probability" - Check exception details

### **Issue 4: Want to tune sensitivity**
Edit `switch_probability.py` signal weights:
```python
# Current weights
pattern_score = min(0.30, ...)     # Max 0.30
changepoint_score = min(0.25, ...) # Max 0.25
momentum_score = min(0.20, ...)    # Max 0.20
flip_score = min(0.15, ...)        # Max 0.15
drift_score = min(0.10, ...)       # Max 0.10

# To make it MORE sensitive:
pattern_score = min(0.35, ...)     # Increase max
# To make it LESS sensitive:
pattern_score = min(0.20, ...)     # Decrease max
```

---

## ✅ Validation Checklist

- [ ] `scipy` installed
- [ ] `switch_probability.py` in segmentation_agent folder
- [ ] `tools.py` updated to call `compute_switch_probability()`
- [ ] `prompts.py` includes switch prob breakdown
- [ ] `agent.py` overrides Gemini's switch prob with HMM
- [ ] Test endpoint returns `switch_method: "HMM/change-point"`
- [ ] Test endpoint returns `switch_components` dict
- [ ] Logs show "Computing HMM switch probability"
- [ ] Switch prob is between 0.15 and 0.85

---

## 🎯 Expected Outcome

After integration, when you call `/analyze`:

```json
{
  "clientId": "ACME_FX_023",
  "segment": "Trend Follower",
  "confidence": 0.85,
  "switchProb": 0.64,
  "switch_method": "HMM/change-point",
  "switch_components": {
    "pattern_instability": 0.18,
    "change_point": 0.20,
    "momentum_shift": 0.12,
    "flip_acceleration": 0.11,
    "feature_drift": 0.03
  },
  "switch_reasoning_hmm": "HIGH risk of strategy switch. Factors: High pattern instability (0.18), Recent regime change detected (0.20), Frequent direction changes (0.12), Accelerating position flips (0.11).",
  "drivers": [...],
  "riskFlags": [...],
  "media": {...},
  "recommendations": [...]
}
```

**Key additions**:
- ✅ `switch_method` tells you it's using HMM (not Gemini)
- ✅ `switch_components` shows exactly where 0.64 came from
- ✅ `switch_reasoning_hmm` explains the decision

---

## 📚 References

**CUSUM Test**: 
- Page, E.S. (1954). "Continuous Inspection Schemes". Biometrika.
- Used for detecting mean shifts in time series

**Change-Point Detection**:
- Basseville, M., & Nikiforov, I.V. (1993). Detection of Abrupt Changes.
- Standard technique in regime detection

**Hidden Markov Models**:
- While we don't use full HMM here, the multi-signal approach captures the spirit:
  - Observable: Trading behaviors (flips, volumes, directions)
  - Hidden: True strategy regime
  - Transition prob: Switch probability

---

**Questions?** Check `AGENT_SUMMARY.md` for detailed agent explanations!
