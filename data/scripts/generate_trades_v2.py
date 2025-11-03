"""
Enhanced trade generator with SEGMENT-SPECIFIC PATTERNS
Creates realistic trading behavior for each segment type
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


def get_market_data(conn, instrument, start_date):
    """Fetch market prices for pattern generation"""
    query = """
        SELECT timestamp, close 
        FROM market_bars 
        WHERE instrument = %s AND timestamp >= %s
        ORDER BY timestamp
    """
    df = pd.read_sql(query, conn, params=(instrument, start_date))
    return df


def generate_trend_follower_trades(client_id, instrument, market_df, months=6):
    """
    Trend Follower pattern:
    - High momentum alignment (buys when rising, sells when falling)
    - Short holding periods (2-5 days)
    - Aggressive market orders
    - Directional bias
    """
    if len(market_df) < 10:
        return []
    
    market_df = market_df.copy()
    market_df['return'] = market_df['close'].pct_change()
    market_df['trend'] = market_df['return'].rolling(5).mean()  # 5-day trend
    
    trades = []
    trade_id = 1
    position = 0
    entry_time = None
    
    for idx, row in market_df.iterrows():
        timestamp = row['timestamp']
        price = row['close']
        trend = row['trend']
        
        if pd.isna(trend):
            continue
        
        # Follow the trend
        if trend > 0.001 and position <= 0:
            # Buy on uptrend
            quantity = int(np.random.uniform(50000, 150000))
            trades.append({
                'trade_id': f"{client_id}_TF_{trade_id}",
                'client_id': client_id,
                'instrument': instrument,
                'side': 'BUY',
                'quantity': quantity,
                'price': price * np.random.uniform(0.9995, 1.0005),  # Slight slippage
                'timestamp': timestamp,
                'order_type': 'MARKET' if np.random.random() < 0.7 else 'LIMIT',  # 70% aggressive
                'venue': np.random.choice(['EBS', 'CME', 'LMAX'])
            })
            position += quantity
            entry_time = timestamp
            trade_id += 1
            
        elif trend < -0.001 and position > 0:
            # Sell on downtrend (close position)
            holding_days = (timestamp - entry_time).days if entry_time else 999
            if holding_days >= 2:  # Min 2-day hold
                trades.append({
                    'trade_id': f"{client_id}_TF_{trade_id}",
                    'client_id': client_id,
                    'instrument': instrument,
                    'side': 'SELL',
                    'quantity': position,
                    'price': price * np.random.uniform(0.9995, 1.0005),
                    'timestamp': timestamp,
                    'order_type': 'LIMIT',
                    'venue': np.random.choice(['EBS', 'CME', 'LMAX'])
                })
                position = 0
                entry_time = None
                trade_id += 1
    
    return trades


def generate_mean_reverter_trades(client_id, instrument, market_df, months=6):
    """
    Mean Reverter pattern:
    - Contrarian (buys dips, sells rallies)
    - Very short holds (1-3 days)
    - Frequent flips
    - Range-bound
    """
    if len(market_df) < 20:
        return []
    
    market_df = market_df.copy()
    market_df['ma20'] = market_df['close'].rolling(20).mean()
    market_df['deviation'] = (market_df['close'] - market_df['ma20']) / market_df['ma20']
    
    trades = []
    trade_id = 1
    position = 0
    entry_time = None
    
    for idx, row in market_df.iterrows():
        timestamp = row['timestamp']
        price = row['close']
        deviation = row['deviation']
        
        if pd.isna(deviation):
            continue
        
        # Buy when oversold (below mean)
        if deviation < -0.01 and position <= 0:
            quantity = int(np.random.uniform(30000, 100000))
            trades.append({
                'trade_id': f"{client_id}_MR_{trade_id}",
                'client_id': client_id,
                'instrument': instrument,
                'side': 'BUY',
                'quantity': quantity,
                'price': price * np.random.uniform(0.9998, 1.0002),
                'timestamp': timestamp,
                'order_type': 'LIMIT',  # Patient limit orders
                'venue': np.random.choice(['EBS', 'CME'])
            })
            position = quantity
            entry_time = timestamp
            trade_id += 1
            
        # Sell when overbought (above mean)
        elif deviation > 0.01 and position > 0:
            holding_days = (timestamp - entry_time).days if entry_time else 0
            if holding_days >= 1:  # Very short holds
                trades.append({
                    'trade_id': f"{client_id}_MR_{trade_id}",
                    'client_id': client_id,
                    'instrument': instrument,
                    'side': 'SELL',
                    'quantity': position,
                    'price': price * np.random.uniform(0.9998, 1.0002),
                    'timestamp': timestamp,
                    'order_type': 'LIMIT',
                    'venue': np.random.choice(['EBS', 'CME'])
                })
                position = 0
                entry_time = None
                trade_id += 1
    
    return trades


def generate_hedger_trades(client_id, instrument, market_df, months=6):
    """
    Hedger pattern:
    - Long holding periods (30-90 days)
    - Defensive positioning
    - Low frequency
    - Mostly sell-side (hedging longs)
    """
    trades = []
    trade_id = 1
    
    # Hedgers trade infrequently
    num_trades = np.random.randint(5, 15)
    
    selected_dates = np.random.choice(len(market_df), num_trades, replace=False)
    selected_dates.sort()
    
    position = 0
    entry_time = None
    
    for idx in selected_dates:
        row = market_df.iloc[idx]
        timestamp = row['timestamp']
        price = row['close']
        
        if position == 0:
            # Enter hedge (usually sell)
            quantity = int(np.random.uniform(100000, 300000))
            side = 'SELL' if np.random.random() < 0.7 else 'BUY'  # 70% sell-side
            
            trades.append({
                'trade_id': f"{client_id}_HD_{trade_id}",
                'client_id': client_id,
                'instrument': instrument,
                'side': side,
                'quantity': quantity,
                'price': price * np.random.uniform(0.9995, 1.0005),
                'timestamp': timestamp,
                'order_type': 'LIMIT',  # Patient
                'venue': np.random.choice(['EBS', 'CME'])
            })
            position = quantity if side == 'BUY' else -quantity
            entry_time = timestamp
            trade_id += 1
            
        else:
            # Close hedge (after long hold)
            holding_days = (timestamp - entry_time).days if entry_time else 0
            if holding_days >= 30:  # Long holds
                side = 'BUY' if position < 0 else 'SELL'
                trades.append({
                    'trade_id': f"{client_id}_HD_{trade_id}",
                    'client_id': client_id,
                    'instrument': instrument,
                    'side': side,
                    'quantity': abs(position),
                    'price': price * np.random.uniform(0.9995, 1.0005),
                    'timestamp': timestamp,
                    'order_type': 'LIMIT',
                    'venue': np.random.choice(['EBS', 'CME'])
                })
                position = 0
                entry_time = None
                trade_id += 1
    
    return trades


def generate_trend_setter_trades(client_id, instrument, market_df, months=6):
    """
    Trend Setter pattern:
    - Anticipatory (leads market, not follows)
    - Contrarian timing but directional conviction
    - Medium holds (5-15 days)
    - High alpha
    """
    if len(market_df) < 20:
        return []
    
    market_df = market_df.copy()
    market_df['return'] = market_df['close'].pct_change()
    market_df['future_return'] = market_df['return'].shift(-5)  # 5-day forward return
    
    trades = []
    trade_id = 1
    position = 0
    entry_time = None
    
    for idx, row in market_df.iterrows():
        timestamp = row['timestamp']
        price = row['close']
        current_return = row['return']
        future_return = row['future_return']
        
        if pd.isna(future_return) or pd.isna(current_return):
            continue
        
        # Anticipate reversals (buy when down but will recover)
        if current_return < -0.005 and future_return > 0.002 and position <= 0:
            quantity = int(np.random.uniform(80000, 200000))
            trades.append({
                'trade_id': f"{client_id}_TS_{trade_id}",
                'client_id': client_id,
                'instrument': instrument,
                'side': 'BUY',
                'quantity': quantity,
                'price': price * np.random.uniform(0.9995, 1.0005),
                'timestamp': timestamp,
                'order_type': 'MARKET' if np.random.random() < 0.8 else 'LIMIT',  # Very aggressive
                'venue': np.random.choice(['EBS', 'CME', 'LMAX'])
            })
            position = quantity
            entry_time = timestamp
            trade_id += 1
            
        # Exit when anticipated move complete
        elif position > 0:
            holding_days = (timestamp - entry_time).days if entry_time else 0
            if holding_days >= 5 and current_return > 0.003:  # Profit target hit
                trades.append({
                    'trade_id': f"{client_id}_TS_{trade_id}",
                    'client_id': client_id,
                    'instrument': instrument,
                    'side': 'SELL',
                    'quantity': position,
                    'price': price * np.random.uniform(0.9995, 1.0005),
                    'timestamp': timestamp,
                    'order_type': 'LIMIT',
                    'venue': np.random.choice(['EBS', 'CME', 'LMAX'])
                })
                position = 0
                entry_time = None
                trade_id += 1
    
    return trades


def main():
    """Generate segment-specific trades for all clients"""
    print("=" * 60)
    print("📈 Generating Segment-Specific Trades (v2)")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        print("✅ Connected to database\n")
        
        # Get all clients with segments
        cursor = conn.cursor()
        cursor.execute("""
            SELECT client_id, segment, primary_exposure 
            FROM clients 
            WHERE segment IS NOT NULL
            ORDER BY client_id
        """)
        clients = cursor.fetchall()
        
        print(f"Found {len(clients)} clients\n")
        
        all_trades = []
        start_date = datetime.now() - timedelta(days=180)
        
        for i, (client_id, segment, primary_exposure) in enumerate(clients, 1):
            print(f"[{i}/{len(clients)}] {client_id} ({segment})...", end=' ')
            
            # Get market data
            market_df = get_market_data(conn, primary_exposure, start_date)
            
            if len(market_df) < 10:
                print("⏭️  (insufficient market data)")
                continue
            
            # Generate trades based on segment
            if segment == 'Trend Follower':
                trades = generate_trend_follower_trades(client_id, primary_exposure, market_df)
            elif segment == 'Mean Reverter':
                trades = generate_mean_reverter_trades(client_id, primary_exposure, market_df)
            elif segment == 'Hedger':
                trades = generate_hedger_trades(client_id, primary_exposure, market_df)
            elif segment == 'Trend Setter':
                trades = generate_trend_setter_trades(client_id, primary_exposure, market_df)
            else:
                print("⏭️  (unknown segment)")
                continue
            
            all_trades.extend(trades)
            print(f"✅ ({len(trades)} trades)")
        
        # Insert trades
        if all_trades:
            print(f"\n💾 Inserting {len(all_trades)} trades...")
            
            trade_tuples = [
                (
                    t['trade_id'],
                    t['client_id'],
                    t['instrument'],
                    t['side'],
                    t['quantity'],
                    t['price'],
                    t['timestamp'],
                    t['order_type'],
                    t['venue']
                )
                for t in all_trades
            ]
            
            cursor = conn.cursor()
            
            # Insert in batches
            batch_size = 5000
            for i in range(0, len(trade_tuples), batch_size):
                batch = trade_tuples[i:i + batch_size]
                execute_batch(cursor, """
                    INSERT INTO trades 
                    (trade_id, client_id, instrument, side, quantity, price, timestamp, order_type, venue)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trade_id) DO NOTHING
                """, batch, page_size=1000)
                conn.commit()
                print(f"  Batch {i//batch_size + 1}/{(len(trade_tuples)-1)//batch_size + 1} inserted")
            
            print("✅ Trades inserted successfully")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Segment-specific trade generation complete!")
        print("=" * 60)
        print("\n💡 These trades show realistic patterns:")
        print("   - Trend Followers: High momentum, short holds")
        print("   - Mean Reverters: Contrarian, very short holds")
        print("   - Hedgers: Long holds, defensive")
        print("   - Trend Setters: Anticipatory, medium holds")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
