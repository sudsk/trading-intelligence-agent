# Data Scripts - Complete Guide

## 📁 What's in This Folder

### ✅ Your Existing Scripts (Keep These)
- `generate_clients.py` - Creates 50 clients
- `generate_trades.py` - Random trades
- `generate_positions.py` - Current positions
- `generate_market_bars.py` - OHLCV price data
- `generate_media.py` - Headlines with sentiment
- `generate_pnl_risk.py` - PnL/risk metrics
- `seed_data.py` - Master script (CSV output)
- `seed_database.py` - Direct DB insertion
- `schema.sql` - Your database schema

### 🆕 New Scripts (Agent-Ready)
- `generate_features.py` ⭐ - **Computes trading features**
- `generate_regimes.py` ⭐ - **Creates timeline data**
- `generate_switch_probability.py` ⭐ - **Tracks switch prob history**
- `generate_trades_v2.py` ⭐ - **Segment-specific patterns**
- `seed_database_v2.py` ⭐ - **Master orchestrator**

---

## 🎯 Why New Scripts?

Your existing scripts are great but missing data the **Gemini agents need**:

| Missing Data | Impact | New Script |
|--------------|--------|------------|
| Pre-computed features | Agents compute from scratch (slow) | `generate_features.py` |
| Switch prob history | No historical tracking for charts | `generate_switch_probability.py` |
| Client regimes | No timeline view | `generate_regimes.py` |
| Segment patterns | Gemini can't classify correctly | `generate_trades_v2.py` |

---

## 🚀 Quick Start

### Option 1: Run Master Script (Recommended)

```bash
cd data/scripts/

# Run everything in correct order
python seed_database_v2.py
```

This will:
1. ✅ Run your existing `seed_database.py` (clients, positions, headlines, market bars)
2. ✅ Generate segment-specific trades (`generate_trades_v2.py`)
3. ✅ Compute features (`generate_features.py`)
4. ✅ Create regimes (`generate_regimes.py`)
5. ✅ Generate switch prob history (`generate_switch_probability.py`)

**Total time:** ~5-10 minutes for 50 clients

### Option 2: Run Individually

```bash
# 1. Core data first (your existing script)
python seed_database.py

# 2. Then run new generators
python generate_trades_v2.py
python generate_features.py
python generate_regimes.py
python generate_switch_probability.py
```

### Option 3: Just Add Missing Tables

If you already have data and just need the missing tables:

```bash
# Add features
python generate_features.py

# Add regimes
python generate_regimes.py

# Add switch prob history
python generate_switch_probability.py
```

---

## 📊 What Each New Script Does

### 1. `generate_features.py` ⭐

**Purpose:** Computes trading features that agents need

**What it creates:**
```sql
INSERT INTO features (
    momentum_beta_1d,      -- Momentum alignment (1-day)
    momentum_beta_5d,      -- Momentum alignment (5-day)
    momentum_beta_20d,     -- Momentum alignment (20-day)
    holding_period_avg,    -- Average days held
    turnover,              -- Trading frequency
    aggressiveness,        -- Market order ratio
    lead_lag_alpha,        -- Leading/lagging indicator
    exposure_concentration -- Position concentration (JSON)
) VALUES ...
```

**Example output:**
- Trend Follower: `momentum_beta_1d=0.92`, `holding_period_avg=2.5`, `aggressiveness=0.78`
- Mean Reverter: `momentum_beta_1d=-0.35`, `holding_period_avg=1.8`, `turnover=0.65`
- Hedger: `momentum_beta_1d=0.15`, `holding_period_avg=45.0`, `turnover=0.05`

**Why it matters:** Segmentation Agent reads these instead of computing (10x faster!)

---

### 2. `generate_regimes.py` ⭐

**Purpose:** Creates historical segment timeline

**What it creates:**
```sql
INSERT INTO client_regimes (
    client_id, 
    segment, 
    start_date, 
    end_date,      -- NULL for current regime
    confidence, 
    notes
) VALUES ...
```

**Example timeline:**
```
ACME_FX_023:
  2024-01-01 to 2024-03-31: Mean Reverter (0.72 confidence)
  2024-04-01 to NULL:       Trend Follower (0.82 confidence)  ← Current
```

**Why it matters:** Powers the timeline view in UI

---

### 3. `generate_switch_probability.py` ⭐

**Purpose:** Tracks how switch probability evolved over time

**What it creates:**
```sql
INSERT INTO switch_probability_history (
    client_id,
    switch_prob,     -- 0.15 to 0.85
    confidence,
    segment,
    drivers,         -- JSON array
    risk_flags,      -- JSON array
    computed_at
) VALUES ...
```

**Example trajectory:**
```
ACME_FX_023:
  90 days ago: 0.35 (stable)
  60 days ago: 0.38
  30 days ago: 0.45 (gradual rise)
  7 days ago:  0.48
  Today:       0.53 (elevated) ← Alert triggers
```

**Why it matters:** Charts, alerts, trend analysis

---

### 4. `generate_trades_v2.py` ⭐

**Purpose:** Creates **realistic segment-specific trading patterns**

**What it does differently:**

#### Trend Follower Pattern:
```python
- Buy when price rising (momentum > 0)
- Sell when price falling (momentum < 0)
- Short holds (2-5 days)
- 70% market orders (aggressive)
- High turnover
```

#### Mean Reverter Pattern:
```python
- Buy when price below 20-day MA (oversold)
- Sell when price above 20-day MA (overbought)
- Very short holds (1-3 days)
- 100% limit orders (patient)
- Very high turnover
```

#### Hedger Pattern:
```python
- Infrequent trades (5-15 per 6 months)
- Long holds (30-90 days)
- Mostly sell-side (70% SELL)
- Defensive positioning
- Low turnover
```

#### Trend Setter Pattern:
```python
- Buy when down but will recover (anticipatory)
- Contrarian timing, directional conviction
- Medium holds (5-15 days)
- 80% market orders (very aggressive)
- High alpha (early entries)
```

**Why it matters:** Gemini can correctly classify segments from these patterns!

---

## 📋 Comparison: Old vs New

### Your Original `generate_trades.py`:
```python
# Random trades - no pattern
for _ in range(n_trades_per_client):
    instrument = np.random.choice(instruments)  # Random
    side = np.random.choice(['BUY', 'SELL'])    # Random
    timestamp = random_date()                   # Random
```

**Problem:** All clients look the same to Gemini

### New `generate_trades_v2.py`:
```python
# Segment-specific patterns
if segment == 'Trend Follower':
    if market_trend > 0:
        side = 'BUY'  # Follow momentum
        hold_days = 2-5  # Short
        order_type = 'MARKET'  # Aggressive
```

**Benefit:** Each segment has distinct behavior ✅

---

## 🎯 Order Matters!

**Correct order:**

1. **Market bars** (needed by trade generator)
2. **Clients** (needed by all)
3. **Trades** (needed by features)
4. **Positions** (needed by features)
5. **Features** (needs trades + positions)
6. **Regimes** (needs clients)
7. **Switch prob** (needs clients)
8. **Headlines** (independent)

`seed_database_v2.py` handles this automatically ✅

---

## 🔧 Configuration

All scripts use `.env`:

```bash
# .env file
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_intelligence
DB_USER=postgres
DB_PASSWORD=postgres
```

Or use `DATABASE_URL`:
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/trading_intelligence"
```

---

## 📊 What Gets Generated

Running `seed_database_v2.py` creates:

| Table | Records | Notes |
|-------|---------|-------|
| clients | 50 | 4 segments |
| trades | ~10,000+ | Segment-specific patterns |
| positions | ~150 | Current positions |
| market_bars | ~1,080 | 6 months × 6 instruments |
| headlines | 500 | Last 6 months |
| features | 50 | One per client |
| client_regimes | ~75 | 1-3 per client |
| switch_probability_history | ~600 | 10-15 per client |

**Total:** ~12,500+ records

**Database size:** ~50-100 MB

---

## 🧪 Testing

### Verify Features:
```sql
SELECT * FROM features WHERE client_id = 'ACME_FX_023';
```

Expected:
- `momentum_beta_*` values between -1 and 1
- `holding_period_avg` varies by segment
- `exposure_concentration` as JSON

### Verify Regimes:
```sql
SELECT * FROM client_regimes WHERE client_id = 'ACME_FX_023' ORDER BY start_date;
```

Expected:
- 1-4 regimes
- Last one has `end_date = NULL`
- Dates don't overlap

### Verify Switch Prob:
```sql
SELECT * FROM switch_probability_history 
WHERE client_id = 'ACME_FX_023' 
ORDER BY computed_at DESC LIMIT 10;
```

Expected:
- 10-15 historical points
- Gradual evolution (no wild jumps)
- Latest value is realistic for segment

### Verify Segment Patterns:
```sql
-- Trend Follower should have short holds
SELECT client_id, AVG(holding_period_avg) 
FROM features 
JOIN clients USING (client_id)
WHERE segment = 'Trend Follower'
GROUP BY client_id;

-- Should be 2-5 days

-- Hedger should have long holds
SELECT client_id, AVG(holding_period_avg) 
FROM features 
JOIN clients USING (client_id)
WHERE segment = 'Hedger'
GROUP BY client_id;

-- Should be 30-90 days
```

---

## 💡 Tips

### For Development:
```bash
# Test with small dataset first
python generate_features.py  # Takes 2-3 min for 50 clients
```

### For Production:
```bash
# Scale up
python seed_database_v2.py  # Full generation
```

### For Debugging:
```bash
# Run with verbose output
python -u generate_features.py 2>&1 | tee features.log
```

---

## 🚨 Common Issues

### Issue: "No market data"
**Solution:** Run `generate_market_bars.py` first
```bash
python generate_market_bars.py
```

### Issue: "No trades for client"
**Solution:** Ensure trades exist before computing features
```bash
python seed_database.py  # Or generate_trades_v2.py
```

### Issue: "JSONB error"
**Solution:** Ensure PostgreSQL 9.4+ (JSONB support)

---

## 🎓 Understanding the Data

### Momentum Beta:
- **+1.0** = Perfect trend following (buy rallies, sell dips)
- **0.0** = No correlation with market
- **-1.0** = Perfect contrarian (buy dips, sell rallies)

### Holding Period:
- **<3 days** = High frequency (Mean Reverter, Trend Follower)
- **10-20 days** = Medium term (Trend Setter)
- **>30 days** = Long term (Hedger)

### Turnover:
- **>0.5** = Very active
- **0.1-0.5** = Moderate
- **<0.1** = Passive (Hedger)

### Lead/Lag Alpha:
- **Positive** = Leading (Trend Setter) - anticipates moves
- **Near 0** = Concurrent
- **Negative** = Lagging (Trend Follower) - follows moves

---

## ✅ Verification Checklist

After running `seed_database_v2.py`:

- [ ] All tables populated (`\dt` in psql)
- [ ] Features computed for all clients
- [ ] Regimes have current + historical
- [ ] Switch prob shows gradual evolution
- [ ] Trades show segment-specific patterns
- [ ] No errors in logs
- [ ] Query performance is fast

---

## 🚀 Next Steps

1. **Run `seed_database_v2.py`** to generate all data
2. **Verify with SQL queries** above
3. **Test agents** - they should now work properly:
   - Segmentation reads from `features` table
   - Media Fusion analyzes `headlines`
   - NBA generates recommendations
4. **Check UI** - timeline and charts should work

---

## 📞 Need Help?

### Generated wrong patterns?
Re-run specific generator:
```bash
python generate_trades_v2.py  # Will overwrite
```

### Want different parameters?
Edit the scripts:
- Adjust `months_history` in generators
- Change `n_clients` in seed script
- Modify segment patterns in `generate_trades_v2.py`

### Database issues?
Check connection:
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM clients"
```

---

**Status: Ready to use!** 🎉

Run `seed_database_v2.py` and you'll have a complete, agent-ready database in ~5-10 minutes.
