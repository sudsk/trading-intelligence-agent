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
