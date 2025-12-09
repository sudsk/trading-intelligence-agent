-- Switch probability history
CREATE TABLE switch_probability_history (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50),  -- ← Remove REFERENCES clients(client_id)
    switch_prob DECIMAL(4, 3) NOT NULL,
    confidence DECIMAL(4, 3),
    segment VARCHAR(50),
    drivers JSONB,
    risk_flags JSONB,
    computed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_switch_prob_client_computed ON switch_probability_history(client_id, computed_at DESC);

-- Alerts table
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50),  -- ← Remove REFERENCES clients(client_id)
    alert_type VARCHAR(50) NOT NULL,
    old_switch_prob DECIMAL(4, 3),
    new_switch_prob DECIMAL(4, 3),
    reason TEXT,
    severity VARCHAR(20),
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_alerts_client_created ON alerts(client_id, created_at DESC);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);

-- Actions table
CREATE TABLE actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(50),  -- ← Remove REFERENCES clients(client_id)
    action_type VARCHAR(50) NOT NULL,
    product VARCHAR(100),
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    outcome VARCHAR(20),
    outcome_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_actions_client_created ON actions(client_id, created_at DESC);
CREATE INDEX idx_actions_status ON actions(status);

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
    analyzed_at TIMESTAMP NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

CREATE INDEX idx_media_client_time ON media_analysis(client_id, analyzed_at DESC);

-- NBA recommendations
CREATE TABLE IF NOT EXISTS nba_recommendations (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    recommendations JSONB,
    generated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

CREATE INDEX idx_recs_client_time ON nba_recommendations(client_id, generated_at DESC);

-- Sample switch probability data for 20 demo clients
INSERT INTO switch_probability_history (client_id, switch_prob, confidence, segment, drivers, risk_flags, computed_at)
VALUES 
  -- High switch probability (0.60-0.85) - Need attention
  ('ACME_FX_023', 0.720, 0.850, 'Trend Follower', 
   '{"pattern_break": 0.22, "changepoint": 0.20, "momentum_flip": 0.15, "regime_flip": 0.10, "drift": 0.05}',
   '["sustained_deviation", "volatility_spike"]',
   NOW() - INTERVAL '5 minutes'),
   
  ('ATLAS_BOND_012', 0.680, 0.820, 'Trend Setter',
   '{"pattern_break": 0.20, "changepoint": 0.18, "momentum_flip": 0.15, "regime_flip": 0.10, "drift": 0.05}',
   '["sustained_deviation"]',
   NOW() - INTERVAL '2 minutes'),
   
  ('NOVA_MACRO_045', 0.760, 0.880, 'Mean Reverter',
   '{"pattern_break": 0.25, "changepoint": 0.22, "momentum_flip": 0.15, "regime_flip": 0.09, "drift": 0.05}',
   '["sustained_deviation", "volatility_spike", "position_concentration"]',
   NOW() - INTERVAL '8 minutes'),
   
  ('PHOENIX_CAPITAL_031', 0.810, 0.900, 'Trend Follower',
   '{"pattern_break": 0.28, "changepoint": 0.23, "momentum_flip": 0.18, "regime_flip": 0.08, "drift": 0.04}',
   '["sustained_deviation", "volatility_spike", "position_concentration"]',
   NOW() - INTERVAL '12 minutes'),
   
  ('SENTINEL_ASSETS_067', 0.650, 0.800, 'Hedger',
   '{"pattern_break": 0.18, "changepoint": 0.20, "momentum_flip": 0.14, "regime_flip": 0.08, "drift": 0.05}',
   '["sustained_deviation", "position_concentration"]',
   NOW() - INTERVAL '6 minutes'),
  
  -- Medium switch probability (0.35-0.59) - Monitor
  ('ZEUS_COMM_019', 0.480, 0.720, 'Mean Reverter',
   '{"pattern_break": 0.12, "changepoint": 0.15, "momentum_flip": 0.10, "regime_flip": 0.07, "drift": 0.04}',
   '[]',
   NOW() - INTERVAL '3 minutes'),
   
  ('TITAN_EQ_008', 0.420, 0.680, 'Hedger',
   '{"pattern_break": 0.10, "changepoint": 0.12, "momentum_flip": 0.10, "regime_flip": 0.06, "drift": 0.04}',
   '[]',
   NOW() - INTERVAL '7 minutes'),
   
  ('MERIDIAN_FUND_052', 0.520, 0.750, 'Trend Setter',
   '{"pattern_break": 0.15, "changepoint": 0.14, "momentum_flip": 0.12, "regime_flip": 0.07, "drift": 0.04}',
   '["sustained_deviation"]',
   NOW() - INTERVAL '15 minutes'),
   
  ('APEX_TRADING_089', 0.460, 0.700, 'Trend Follower',
   '{"pattern_break": 0.12, "changepoint": 0.13, "momentum_flip": 0.11, "regime_flip": 0.06, "drift": 0.04}',
   '[]',
   NOW() - INTERVAL '10 minutes'),
   
  ('OLYMPUS_VENTURES_024', 0.390, 0.650, 'Mean Reverter',
   '{"pattern_break": 0.09, "changepoint": 0.11, "momentum_flip": 0.09, "regime_flip": 0.06, "drift": 0.04}',
   '[]',
   NOW() - INTERVAL '18 minutes'),
   
  ('QUANTUM_FINANCE_015', 0.540, 0.770, 'Hedger',
   '{"pattern_break": 0.14, "changepoint": 0.15, "momentum_flip": 0.12, "regime_flip": 0.08, "drift": 0.05}',
   '["sustained_deviation"]',
   NOW() - INTERVAL '9 minutes'),
   
  ('VANGUARD_MARKETS_078', 0.440, 0.690, 'Trend Setter',
   '{"pattern_break": 0.11, "changepoint": 0.12, "momentum_flip": 0.11, "regime_flip": 0.06, "drift": 0.04}',
   '[]',
   NOW() - INTERVAL '20 minutes'),
  
  -- Low switch probability (0.15-0.34) - Stable
  ('CORNERSTONE_INV_033', 0.280, 0.620, 'Trend Follower',
   '{"pattern_break": 0.06, "changepoint": 0.08, "momentum_flip": 0.07, "regime_flip": 0.04, "drift": 0.03}',
   '[]',
   NOW() - INTERVAL '4 minutes'),
   
  ('HORIZON_GLOBAL_056', 0.310, 0.640, 'Mean Reverter',
   '{"pattern_break": 0.08, "changepoint": 0.09, "momentum_flip": 0.07, "regime_flip": 0.04, "drift": 0.03}',
   '[]',
   NOW() - INTERVAL '11 minutes'),
   
  ('STERLING_FX_041', 0.240, 0.590, 'Hedger',
   '{"pattern_break": 0.05, "changepoint": 0.07, "momentum_flip": 0.06, "regime_flip": 0.04, "drift": 0.02}',
   '[]',
   NOW() - INTERVAL '14 minutes'),
   
  ('ECLIPSE_PARTNERS_092', 0.190, 0.550, 'Trend Setter',
   '{"pattern_break": 0.04, "changepoint": 0.05, "momentum_flip": 0.05, "regime_flip": 0.03, "drift": 0.02}',
   '[]',
   NOW() - INTERVAL '22 minutes'),
   
  ('PINNACLE_WEALTH_064', 0.330, 0.660, 'Trend Follower',
   '{"pattern_break": 0.08, "changepoint": 0.09, "momentum_flip": 0.08, "regime_flip": 0.05, "drift": 0.03}',
   '[]',
   NOW() - INTERVAL '16 minutes'),
   
  ('NEXUS_CAPITAL_017', 0.270, 0.610, 'Mean Reverter',
   '{"pattern_break": 0.06, "changepoint": 0.08, "momentum_flip": 0.07, "regime_flip": 0.04, "drift": 0.02}',
   '[]',
   NOW() - INTERVAL '13 minutes'),
   
  ('ROCKFORD_TRUST_088', 0.220, 0.580, 'Hedger',
   '{"pattern_break": 0.05, "changepoint": 0.06, "momentum_flip": 0.06, "regime_flip": 0.03, "drift": 0.02}',
   '[]',
   NOW() - INTERVAL '19 minutes'),
   
  ('SUMMIT_ADVISORS_051', 0.290, 0.630, 'Trend Setter',
   '{"pattern_break": 0.07, "changepoint": 0.08, "momentum_flip": 0.07, "regime_flip": 0.04, "drift": 0.03}',
   '[]',
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


-- Sample Alerts/Insights for Demo (last 7 days)
INSERT INTO alerts (client_id, alert_type, severity, old_switch_prob, new_switch_prob, reason, acknowledged, created_at) VALUES
  -- High priority alerts (recent)
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
