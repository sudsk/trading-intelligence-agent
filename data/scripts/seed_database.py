"""
Generate and insert mock data directly into PostgreSQL database
"""
import psycopg2
from psycopg2.extras import execute_batch
import numpy as np
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'trading_intelligence'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)

def generate_and_insert_clients(conn, n=50):
    """Generate and insert clients"""
    print(f"\n📊 Generating {n} clients...")
    
    segments = ['Trend Follower', 'Mean Reverter', 'Hedger', 'Trend Setter']
    rms = ['Sarah Chen', 'Michael Torres', 'Emma Wilson', 'James Park', 'Lisa Anderson']
    exposures = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'CL', 'SPX']
    sectors = ['Financial Services', 'Energy', 'Technology', 'Commodities']
    
    clients = []
    np.random.seed(42)
    
    for i in range(n):
        client_id = f"{np.random.choice(['ACME', 'ZEUS', 'TITAN', 'NOVA', 'APEX'])}_{np.random.choice(['FX', 'COMM', 'EQ', 'RATES'])}_{str(i).zfill(3)}"
        
        clients.append((
            client_id,
            client_id,  # name
            np.random.choice(segments),
            np.random.choice(rms),
            np.random.choice(sectors),
            np.random.choice(exposures)
        ))
    
    cursor = conn.cursor()
    execute_batch(cursor, """
        INSERT INTO clients (client_id, name, segment, rm, sector, primary_exposure)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (client_id) DO NOTHING
    """, clients)
    conn.commit()
    
    print(f"✅ Inserted {len(clients)} clients")
    return [c[0] for c in clients]

def generate_and_insert_trades(conn, client_ids, trades_per_client=1000, months=6):
    """Generate and insert trades"""
    print(f"\n📈 Generating {trades_per_client} trades per client for {months} months...")
    
    instruments = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'CL', 'SPX']
    sides = ['BUY', 'SELL']
    order_types = ['MARKET', 'LIMIT']
    venues = ['EBS', 'CME', 'LMAX', 'ICE']
    
    trades = []
    trade_id = 1
    start_date = datetime.now() - timedelta(days=months * 30)
    
    np.random.seed(42)
    
    for client_id in client_ids:
        for _ in range(trades_per_client):
            timestamp = start_date + timedelta(
                days=np.random.randint(0, months * 30),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            
            trades.append((
                f"TRD{str(trade_id).zfill(8)}",
                client_id,
                np.random.choice(instruments),
                np.random.choice(sides),
                int(np.random.uniform(1000, 100000)),
                round(np.random.uniform(1.0, 2000.0), 4),
                timestamp,
                np.random.choice(order_types),
                np.random.choice(venues)
            ))
            trade_id += 1
    
    cursor = conn.cursor()
    
    # Insert in batches
    batch_size = 5000
    for i in range(0, len(trades), batch_size):
        batch = trades[i:i + batch_size]
        execute_batch(cursor, """
            INSERT INTO trades (trade_id, client_id, instrument, side, quantity, price, timestamp, order_type, venue)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (trade_id) DO NOTHING
        """, batch, page_size=1000)
        conn.commit()
        print(f"  Inserted batch {i//batch_size + 1}/{(len(trades)-1)//batch_size + 1}")
    
    print(f"✅ Inserted {len(trades)} trades")

def generate_and_insert_positions(conn, client_ids):
    """Generate and insert current positions"""
    print(f"\n💼 Generating positions...")
    
    instruments = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'CL', 'SPX']
    positions = []
    
    np.random.seed(42)
    
    for client_id in client_ids:
        n_positions = np.random.randint(1, 5)
        for instrument in np.random.choice(instruments, n_positions, replace=False):
            net_pos = int(np.random.uniform(-50000, 50000))
            
            positions.append((
                client_id,
                instrument,
                net_pos,
                abs(net_pos) * 1.2,
                round(np.random.uniform(1.0, 5.0), 2),
                round(np.random.uniform(-10000, 10000), 2)
            ))
    
    cursor = conn.cursor()
    execute_batch(cursor, """
        INSERT INTO positions (client_id, instrument, net_position, gross_position, leverage, unrealized_pnl)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (client_id, instrument) DO UPDATE SET
            net_position = EXCLUDED.net_position,
            gross_position = EXCLUDED.gross_position,
            leverage = EXCLUDED.leverage,
            unrealized_pnl = EXCLUDED.unrealized_pnl,
            updated_at = CURRENT_TIMESTAMP
    """, positions)
    conn.commit()
    
    print(f"✅ Inserted {len(positions)} positions")

def generate_and_insert_headlines(conn, n=500, months=6):
    """Generate and insert headlines"""
    print(f"\n📰 Generating {n} headlines...")
    
    instruments = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'CL', 'SPX']
    sentiments = ['negative', 'neutral', 'positive']
    sources = ['Reuters', 'Bloomberg', 'FT', 'WSJ', 'CNBC']
    
    headline_templates = {
        'EURUSD': [
            "ECB {} Rate Decision Amid Inflation Concerns",
            "EUR Volatility {} on Economic Data",
            "European Markets {} After Policy Announcement",
            "Euro Zone GDP {} Expectations",
            "German Manufacturing {} Forecast"
        ],
        'GBPUSD': [
            "Bank of England {} Interest Rate Decision",
            "UK Inflation Data {} Estimates",
            "Sterling {} Against Dollar",
            "British Economy {} Growth Projections"
        ],
        'USDJPY': [
            "BOJ {} Monetary Policy",
            "Yen {} as Fed Signals Rate Path",
            "Japanese Trade Balance {} Expectations"
        ],
        'XAUUSD': [
            "Gold {} on Safe-Haven Demand",
            "Precious Metals {} After Fed Comments",
            "Gold Prices {} Amid Dollar Strength"
        ],
        'CL': [
            "Oil Prices {} on OPEC+ Decision",
            "Crude {} After Inventory Report",
            "Energy Markets {} on Geopolitical Tensions"
        ],
        'SPX': [
            "S&P 500 {} on Earnings Reports",
            "Tech Stocks {} Market Rally",
            "Equity Markets {} After Fed Minutes"
        ]
    }
    
    verbs = {
        'negative': ['Falls', 'Drops', 'Declines', 'Weakens', 'Misses'],
        'neutral': ['Holds Steady', 'Unchanged', 'Stable', 'Maintains'],
        'positive': ['Rises', 'Surges', 'Gains', 'Strengthens', 'Exceeds']
    }
    
    sentiment_scores = {
        'negative': (-0.8, -0.2),
        'neutral': (-0.1, 0.1),
        'positive': (0.2, 0.8)
    }
    
    headlines = []
    start_date = datetime.now() - timedelta(days=months * 30)
    
    np.random.seed(42)
    
    for i in range(n):
        instrument = np.random.choice(instruments)
        sentiment = np.random.choice(sentiments, p=[0.3, 0.4, 0.3])
        timestamp = start_date + timedelta(
            days=np.random.randint(0, months * 30),
            hours=np.random.randint(0, 24)
        )
        
        template = np.random.choice(headline_templates[instrument])
        verb = np.random.choice(verbs[sentiment])
        title = template.format(verb)
        
        score_range = sentiment_scores[sentiment]
        sentiment_score = round(np.random.uniform(score_range[0], score_range[1]), 2)
        
        topics = np.random.choice(['rates', 'inflation', 'gdp', 'trade', 'policy'], 2, replace=False).tolist()
        
        headlines.append((
            f"HDL{str(i).zfill(6)}",
            instrument,
            title,
            sentiment,
            sentiment_score,
            timestamp,
            np.random.choice(sources),
            topics
        ))
    
    cursor = conn.cursor()
    execute_batch(cursor, """
        INSERT INTO headlines (headline_id, instrument, title, sentiment, sentiment_score, timestamp, source, topics)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (headline_id) DO NOTHING
    """, headlines)
    conn.commit()
    
    print(f"✅ Inserted {len(headlines)} headlines")

def generate_and_insert_market_bars(conn, months=6):
    """Generate and insert market bars"""
    print(f"\n📊 Generating market bars for {months} months...")
    
    instruments = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'CL', 'SPX']
    base_prices = {
        'EURUSD': 1.10,
        'GBPUSD': 1.27,
        'USDJPY': 149.50,
        'XAUUSD': 1950.00,
        'CL': 75.00,
        'SPX': 4500.00
    }
    
    bars = []
    start_date = datetime.now() - timedelta(days=months * 30)
    
    np.random.seed(42)
    
    for instrument in instruments:
        price = base_prices[instrument]
        volatility = price * 0.01
        
        for day in range(months * 30):
            timestamp = start_date + timedelta(days=day)
            
            # Random walk
            change = np.random.normal(0, volatility)
            price += change
            
            open_price = price + np.random.normal(0, volatility * 0.5)
            high_price = price + abs(np.random.normal(0, volatility))
            low_price = price - abs(np.random.normal(0, volatility))
            close_price = price
            volume = int(np.random.uniform(100000, 1000000))
            
            bars.append((
                instrument,
                timestamp,
                round(open_price, 4),
                round(high_price, 4),
                round(low_price, 4),
                round(close_price, 4),
                volume
            ))
    
    cursor = conn.cursor()
    
    # Insert in batches
    batch_size = 1000
    for i in range(0, len(bars), batch_size):
        batch = bars[i:i + batch_size]
        execute_batch(cursor, """
            INSERT INTO market_bars (instrument, timestamp, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (instrument, timestamp) DO NOTHING
        """, batch, page_size=500)
        conn.commit()
        print(f"  Inserted batch {i//batch_size + 1}/{(len(bars)-1)//batch_size + 1}")
    
    print(f"✅ Inserted {len(bars)} market bars")

def main():
    """Main seeding function"""
    print("=" * 60)
    print("📦 Seeding Trading Intelligence Database")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        print("✅ Connected to database")
        
        # Seed data
        client_ids = generate_and_insert_clients(conn, n=50)
        generate_and_insert_trades(conn, client_ids, trades_per_client=1000, months=6)
        generate_and_insert_positions(conn, client_ids)
        generate_and_insert_headlines(conn, n=500, months=6)
        generate_and_insert_market_bars(conn, months=6)
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Database seeding complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
