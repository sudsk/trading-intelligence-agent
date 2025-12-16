-- Switch probability history
CREATE TABLE switch_probability_history (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50),  -- ← Remove REFERENCES clients(client_id)
    switch_prob DECIMAL(4, 3) NOT NULL,
    confidence DECIMAL(4, 3),
    segment VARCHAR(50),
    drivers JSONB,
    risk_flags JSONB,
    rm VARCHAR(100),
    primary_exposure VARCHAR(50),
    computed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_switch_prob_client_computed ON switch_probability_history(client_id, computed_at DESC);

CREATE TABLE IF NOT EXISTS insights (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL,  -- 'SIGNAL', 'ACTION', 'OUTCOME', 'ALERT'
    severity VARCHAR(20) NOT NULL DEFAULT 'INFO',
    title VARCHAR(200),
    reason TEXT,  -- Full description/message
    
    -- For SIGNAL/ALERT (switch probability changes)
    old_switch_prob NUMERIC(5,2),
    new_switch_prob NUMERIC(5,2),
    
    -- For ACTION (what was proposed)
    action_type VARCHAR(50),  -- e.g., 'PROACTIVE_OUTREACH', 'PROPOSE_HEDGE'
    products TEXT,  -- JSON array or comma-separated products
    rm VARCHAR(100),  -- Relationship manager who took action
    
    -- For OUTCOME (result of action)
    action_id INTEGER,  -- Links OUTCOME back to its ACTION
    outcome_status VARCHAR(50),  -- 'success', 'failed', 'pending'
    
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_insights_client_id ON insights(client_id);
CREATE INDEX idx_insights_type ON insights(type);
CREATE INDEX idx_insights_created_at ON insights(created_at DESC);
CREATE INDEX idx_insights_action_id ON insights(action_id);


-- Sample switch probability data for 20 demo clients
-- Mix of all segments with varied probabilities for realistic demo


-- Client Regimes History (for Timeline)
CREATE TABLE client_regimes (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50),
    segment VARCHAR(50) NOT NULL,
    period VARCHAR(50) NOT NULL,  -- e.g., "Q1 2025", "Jan-Mar 2025"
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_client_regimes_client ON client_regimes(client_id, start_date DESC);

-- Media analysis results
CREATE TABLE IF NOT EXISTS media_analysis (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    pressure VARCHAR(20),
    sentiment_score DECIMAL(3,2),
    headlines JSONB,
    analyzed_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_media_client_time ON media_analysis(client_id, analyzed_at DESC);

-- NBA recommendations
CREATE TABLE IF NOT EXISTS nba_recommendations (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    recommendations JSONB,
    generated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_recs_client_time ON nba_recommendations(client_id, generated_at DESC);

-- Sample switch probability data for 20 demo clients
INSERT INTO switch_probability_history (client_id, switch_prob, confidence, segment, drivers, risk_flags, rm, primary_exposure, computed_at)
VALUES 
  -- High switch probability (0.60-0.85) - Need attention
  ('ACME_FX_023', 0.720, 0.850, 'Trend Follower', 
   '["High momentum-beta (0.85) with strong directional bias", "Shortened holding times from 5d to 2.8d average", "Recent pattern break detected in EURUSD positioning"]',
   '["sustained_deviation", "volatility_spike"]', 'Sarah Chen','GBPUSD',
   NOW() - INTERVAL '5 minutes'),
   
  ('ATLAS_BOND_012', 0.680, 0.820, 'Trend Setter',
   '["Early positioning ahead of rate moves shows alpha", "Positive lead-lag correlation (0.72) vs market", "Duration concentration in 5-7yr sector creating risk"]',
   '["sustained_deviation"]','James Wong','EURUSD',
   NOW() - INTERVAL '2 minutes'),
   
  ('NOVA_MACRO_045', 0.760, 0.880, 'Mean Reverter',
   '["Frequent position flips (18/month) indicate reversal-seeking", "Counter-trend positioning in 78% of recent trades", "Recent changepoint detected - drift toward momentum trades"]',
   '["sustained_deviation", "volatility_spike", "position_concentration"]','Emma Richardson','AUDUSD',
   NOW() - INTERVAL '8 minutes'),
   
  ('PHOENIX_CAPITAL_031', 0.810, 0.900, 'Trend Follower',
   '["Very high momentum alignment (0.89 beta) with market moves", "Ultra-short 2.3-day holding period suggests active trading", "Sharp increase in position volatility last 14 days"]',
   '["sustained_deviation", "volatility_spike", "position_concentration"]','Michael Torres','GBPUSD',
   NOW() - INTERVAL '12 minutes'),
   
  ('SENTINEL_ASSETS_067', 0.650, 0.800, 'Hedger',
   '["Long 42-day average holding reflects defensive mindset", "Balanced exposure maintenance with 35% hedge ratio", "Recent concentration increase in single-name positions"]',
   '["sustained_deviation", "position_concentration"]','Michael Torres','GBPUSD',
   NOW() - INTERVAL '6 minutes'),
  
  -- Medium switch probability (0.35-0.59) - Monitor
  ('ZEUS_COMM_019', 0.480, 0.720, 'Mean Reverter',
   '["Moderate flip frequency (8/month) shows reversal strategy", "6.5-day holding period aligns with range-bound approach", "Mixed order types suggest flexible entry/exit strategy"]',
   '[]','Michael Torres','AUDUSD',
   NOW() - INTERVAL '3 minutes'),
   
  ('TITAN_EQ_008', 0.420, 0.680, 'Hedger',
   '["Consistent 38-day holding period shows conviction", "Low turnover (0.6 trades/day) reflects defensive approach", "Options usage indicates structured hedging strategy"]',
   '[]','Sarah Chen','AUDUSD',
   NOW() - INTERVAL '7 minutes'),
   
  ('MERIDIAN_FUND_052', 0.520, 0.750, 'Trend Setter',
   '["Anticipatory positioning with 0.68 lead-lag correlation", "Recent transition from trend-following to leading behavior", "Increased market order usage (72%) shows conviction"]',
   '["sustained_deviation"]','Sarah Chen','AUDUSD',
   NOW() - INTERVAL '15 minutes'),
   
  ('APEX_TRADING_089', 0.460, 0.700, 'Trend Follower',
   '["High trade frequency (4.2/day) with momentum alignment", "Short 3.1-day holding indicates active trend capture", "Consistent directional bias (82% momentum-aligned)"]',
   '[]','Sarah Chen','AUDUSD',
   NOW() - INTERVAL '10 minutes'),
   
  ('OLYMPUS_VENTURES_024', 0.390, 0.650, 'Mean Reverter',
   '["Counter-trend positioning in 68% of trades", "Moderate 7.2-day holding suits reversal strategy", "Recent reduction in flip frequency suggests stabilization"]',
   '[]','Sarah Chen','SPX',
   NOW() - INTERVAL '18 minutes'),
   
  ('QUANTUM_FINANCE_015', 0.540, 0.770, 'Hedger',
   '["Long-term 45-day average holding shows defensive focus", "Balanced position maintenance across currency pairs", "Recent uptick in position concentration needs monitoring"]',
   '["sustained_deviation"]','James Wong','USDCHF',
   NOW() - INTERVAL '9 minutes'),
   
  ('VANGUARD_MARKETS_078', 0.440, 0.690, 'Trend Setter',
   '["Early market-making positioning shows anticipatory behavior", "Mild positive lead-lag (0.58) vs benchmark", "Consistent bid-ask management with directional overlay"]',
   '[]','Emma Richardson','GBPUSD',
   NOW() - INTERVAL '20 minutes'),
  
  -- Low switch probability (0.15-0.34) - Stable
  ('CORNERSTONE_INV_033', 0.280, 0.620, 'Trend Follower',
   '["Stable momentum-beta (0.76) over 90-day period", "Consistent 4.5-day holding pattern", "Low position flip frequency (2/month) shows conviction"]',
   '[]','Michael Torres','USDCHF',
   NOW() - INTERVAL '4 minutes'),
   
  ('HORIZON_GLOBAL_056', 0.310, 0.640, 'Mean Reverter',
   '["Disciplined counter-trend approach with 8.5-day holds", "Consistent reversal identification across markets", "Stable flip frequency (9/month) shows systematic strategy"]',
   '[]','Michael Torres','GBPUSD',
   NOW() - INTERVAL '11 minutes'),
   
  ('STERLING_FX_041', 0.240, 0.590, 'Hedger',
   '["Very long 52-day holding period reflects conviction", "Extremely low turnover (0.3 trades/day)", "Consistent hedging approach with minimal drift"]',
   '[]','Emma Richardson','AUDUSD',
   NOW() - INTERVAL '14 minutes'),
   
  ('ECLIPSE_PARTNERS_092', 0.190, 0.550, 'Trend Setter',
   '["Strong early-positioning alpha (0.82 lead-lag)", "Systematic approach with consistent entry signals", "High conviction shown by 15% market order usage"]',
   '[]','Sarah Chen','USDJPY',
   NOW() - INTERVAL '22 minutes'),
   
  ('PINNACLE_WEALTH_064', 0.330, 0.660, 'Trend Follower',
   '["Moderate momentum alignment (0.71 beta)", "Stable 5.2-day average holding period", "Consistent directional bias with low volatility"]',
   '[]','James Wong','SPX',
   NOW() - INTERVAL '16 minutes'),
   
  ('NEXUS_CAPITAL_017', 0.270, 0.610, 'Mean Reverter',
   '["Patient reversal strategy with 9.8-day holds", "Consistent counter-positioning across market regimes", "Stable behavior pattern over 90-day observation"]',
   '[]','Emma Richardson','GBPUSD',
   NOW() - INTERVAL '13 minutes'),
   
  ('ROCKFORD_TRUST_088', 0.220, 0.580, 'Hedger',
   '["Ultra-long 68-day average holding shows conviction", "Minimal trading activity (0.2 trades/day)", "Rock-solid hedging approach with zero drift"]',
   '[]','James Wong','USDJPY',
   NOW() - INTERVAL '19 minutes'),
   
  ('SUMMIT_ADVISORS_051', 0.290, 0.630, 'Trend Setter',
   '["Consistent anticipatory positioning (0.65 lead-lag)", "Stable early-entry patterns across market cycles", "Disciplined approach with minimal strategy drift"]',
   '[]','James Wong','AUDUSD',
   NOW() - INTERVAL '17 minutes')
ON CONFLICT DO NOTHING;

-- Sample Timeline Data for Demo Clients
INSERT INTO client_regimes (client_id, segment, period, description, start_date, end_date) VALUES
  -- ACME_FX_023 - Evolved from Hedger to Trend Follower
  ('ACME_FX_023', 'Hedger', 'Q1 2025', 'Conservative hedging strategy', '2025-01-01', '2025-03-31'),
  ('ACME_FX_023', 'Mean Reverter', 'Q2 2025', 'Shifted to mean reversion after volatility spike', '2025-04-01', '2025-06-30'),
  ('ACME_FX_023', 'Trend Follower', 'Q3-Q4 2025', 'Adopted momentum following strategy', '2025-07-01', NULL),
  
  -- PHOENIX_CAPITAL_031 - Consistent Trend Follower
  ('PHOENIX_CAPITAL_031', 'Trend Follower', 'Q1-Q2 2025', 'Strong momentum bias', '2025-01-01', '2025-06-30'),
  ('PHOENIX_CAPITAL_031', 'Trend Follower', 'Q3-Q4 2025', 'Continued momentum strategy', '2025-07-01', NULL),
  
  -- NOVA_MACRO_045 - Volatile switches
  ('NOVA_MACRO_045', 'Trend Setter', 'Q1 2025', 'Aggressive positioning', '2025-01-01', '2025-03-31'),
  ('NOVA_MACRO_045', 'Mean Reverter', 'Q2 2025', 'Pivot to contrarian trades', '2025-04-01', '2025-06-30'),
  ('NOVA_MACRO_045', 'Mean Reverter', 'Q3-Q4 2025', 'Maintained reversal strategy', '2025-07-01', NULL),
  
  -- ATLAS_BOND_012 - Evolved to Trend Setter
  ('ATLAS_BOND_012', 'Hedger', 'Q1-Q2 2025', 'Risk-off positioning', '2025-01-01', '2025-06-30'),
  ('ATLAS_BOND_012', 'Trend Setter', 'Q3-Q4 2025', 'More aggressive trend setting', '2025-07-01', NULL),
  
  -- SENTINEL_ASSETS_067 - Stable Hedger
  ('SENTINEL_ASSETS_067', 'Hedger', 'Q1-Q4 2025', 'Consistent hedging approach', '2025-01-01', NULL),
  
  -- ZEUS_COMM_019 - Mean Reverter throughout
  ('ZEUS_COMM_019', 'Mean Reverter', 'Q1-Q2 2025', 'Commodity mean reversion', '2025-01-01', '2025-06-30'),
  ('ZEUS_COMM_019', 'Mean Reverter', 'Q3-Q4 2025', 'Continued mean reversion', '2025-07-01', NULL),
  
  -- TITAN_EQ_008 - Stable Hedger
  ('TITAN_EQ_008', 'Hedger', 'Q1-Q4 2025', 'Equity hedging strategy', '2025-01-01', NULL),
  
  -- MERIDIAN_FUND_052 - Trend Setter evolution
  ('MERIDIAN_FUND_052', 'Trend Follower', 'Q1 2025', 'Momentum trading', '2025-01-01', '2025-03-31'),
  ('MERIDIAN_FUND_052', 'Trend Setter', 'Q2-Q4 2025', 'Leading market moves', '2025-04-01', NULL),
  
  -- APEX_TRADING_089 - Consistent Trend Follower
  ('APEX_TRADING_089', 'Trend Follower', 'Q1-Q4 2025', 'Systematic trend following', '2025-01-01', NULL),
  
  -- OLYMPUS_VENTURES_024 - Mean Reverter
  ('OLYMPUS_VENTURES_024', 'Mean Reverter', 'Q1-Q4 2025', 'Value-focused reversals', '2025-01-01', NULL),
  
  -- QUANTUM_FINANCE_015 - Hedger with recent evolution
  ('QUANTUM_FINANCE_015', 'Hedger', 'Q1-Q3 2025', 'Conservative hedging', '2025-01-01', '2025-09-30'),
  ('QUANTUM_FINANCE_015', 'Hedger', 'Q4 2025', 'Maintained hedging focus', '2025-10-01', NULL),
  
  -- VANGUARD_MARKETS_078 - Trend Setter
  ('VANGUARD_MARKETS_078', 'Trend Setter', 'Q1-Q4 2025', 'Market making with directional bias', '2025-01-01', NULL),
  
  -- CORNERSTONE_INV_033 - Stable Trend Follower
  ('CORNERSTONE_INV_033', 'Trend Follower', 'Q1-Q4 2025', 'Long-term momentum', '2025-01-01', NULL),
  
  -- HORIZON_GLOBAL_056 - Mean Reverter
  ('HORIZON_GLOBAL_056', 'Mean Reverter', 'Q1-Q4 2025', 'Global macro reversals', '2025-01-01', NULL),
  
  -- STERLING_FX_041 - Stable Hedger
  ('STERLING_FX_041', 'Hedger', 'Q1-Q4 2025', 'FX hedging specialist', '2025-01-01', NULL),
  
  -- ECLIPSE_PARTNERS_092 - Trend Setter
  ('ECLIPSE_PARTNERS_092', 'Trend Setter', 'Q1-Q4 2025', 'Prop trading momentum', '2025-01-01', NULL),
  
  -- PINNACLE_WEALTH_064 - Trend Follower
  ('PINNACLE_WEALTH_064', 'Trend Follower', 'Q1-Q4 2025', 'Client portfolio momentum', '2025-01-01', NULL),
  
  -- NEXUS_CAPITAL_017 - Mean Reverter
  ('NEXUS_CAPITAL_017', 'Mean Reverter', 'Q1-Q4 2025', 'VC-backed reversals', '2025-01-01', NULL),
  
  -- ROCKFORD_TRUST_088 - Hedger
  ('ROCKFORD_TRUST_088', 'Hedger', 'Q1-Q4 2025', 'Trust fund hedging', '2025-01-01', NULL),
  
  -- SUMMIT_ADVISORS_051 - Trend Setter
  ('SUMMIT_ADVISORS_051', 'Trend Setter', 'Q1-Q4 2025', 'Advisory-driven trends', '2025-01-01', NULL)
ON CONFLICT DO NOTHING;


-- Sample Insights for Demo (last 7 days)
INSERT INTO insights (client_id, type, severity, old_switch_prob, new_switch_prob, reason, acknowledged, created_at) VALUES
  -- High priority signals (recent)
  ('ACME_FX_023', 'SIGNAL', 'HIGH', 0.650, 0.720, 'Switch probability increased by 11% - pattern break detected in EURUSD positions', FALSE, NOW() - INTERVAL '2 hours'),
  ('PHOENIX_CAPITAL_031', 'SIGNAL', 'CRITICAL', 0.750, 0.810, 'Critical threshold breached - sustained deviation from normal trading pattern', FALSE, NOW() - INTERVAL '4 hours'),
  ('NOVA_MACRO_045', 'SIGNAL', 'HIGH', 0.680, 0.760, 'Volatility spike detected - position concentration risk elevated', FALSE, NOW() - INTERVAL '8 hours'),
  
  -- Actions taken (yesterday)
  ('ACME_FX_023', 'ACTION', 'MEDIUM', NULL, NULL, 'RM outreach scheduled - Sarah Chen to contact client within 48 hours', FALSE, NOW() - INTERVAL '1 day'),
  ('PHOENIX_CAPITAL_031', 'ACTION', 'HIGH', NULL, NULL, 'Emergency risk review meeting scheduled with Michael Torres', FALSE, NOW() - INTERVAL '1 day'),
  ('ATLAS_BOND_012', 'ACTION', 'MEDIUM', NULL, NULL, 'Portfolio rebalancing proposal sent to client', FALSE, NOW() - INTERVAL '1 day'),
  
  -- Outcomes (2-3 days ago)
  ('SENTINEL_ASSETS_067', 'OUTCOME', 'LOW', 0.650, 0.580, 'Client meeting successful - agreed to hedge 30% of exposure, switch prob decreased', TRUE, NOW() - INTERVAL '2 days'),
  ('ATLAS_BOND_012', 'OUTCOME', 'MEDIUM', 0.720, 0.680, 'Risk mitigation implemented - diversification strategy adopted', TRUE, NOW() - INTERVAL '2 days'),
  ('ZEUS_COMM_019', 'OUTCOME', 'LOW', 0.520, 0.480, 'Client engagement positive - relationship strengthened', TRUE, NOW() - INTERVAL '3 days'),
  
  -- Medium priority signals (3-5 days ago)
  ('MERIDIAN_FUND_052', 'SIGNAL', 'MEDIUM', 0.480, 0.520, 'Segment drift detected - moving toward trend setting behavior', FALSE, NOW() - INTERVAL '3 days'),
  ('QUANTUM_FINANCE_015', 'SIGNAL', 'MEDIUM', 0.500, 0.540, 'Position concentration increasing in Asian FX pairs', FALSE, NOW() - INTERVAL '4 days'),
  ('VANGUARD_MARKETS_078', 'SIGNAL', 'MEDIUM', 0.410, 0.440, 'Trading frequency increasing - monitoring required', FALSE, NOW() - INTERVAL '5 days'),
  
  -- More actions (4-5 days ago)
  ('NOVA_MACRO_045', 'ACTION', 'HIGH', NULL, NULL, 'Risk limit review initiated - compliance check requested', FALSE, NOW() - INTERVAL '4 days'),
  ('SENTINEL_ASSETS_067', 'ACTION', 'MEDIUM', NULL, NULL, 'Client strategy review call scheduled', TRUE, NOW() - INTERVAL '5 days'),
  
  -- Low priority signals (5-7 days ago)
  ('CORNERSTONE_INV_033', 'SIGNAL', 'LOW', 0.260, 0.280, 'Minor shift in trading pattern - within normal range', FALSE, NOW() - INTERVAL '5 days'),
  ('HORIZON_GLOBAL_056', 'SIGNAL', 'LOW', 0.290, 0.310, 'Holding period slightly extended - low risk', FALSE, NOW() - INTERVAL '6 days'),
  ('STERLING_FX_041', 'SIGNAL', 'LOW', 0.220, 0.240, 'Stable client - minor fluctuation detected', FALSE, NOW() - INTERVAL '6 days'),
  ('PINNACLE_WEALTH_064', 'SIGNAL', 'LOW', 0.310, 0.330, 'Portfolio adjustment noted - monitoring continues', FALSE, NOW() - INTERVAL '7 days'),
  
  -- Older outcomes (7 days ago)
  ('OLYMPUS_VENTURES_024', 'OUTCOME', 'LOW', 0.420, 0.390, 'Quarterly review completed - client satisfied with performance', TRUE, NOW() - INTERVAL '7 days'),
  ('APEX_TRADING_089', 'OUTCOME', 'MEDIUM', 0.500, 0.460, 'Hedging strategy implemented - reduced exposure risk', TRUE, NOW() - INTERVAL '7 days')
ON CONFLICT DO NOTHING;


INSERT INTO media_analysis (client_id, pressure, sentiment_score, headlines, analyzed_at) VALUES

-- High switch probability clients (HIGH media pressure)
('ACME_FX_023', 'HIGH', -0.45, 
 '[
   {"title": "Euro Faces Pressure Amid ECB Policy Uncertainty", "sentiment": "negative", "timestamp": "2025-12-09T14:30:00Z", "source": "Reuters"},
   {"title": "Technology Sector Volatility Impacts FX Markets", "sentiment": "negative", "timestamp": "2025-12-09T13:15:00Z", "source": "Bloomberg"},
   {"title": "Dollar Strength Continues as Fed Signals Hawkish Stance", "sentiment": "negative", "timestamp": "2025-12-09T11:45:00Z", "source": "Financial Times"},
   {"title": "Risk-Off Sentiment Dominates European Trading Session", "sentiment": "negative", "timestamp": "2025-12-09T10:20:00Z", "source": "WSJ"},
   {"title": "Tech Earnings Concerns Drive FX Volatility Higher", "sentiment": "negative", "timestamp": "2025-12-09T09:00:00Z", "source": "CNBC"}
 ]'::jsonb,
 NOW() - INTERVAL '5 minutes'),

('ATLAS_BOND_012', 'HIGH', -0.38,
 '[
   {"title": "Bond Market Selloff Accelerates on Rate Fears", "sentiment": "negative", "timestamp": "2025-12-09T14:45:00Z", "source": "Bloomberg"},
   {"title": "European Yields Surge to Multi-Year Highs", "sentiment": "negative", "timestamp": "2025-12-09T13:30:00Z", "source": "Reuters"},
   {"title": "Fixed Income Traders Brace for ECB Decision", "sentiment": "neutral", "timestamp": "2025-12-09T12:00:00Z", "source": "Financial Times"},
   {"title": "Credit Spreads Widen Amid Market Uncertainty", "sentiment": "negative", "timestamp": "2025-12-09T10:45:00Z", "source": "WSJ"},
   {"title": "Duration Risk Concerns Mount in European Markets", "sentiment": "negative", "timestamp": "2025-12-09T09:15:00Z", "source": "FT Alphaville"}
 ]'::jsonb,
 NOW() - INTERVAL '2 minutes'),

('NOVA_MACRO_045', 'HIGH', -0.52,
 '[
   {"title": "Global Macro Funds Face Unprecedented Volatility", "sentiment": "negative", "timestamp": "2025-12-09T15:00:00Z", "source": "Bloomberg"},
   {"title": "Multi-Asset Portfolios Under Pressure from Rate Swings", "sentiment": "negative", "timestamp": "2025-12-09T14:00:00Z", "source": "Reuters"},
   {"title": "Hedge Funds Reduce Risk Amid Market Turbulence", "sentiment": "negative", "timestamp": "2025-12-09T12:30:00Z", "source": "Financial Times"},
   {"title": "Macro Strategy Returns Turn Negative in Q4", "sentiment": "negative", "timestamp": "2025-12-09T11:00:00Z", "source": "Institutional Investor"},
   {"title": "Market Dislocation Creates Challenges for Systematic Funds", "sentiment": "negative", "timestamp": "2025-12-09T09:30:00Z", "source": "Hedge Fund Alert"}
 ]'::jsonb,
 NOW() - INTERVAL '8 minutes'),

('PHOENIX_CAPITAL_031', 'HIGH', -0.58,
 '[
   {"title": "Private Equity Portfolios Exposed to Currency Swings", "sentiment": "negative", "timestamp": "2025-12-09T14:50:00Z", "source": "Private Equity International"},
   {"title": "FX Hedging Costs Surge for PE Funds", "sentiment": "negative", "timestamp": "2025-12-09T13:45:00Z", "source": "Bloomberg"},
   {"title": "Capital Markets Volatility Impacts PE Exit Strategies", "sentiment": "negative", "timestamp": "2025-12-09T12:15:00Z", "source": "Financial Times"},
   {"title": "Dollar Strength Erodes Returns for US-Based PE Investors", "sentiment": "negative", "timestamp": "2025-12-09T11:30:00Z", "source": "WSJ"},
   {"title": "Private Capital Firms Reassess Currency Exposure", "sentiment": "negative", "timestamp": "2025-12-09T10:00:00Z", "source": "Reuters"}
 ]'::jsonb,
 NOW() - INTERVAL '12 minutes'),

('SENTINEL_ASSETS_067', 'HIGH', -0.42,
 '[
   {"title": "Asset Managers Navigate Choppy FX Markets", "sentiment": "negative", "timestamp": "2025-12-09T15:15:00Z", "source": "Bloomberg"},
   {"title": "Currency Volatility Tests Hedging Strategies", "sentiment": "negative", "timestamp": "2025-12-09T14:20:00Z", "source": "Reuters"},
   {"title": "North American Asset Managers Face FX Headwinds", "sentiment": "negative", "timestamp": "2025-12-09T13:00:00Z", "source": "Investment News"},
   {"title": "Risk Management Focus Intensifies Amid Market Swings", "sentiment": "neutral", "timestamp": "2025-12-09T11:45:00Z", "source": "Financial Times"},
   {"title": "Multi-Asset Strategies Under Scrutiny as Correlations Break", "sentiment": "negative", "timestamp": "2025-12-09T10:30:00Z", "source": "Institutional Investor"}
 ]'::jsonb,
 NOW() - INTERVAL '6 minutes'),

-- Medium switch probability clients (MEDIUM media pressure)
('ZEUS_COMM_019', 'MEDIUM', -0.25,
 '[
   {"title": "Commodity Prices Stabilize After Recent Volatility", "sentiment": "neutral", "timestamp": "2025-12-09T14:30:00Z", "source": "Reuters"},
   {"title": "Energy Markets Show Mixed Signals on Demand", "sentiment": "neutral", "timestamp": "2025-12-09T13:15:00Z", "source": "Bloomberg Energy"},
   {"title": "European Commodity Traders Cautious Amid Rate Uncertainty", "sentiment": "negative", "timestamp": "2025-12-09T12:00:00Z", "source": "Financial Times"},
   {"title": "Industrial Metals Face Headwinds from Strong Dollar", "sentiment": "negative", "timestamp": "2025-12-09T10:45:00Z", "source": "Mining.com"},
   {"title": "Agricultural Commodities Outlook Remains Mixed", "sentiment": "neutral", "timestamp": "2025-12-09T09:30:00Z", "source": "Agrimoney"}
 ]'::jsonb,
 NOW() - INTERVAL '3 minutes'),

('TITAN_EQ_008', 'MEDIUM', -0.18,
 '[
   {"title": "Asian Equity Markets Show Resilience Amid FX Volatility", "sentiment": "positive", "timestamp": "2025-12-09T08:00:00Z", "source": "Asia Times Financial"},
   {"title": "Fund Managers Maintain Hedges Despite Market Calm", "sentiment": "neutral", "timestamp": "2025-12-09T07:30:00Z", "source": "Reuters"},
   {"title": "Currency Stability Supports Asian Investment Flows", "sentiment": "positive", "timestamp": "2025-12-09T06:45:00Z", "source": "Bloomberg"},
   {"title": "Regional Equity Funds Navigate Policy Divergence", "sentiment": "neutral", "timestamp": "2025-12-09T05:30:00Z", "source": "Financial Times Asia"},
   {"title": "Hedging Strategies Prove Effective for Asia-Focused Funds", "sentiment": "positive", "timestamp": "2025-12-09T04:15:00Z", "source": "Fund Selector Asia"}
 ]'::jsonb,
 NOW() - INTERVAL '7 minutes'),

('MERIDIAN_FUND_052', 'MEDIUM', -0.28,
 '[
   {"title": "Hedge Funds Adjust Positioning Amid Macro Uncertainty", "sentiment": "negative", "timestamp": "2025-12-09T08:30:00Z", "source": "Hedge Fund Intelligence"},
   {"title": "Asian Opportunity Funds Face Currency Headwinds", "sentiment": "negative", "timestamp": "2025-12-09T07:45:00Z", "source": "Bloomberg"},
   {"title": "Regional FX Volatility Tests Multi-Strategy Approaches", "sentiment": "neutral", "timestamp": "2025-12-09T06:30:00Z", "source": "AsiaHedge"},
   {"title": "Dollar Strength Impacts EM-Focused Investment Strategies", "sentiment": "negative", "timestamp": "2025-12-09T05:15:00Z", "source": "Emerging Markets"},
   {"title": "Hedge Funds Increase Hedging Ratios in Asian Markets", "sentiment": "neutral", "timestamp": "2025-12-09T04:00:00Z", "source": "Reuters"}
 ]'::jsonb,
 NOW() - INTERVAL '15 minutes'),

('APEX_TRADING_089', 'MEDIUM', -0.22,
 '[
   {"title": "Proprietary Trading Firms Adapt to New Volatility Regime", "sentiment": "neutral", "timestamp": "2025-12-09T14:45:00Z", "source": "Trading Technology"},
   {"title": "Systematic Strategies Show Mixed Performance in Q4", "sentiment": "neutral", "timestamp": "2025-12-09T13:30:00Z", "source": "Bloomberg"},
   {"title": "High-Frequency Trading Volumes Surge Amid Market Swings", "sentiment": "positive", "timestamp": "2025-12-09T12:15:00Z", "source": "WSJ Markets"},
   {"title": "Trend Following Strategies Face Challenging Environment", "sentiment": "negative", "timestamp": "2025-12-09T11:00:00Z", "source": "Financial Times"},
   {"title": "Prop Trading Desks Reassess Risk Parameters", "sentiment": "neutral", "timestamp": "2025-12-09T09:45:00Z", "source": "Markets Media"}
 ]'::jsonb,
 NOW() - INTERVAL '10 minutes'),

('OLYMPUS_VENTURES_024', 'MEDIUM', -0.15,
 '[
   {"title": "Private Equity Markets Remain Robust Despite FX Volatility", "sentiment": "positive", "timestamp": "2025-12-09T14:00:00Z", "source": "PE Hub Europe"},
   {"title": "European VC Activity Shows Steady Growth", "sentiment": "positive", "timestamp": "2025-12-09T13:00:00Z", "source": "Sifted"},
   {"title": "Currency Hedging Becomes Standard for Cross-Border Deals", "sentiment": "neutral", "timestamp": "2025-12-09T12:00:00Z", "source": "Financial Times"},
   {"title": "Tech Sector Valuations Hold Despite Market Uncertainty", "sentiment": "neutral", "timestamp": "2025-12-09T10:30:00Z", "source": "TechCrunch"},
   {"title": "Venture Capital Firms Maintain Investment Pace", "sentiment": "positive", "timestamp": "2025-12-09T09:00:00Z", "source": "Bloomberg"}
 ]'::jsonb,
 NOW() - INTERVAL '18 minutes'),

('QUANTUM_FINANCE_015', 'MEDIUM', -0.30,
 '[
   {"title": "Investment Banks Navigate Complex Hedging Environment", "sentiment": "negative", "timestamp": "2025-12-09T08:45:00Z", "source": "Financial Times Asia"},
   {"title": "Asian Financial Institutions Face FX Risk Management Challenges", "sentiment": "negative", "timestamp": "2025-12-09T07:30:00Z", "source": "Reuters"},
   {"title": "Regulatory Focus on Currency Risk Intensifies", "sentiment": "neutral", "timestamp": "2025-12-09T06:15:00Z", "source": "Central Banking"},
   {"title": "Banks Enhance FX Trading Infrastructure Amid Volatility", "sentiment": "neutral", "timestamp": "2025-12-09T05:00:00Z", "source": "Bloomberg"},
   {"title": "Cross-Currency Swap Spreads Widen in Asian Markets", "sentiment": "negative", "timestamp": "2025-12-09T03:45:00Z", "source": "IFR Asia"}
 ]'::jsonb,
 NOW() - INTERVAL '9 minutes'),

('VANGUARD_MARKETS_078', 'MEDIUM', -0.20,
 '[
   {"title": "Market Makers Benefit from Increased Trading Volumes", "sentiment": "positive", "timestamp": "2025-12-09T15:00:00Z", "source": "Trading Strategy"},
   {"title": "FX Liquidity Providers See Opportunity in Volatility", "sentiment": "positive", "timestamp": "2025-12-09T14:15:00Z", "source": "FX Week"},
   {"title": "European Market Making Firms Expand Operations", "sentiment": "positive", "timestamp": "2025-12-09T13:00:00Z", "source": "Bloomberg"},
   {"title": "Bid-Ask Spreads Normalize After Recent Widening", "sentiment": "neutral", "timestamp": "2025-12-09T11:30:00Z", "source": "Financial Times"},
   {"title": "Systematic Market Makers Adjust Algorithms for New Volatility", "sentiment": "neutral", "timestamp": "2025-12-09T10:00:00Z", "source": "Markets Media"}
 ]'::jsonb,
 NOW() - INTERVAL '20 minutes'),

-- Low switch probability clients (LOW media pressure)
('CORNERSTONE_INV_033', 'LOW', 0.12,
 '[
   {"title": "Long-Term Investment Strategies Weather Market Turbulence", "sentiment": "positive", "timestamp": "2025-12-09T14:30:00Z", "source": "Investment News"},
   {"title": "Patient Capital Approach Pays Off for Asset Managers", "sentiment": "positive", "timestamp": "2025-12-09T13:15:00Z", "source": "Institutional Investor"},
   {"title": "North American Funds Show Resilience in Q4", "sentiment": "positive", "timestamp": "2025-12-09T12:00:00Z", "source": "Pensions & Investments"},
   {"title": "Diversification Benefits Evident in Market Volatility", "sentiment": "positive", "timestamp": "2025-12-09T10:45:00Z", "source": "Financial Times"},
   {"title": "Conservative Strategies Outperform in Risk-Off Environment", "sentiment": "positive", "timestamp": "2025-12-09T09:30:00Z", "source": "Bloomberg"}
 ]'::jsonb,
 NOW() - INTERVAL '4 minutes'),

('HORIZON_GLOBAL_056', 'LOW', 0.08,
 '[
   {"title": "Global Macro Strategies Find Balance Amid Uncertainty", "sentiment": "positive", "timestamp": "2025-12-09T15:15:00Z", "source": "Hedge Fund Journal"},
   {"title": "European Hedge Funds Demonstrate Risk Management Excellence", "sentiment": "positive", "timestamp": "2025-12-09T14:00:00Z", "source": "Bloomberg"},
   {"title": "Mean Reversion Strategies Prove Effective in Choppy Markets", "sentiment": "positive", "timestamp": "2025-12-09T12:45:00Z", "source": "Financial Times"},
   {"title": "Disciplined Approach Delivers Steady Returns", "sentiment": "positive", "timestamp": "2025-12-09T11:30:00Z", "source": "AsiaHedge"},
   {"title": "Sophisticated Hedging Protects Portfolio Values", "sentiment": "positive", "timestamp": "2025-12-09T10:15:00Z", "source": "Fund Strategy"}
 ]'::jsonb,
 NOW() - INTERVAL '11 minutes'),

('STERLING_FX_041', 'LOW', 0.15,
 '[
   {"title": "Specialized FX Firms Thrive in Volatile Environment", "sentiment": "positive", "timestamp": "2025-12-09T15:30:00Z", "source": "FX Week"},
   {"title": "Sterling Shows Resilience Against Major Currencies", "sentiment": "positive", "timestamp": "2025-12-09T14:15:00Z", "source": "Reuters"},
   {"title": "European FX Trading Volumes Remain Healthy", "sentiment": "positive", "timestamp": "2025-12-09T13:00:00Z", "source": "Bloomberg"},
   {"title": "UK-Based Traders Navigate Brexit Transition Successfully", "sentiment": "positive", "timestamp": "2025-12-09T11:45:00Z", "source": "Financial Times"},
   {"title": "FX Hedging Solutions in High Demand", "sentiment": "positive", "timestamp": "2025-12-09T10:30:00Z", "source": "The Treasurer"}
 ]'::jsonb,
 NOW() - INTERVAL '14 minutes'),

('ECLIPSE_PARTNERS_092', 'LOW', 0.18,
 '[
   {"title": "Proprietary Trading Firms Post Strong Q4 Results", "sentiment": "positive", "timestamp": "2025-12-09T15:45:00Z", "source": "Traders Magazine"},
   {"title": "European Prop Trading Sector Shows Robust Growth", "sentiment": "positive", "timestamp": "2025-12-09T14:30:00Z", "source": "Bloomberg"},
   {"title": "Advanced Risk Models Protect Trading Capital", "sentiment": "positive", "timestamp": "2025-12-09T13:15:00Z", "source": "Risk.net"},
   {"title": "Technology Investment Pays Off for Trading Firms", "sentiment": "positive", "timestamp": "2025-12-09T12:00:00Z", "source": "Markets Media"},
   {"title": "Volatility Creates Opportunities for Nimble Traders", "sentiment": "positive", "timestamp": "2025-12-09T10:45:00Z", "source": "Financial Times"}
 ]'::jsonb,
 NOW() - INTERVAL '22 minutes'),

('PINNACLE_WEALTH_064', 'LOW', 0.10,
 '[
   {"title": "Wealth Management Clients Benefit from Stable FX Strategies", "sentiment": "positive", "timestamp": "2025-12-09T14:45:00Z", "source": "Wealth Professional"},
   {"title": "High-Net-Worth Investors Maintain Confidence", "sentiment": "positive", "timestamp": "2025-12-09T13:30:00Z", "source": "Private Banker International"},
   {"title": "Comprehensive Hedging Protects Client Portfolios", "sentiment": "positive", "timestamp": "2025-12-09T12:15:00Z", "source": "Family Wealth Report"},
   {"title": "North American Wealth Managers Lead in Risk Management", "sentiment": "positive", "timestamp": "2025-12-09T11:00:00Z", "source": "Institutional Investor"},
   {"title": "Client Retention Rates Reach Record Highs", "sentiment": "positive", "timestamp": "2025-12-09T09:45:00Z", "source": "InvestmentNews"}
 ]'::jsonb,
 NOW() - INTERVAL '16 minutes'),

('NEXUS_CAPITAL_017', 'LOW', 0.14,
 '[
   {"title": "Asian Venture Capital Shows Strong Performance", "sentiment": "positive", "timestamp": "2025-12-09T08:30:00Z", "source": "Tech in Asia"},
   {"title": "Cross-Border VC Deals Accelerate Despite Currency Volatility", "sentiment": "positive", "timestamp": "2025-12-09T07:15:00Z", "source": "Bloomberg"},
   {"title": "Regional Tech Startups Attract Record Funding", "sentiment": "positive", "timestamp": "2025-12-09T06:00:00Z", "source": "DealStreetAsia"},
   {"title": "Currency Hedging Strategies Protect VC Returns", "sentiment": "positive", "timestamp": "2025-12-09T04:45:00Z", "source": "PE Hub"},
   {"title": "Asian Innovation Centers Draw Global Capital", "sentiment": "positive", "timestamp": "2025-12-09T03:30:00Z", "source": "Financial Times Asia"}
 ]'::jsonb,
 NOW() - INTERVAL '13 minutes'),

('ROCKFORD_TRUST_088', 'LOW', 0.09,
 '[
   {"title": "Trust Services Sector Shows Stability Amid Market Volatility", "sentiment": "positive", "timestamp": "2025-12-09T08:45:00Z", "source": "Trusts & Estates"},
   {"title": "Conservative Investment Approach Protects Trust Assets", "sentiment": "positive", "timestamp": "2025-12-09T07:30:00Z", "source": "Asian Banker"},
   {"title": "Fiduciary Standards Ensure Sound Risk Management", "sentiment": "positive", "timestamp": "2025-12-09T06:15:00Z", "source": "International Trust"},
   {"title": "Long-Term Focus Delivers Consistent Returns", "sentiment": "positive", "timestamp": "2025-12-09T05:00:00Z", "source": "WealthBriefing Asia"},
   {"title": "Client Satisfaction Scores Remain High for Trust Services", "sentiment": "positive", "timestamp": "2025-12-09T03:45:00Z", "source": "Family Office Magazine"}
 ]'::jsonb,
 NOW() - INTERVAL '19 minutes'),

('SUMMIT_ADVISORS_051', 'LOW', 0.11,
 '[
   {"title": "Financial Advisory Services in High Demand", "sentiment": "positive", "timestamp": "2025-12-09T15:00:00Z", "source": "Financial Advisor Magazine"},
   {"title": "European Advisory Firms Expand Client Base", "sentiment": "positive", "timestamp": "2025-12-09T13:45:00Z", "source": "Citywire"},
   {"title": "Comprehensive Planning Helps Clients Navigate Uncertainty", "sentiment": "positive", "timestamp": "2025-12-09T12:30:00Z", "source": "Financial Planning"},
   {"title": "Trend-Setting Strategies Deliver Alpha for Clients", "sentiment": "positive", "timestamp": "2025-12-09T11:15:00Z", "source": "Professional Adviser"},
   {"title": "Advisory Excellence Recognized by Industry Awards", "sentiment": "positive", "timestamp": "2025-12-09T10:00:00Z", "source": "Money Management"}
 ]'::jsonb,
 NOW() - INTERVAL '17 minutes')

ON CONFLICT DO NOTHING;
