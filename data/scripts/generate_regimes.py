"""
Generate historical client regimes (segment timeline)
For timeline visualization in the UI
"""
import psycopg2
from psycopg2.extras import execute_batch
import numpy as np
from datetime import datetime, timedelta, date
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


def generate_regimes_for_client(client_id, current_segment, months_history=12):
    """
    Generate historical regime timeline for a client
    
    Creates 1-4 historical regimes showing segment evolution
    """
    if not current_segment:
        return []  # Skip clients without segment
    
    segments = ['Trend Follower', 'Mean Reverter', 'Hedger', 'Trend Setter']
    
    # How many historical regimes? (1-3 past + 1 current)
    num_past_regimes = np.random.randint(0, 3)
    
    regimes = []
    start_date = datetime.now().date() - timedelta(days=months_history * 30)
    
    # Generate past regimes
    for i in range(num_past_regimes):
        # Pick a different segment
        past_segment = np.random.choice([s for s in segments if s != current_segment])
        
        # Duration: 2-4 months
        duration_days = np.random.randint(60, 120)
        end_date = start_date + timedelta(days=duration_days)
        
        # Confidence slightly lower for historical
        confidence = round(np.random.uniform(0.65, 0.80), 3)
        
        notes = f"Historical classification - {past_segment} behavior observed"
        
        regimes.append({
            'client_id': client_id,
            'segment': past_segment,
            'start_date': start_date,
            'end_date': end_date,
            'confidence': confidence,
            'notes': notes
        })
        
        # Next regime starts day after
        start_date = end_date + timedelta(days=1)
    
    # Current regime (no end date)
    confidence = round(np.random.uniform(0.75, 0.90), 3)
    notes = f"Current active classification - {current_segment} pattern"
    
    regimes.append({
        'client_id': client_id,
        'segment': current_segment,
        'start_date': start_date,
        'end_date': None,  # Active regime
        'confidence': confidence,
        'notes': notes
    })
    
    return regimes


def main():
    """Generate regimes for all clients"""
    print("=" * 60)
    print("📅 Generating Client Regimes (Timeline)")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        print("✅ Connected to database\n")
        
        # Get all clients with segments
        cursor = conn.cursor()
        cursor.execute("""
            SELECT client_id, segment 
            FROM clients 
            WHERE segment IS NOT NULL
            ORDER BY client_id
        """)
        clients = cursor.fetchall()
        
        print(f"Found {len(clients)} clients with segments\n")
        
        all_regimes = []
        
        np.random.seed(42)
        
        for i, (client_id, current_segment) in enumerate(clients, 1):
            print(f"[{i}/{len(clients)}] Generating regimes for {client_id}...", end=' ')
            
            regimes = generate_regimes_for_client(client_id, current_segment, months_history=12)
            all_regimes.extend(regimes)
            
            print(f"✅ ({len(regimes)} regimes)")
        
        # Insert regimes
        if all_regimes:
            print(f"\n💾 Inserting {len(all_regimes)} regime records...")
            
            regime_tuples = [
                (
                    r['client_id'],
                    r['segment'],
                    r['start_date'],
                    r['end_date'],
                    r['confidence'],
                    r['notes']
                )
                for r in all_regimes
            ]
            
            execute_batch(cursor, """
                INSERT INTO client_regimes 
                (client_id, segment, start_date, end_date, confidence, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, regime_tuples)
            
            conn.commit()
            print("✅ Regimes inserted successfully")
        
        # Summary
        cursor.execute("SELECT COUNT(*) FROM client_regimes")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM client_regimes WHERE end_date IS NULL")
        active = cursor.fetchone()[0]
        
        print(f"\n📊 Summary:")
        print(f"   Total regimes: {total}")
        print(f"   Active regimes: {active}")
        print(f"   Historical regimes: {total - active}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Regime generation complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
