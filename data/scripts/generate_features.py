"""
Generate trading features from trade history
Computes momentum betas, holding periods, turnover, etc.
"""
import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'trading_intelligence'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def compute_momentum_beta(trades_df, market_df, window_days):
    """
    Compute momentum beta over window
    Measures how aligned trades are with market direction
    """
    if len(trades_df) < 10:
        return 0.0
    
    # Aggregate daily position changes
    trades_df['date'] = pd.to_datetime(trades_df['timestamp']).dt.date
    daily_flow = trades_df.groupby('date').apply(
        lambda x: (x[x['side'] == 'BUY']['quantity'].sum() - 
                   x[x['side'] == 'SELL']['quantity'].sum())
    ).reset_index()
    daily_flow.columns = ['date', 'net_flow']
    
    # Get market returns
    market_df = market_df.sort_values('timestamp')
    market_df['return'] = market_df['close'].pct_change()
    market_df['date'] = pd.to_datetime(market_df['timestamp']).dt.date
    
    # Merge and compute correlation
    merged = pd.merge(daily_flow, market_df[['date', 'return']], on='date')
    
    if len(merged) < 5:
        return 0.0
    
    # Correlation approximates beta
    try:
        beta = np.corrcoef(merged['net_flow'], merged['return'])[0, 1]
        return round(float(beta) if not np.isnan(beta) else 0.0, 4)
    except:
        return 0.0


def compute_holding_period(trades_df):
    """
    Compute average holding period in days
    """
    if len(trades_df) < 2:
        return 0.0
    
    # Sort by instrument and time
    trades_df = trades_df.sort_values(['instrument', 'timestamp'])
    
    holding_periods = []
    
    for instrument in trades_df['instrument'].unique():
        inst_trades = trades_df[trades_df['instrument'] == instrument].copy()
        
        # Track position and entry time
        position = 0
        entry_time = None
        
        for _, trade in inst_trades.iterrows():
            if trade['side'] == 'BUY':
                if position <= 0:  # Opening or flipping
                    entry_time = trade['timestamp']
                position += trade['quantity']
            else:  # SELL
                if position > 0 and entry_time is not None:
                    # Closing position
                    hold_time = (trade['timestamp'] - entry_time).total_seconds() / 86400
                    holding_periods.append(hold_time)
                    entry_time = None
                position -= trade['quantity']
    
    if not holding_periods:
        return 1.0  # Default
    
    return round(np.mean(holding_periods), 2)


def compute_turnover(trades_df, positions_df):
    """
    Compute turnover ratio
    Trading volume / average position size
    """
    if len(trades_df) == 0 or len(positions_df) == 0:
        return 0.0
    
    # Total traded volume (absolute)
    total_volume = trades_df['quantity'].abs().sum()
    
    # Average position size
    avg_position = positions_df['gross_position'].mean()
    
    if avg_position == 0:
        return 0.0
    
    # Annualized turnover
    days = (trades_df['timestamp'].max() - trades_df['timestamp'].min()).days + 1
    annual_factor = 365 / max(days, 1)
    
    turnover = (total_volume / avg_position) * annual_factor / 365  # Daily turnover
    
    return round(min(turnover, 9.9999), 4)


def compute_aggressiveness(trades_df):
    """
    Compute aggressiveness ratio
    Market orders / Total orders
    """
    if len(trades_df) == 0:
        return 0.0
    
    market_orders = (trades_df['order_type'] == 'MARKET').sum()
    total_orders = len(trades_df)
    
    return round(market_orders / total_orders, 4)


def compute_lead_lag_alpha(trades_df, market_df):
    """
    Compute lead/lag alpha
    Positive = leading (anticipatory), Negative = lagging (following)
    """
    if len(trades_df) < 10:
        return 0.0
    
    # Client daily net flow
    trades_df['date'] = pd.to_datetime(trades_df['timestamp']).dt.date
    daily_flow = trades_df.groupby('date').apply(
        lambda x: (x[x['side'] == 'BUY']['quantity'].sum() - 
                   x[x['side'] == 'SELL']['quantity'].sum())
    ).reset_index()
    daily_flow.columns = ['date', 'net_flow']
    
    # Market returns
    market_df = market_df.sort_values('timestamp')
    market_df['return'] = market_df['close'].pct_change()
    market_df['return_next'] = market_df['return'].shift(-1)  # Future return
    market_df['date'] = pd.to_datetime(market_df['timestamp']).dt.date
    
    # Merge
    merged = pd.merge(daily_flow, market_df[['date', 'return', 'return_next']], on='date')
    
    if len(merged) < 5:
        return 0.0
    
    # Alpha = correlation(client_flow_today, market_return_tomorrow)
    try:
        alpha = np.corrcoef(merged['net_flow'], merged['return_next'])[0, 1]
        return round(float(alpha) if not np.isnan(alpha) else 0.0, 4)
    except:
        return 0.0


def compute_exposure_concentration(positions_df):
    """
    Compute exposure concentration as JSON
    """
    if len(positions_df) == 0:
        return {}
    
    total_exposure = positions_df['gross_position'].sum()
    
    if total_exposure == 0:
        return {}
    
    concentration = {}
    for _, pos in positions_df.iterrows():
        pct = round(pos['gross_position'] / total_exposure, 2)
        if pct > 0.05:  # Only include >5%
            concentration[pos['instrument']] = pct
    
    return concentration


def generate_features_for_client(client_id, conn):
    """Generate all features for a single client"""
    
    # Fetch trades (last 90 days)
    trades_query = """
        SELECT * FROM trades 
        WHERE client_id = %s 
        AND timestamp > %s
        ORDER BY timestamp
    """
    start_date = datetime.now() - timedelta(days=90)
    trades_df = pd.read_sql(trades_query, conn, params=(client_id, start_date))
    
    if len(trades_df) == 0:
        return None  # Skip clients with no trades
    
    # Fetch positions
    positions_query = "SELECT * FROM positions WHERE client_id = %s"
    positions_df = pd.read_sql(positions_query, conn, params=(client_id,))
    
    # Get primary instrument for market data
    cursor = conn.cursor()
    cursor.execute("SELECT primary_exposure FROM clients WHERE client_id = %s", (client_id,))
    primary_exposure = cursor.fetchone()
    primary_instrument = primary_exposure[0] if primary_exposure else 'EURUSD'
    
    # Fetch market data
    market_query = """
        SELECT * FROM market_bars 
        WHERE instrument = %s 
        AND timestamp > %s
        ORDER BY timestamp
    """
    market_df = pd.read_sql(market_query, conn, params=(primary_instrument, start_date))
    
    if len(market_df) == 0:
        # Use any available market data
        market_query = "SELECT * FROM market_bars ORDER BY timestamp LIMIT 100"
        market_df = pd.read_sql(market_query, conn)
    
    # Compute features
    features = {
        'client_id': client_id,
        'computed_at': datetime.now(),
        'momentum_beta_1d': compute_momentum_beta(trades_df, market_df, 1),
        'momentum_beta_5d': compute_momentum_beta(trades_df, market_df, 5),
        'momentum_beta_20d': compute_momentum_beta(trades_df, market_df, 20),
        'holding_period_avg': compute_holding_period(trades_df),
        'turnover': compute_turnover(trades_df, positions_df),
        'aggressiveness': compute_aggressiveness(trades_df),
        'lead_lag_alpha': compute_lead_lag_alpha(trades_df, market_df),
        'exposure_concentration': compute_exposure_concentration(positions_df)
    }
    
    return features


def main():
    """Generate features for all clients"""
    print("=" * 60)
    print("📊 Generating Trading Features")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        print("✅ Connected to database\n")
        
        # Get all clients
        cursor = conn.cursor()
        cursor.execute("SELECT client_id FROM clients ORDER BY client_id")
        client_ids = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(client_ids)} clients\n")
        
        features_list = []
        
        for i, client_id in enumerate(client_ids, 1):
            print(f"[{i}/{len(client_ids)}] Processing {client_id}...", end=' ')
            
            features = generate_features_for_client(client_id, conn)
            
            if features:
                features_list.append(features)
                print("✅")
            else:
                print("⏭️  (no trades)")
        
        # Insert features
        if features_list:
            print(f"\n💾 Inserting {len(features_list)} feature records...")
            
            cursor = conn.cursor()
            
            for features in features_list:
                cursor.execute("""
                    INSERT INTO features (
                        client_id, computed_at,
                        momentum_beta_1d, momentum_beta_5d, momentum_beta_20d,
                        holding_period_avg, turnover, aggressiveness,
                        lead_lag_alpha, exposure_concentration
                    ) VALUES (
                        %(client_id)s, %(computed_at)s,
                        %(momentum_beta_1d)s, %(momentum_beta_5d)s, %(momentum_beta_20d)s,
                        %(holding_period_avg)s, %(turnover)s, %(aggressiveness)s,
                        %(lead_lag_alpha)s, %(exposure_concentration)s::jsonb
                    )
                """, features)
            
            conn.commit()
            print("✅ Features inserted successfully")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Feature generation complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
