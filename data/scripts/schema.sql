-- Trading Intelligence Database Schema

-- Clients table
CREATE TABLE clients (
    client_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    segment VARCHAR(50),
    rm VARCHAR(100),
    sector VARCHAR(100),
    primary_exposure VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clients_segment ON clients(segment);
CREATE INDEX idx_clients_rm ON clients(rm);

-- Trades table
CREATE TABLE trades (
    trade_id VARCHAR(50) PRIMARY KEY,
    client_id VARCHAR(50) REFERENCES clients(client_id),
    instrument VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(12, 4) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    order_type VARCHAR(20),
    venue VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_client_timestamp ON trades(client_id, timestamp DESC);
CREATE INDEX idx_trades_instrument ON trades(instrument);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);

-- Positions table
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) REFERENCES clients(client_id),
    instrument VARCHAR(20) NOT NULL,
    net_position DECIMAL(15, 2) NOT NULL,
    gross_position DECIMAL(15, 2),
    leverage DECIMAL(5, 2),
    unrealized_pnl DECIMAL(15, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_id, instrument)
);

CREATE INDEX idx_positions_client ON positions(client_id);

-- Features table (computed trading features)
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) REFERENCES clients(client_id),
    computed_at TIMESTAMP NOT NULL,
    momentum_beta_1d DECIMAL(8, 4),
    momentum_beta_5d DECIMAL(8, 4),
    momentum_beta_20d DECIMAL(8, 4),
    holding_period_avg DECIMAL(8, 2),
    turnover DECIMAL(8, 4),
    aggressiveness DECIMAL(8, 4),
    lead_lag_alpha DECIMAL(8, 4),
    exposure_concentration JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_features_client_computed ON features(client_id, computed_at DESC);

-- Headlines table
CREATE TABLE headlines (
    headline_id VARCHAR(50) PRIMARY KEY,
    instrument VARCHAR(20) NOT NULL,
    title TEXT NOT NULL,
    sentiment VARCHAR(20),
    sentiment_score DECIMAL(3, 2),
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50),
    topics TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_headlines_instrument_timestamp ON headlines(instrument, timestamp DESC);
CREATE INDEX idx_headlines_timestamp ON headlines(timestamp DESC);

-- Switch probability history
CREATE TABLE switch_probability_history (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50) REFERENCES clients(client_id),
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
    client_id VARCHAR(50) REFERENCES clients(client_id),
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
    client_id VARCHAR(50) REFERENCES clients(client_id),
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

-- Market bars table
CREATE TABLE market_bars (
    id SERIAL PRIMARY KEY,
    instrument VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(12, 4) NOT NULL,
    high DECIMAL(12, 4) NOT NULL,
    low DECIMAL(12, 4) NOT NULL,
    close DECIMAL(12, 4) NOT NULL,
    volume BIGINT,
    UNIQUE(instrument, timestamp)
);

CREATE INDEX idx_market_bars_instrument_timestamp ON market_bars(instrument, timestamp DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_actions_updated_at BEFORE UPDATE ON actions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
