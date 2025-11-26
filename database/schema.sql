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
