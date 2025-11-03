"""
Generate switch probability history
Tracks how switch probability evolved over time for each client
"""
import psycopg2
from psycopg2.extras import execute_batch
import numpy as np
import json
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


def generate_switch_prob_history(client_id, current_segment, days_history=90):
    """
    Generate historical switch probability trajectory
    
    Creates realistic evolution showing:
    - Stable periods (low variance)
    - Volatility spikes (sudden increases)
    - Gradual trends
    """
    if not current_segment:
        return []
    
    # Current switch probability (final value)
    # Vary by segment type
    segment_base_probs = {
        'Trend Follower': (0.35, 0.65),  # Moderate to high
        'Mean Reverter': (0.20, 0.45),   # Low to moderate
        'Hedger': (0.15, 0.35),          # Very low to low
        'Trend Setter': (0.40, 0.75)     # Moderate to very high
    }
    
    prob_range = segment_base_probs.get(current_segment, (0.30, 0.60))
    current_prob = np.random.uniform(prob_range[0], prob_range[1])
    
    # Generate ~10-15 historical points
    num_points = np.random.randint(10, 16)
    
    history = []
    start_date = datetime.now() - timedelta(days=days_history)
    
    # Start with lower probability
    prob = max(0.15, current_prob - np.random.uniform(0.10, 0.25))
    
    for i in range(num_points):
        # Time interval
        days_ago = days_history - (i * days_history / num_points)
        computed_at = datetime.now() - timedelta(days=days_ago)
        
        # Add random walk
        change = np.random.normal(0, 0.03)
        
        # Occasional spikes (20% chance)
        if np.random.random() < 0.2:
            change += np.random.uniform(0.05, 0.15)  # Spike up
        
        prob += change
        prob = np.clip(prob, 0.15, 0.85)  # Keep in valid range
        
        # Confidence (slightly variable)
        confidence = round(np.random.uniform(0.70, 0.85), 3)
        
        # Drivers (realistic)
        drivers = generate_drivers(prob, current_segment)
        
        # Risk flags (when prob is high)
        risk_flags = generate_risk_flags(prob, current_segment)
        
        history.append({
            'client_id': client_id,
            'switch_prob': round(prob, 3),
            'confidence': confidence,
            'segment': current_segment,
            'drivers': json.dumps(drivers),
            'risk_flags': json.dumps(risk_flags),
            'computed_at': computed_at
        })
    
    # Ensure last point is close to current
    if history:
        history[-1]['switch_prob'] = round(current_prob, 3)
        history[-1]['computed_at'] = datetime.now() - timedelta(hours=1)
    
    return history


def generate_drivers(prob, segment):
    """Generate realistic classification drivers"""
    
    driver_templates = {
        'Trend Follower': [
            "High momentum alignment",
            "Short holding periods",
            "Directional bias in entries",
            "Following market trends",
            "Aggressive entry timing"
        ],
        'Mean Reverter': [
            "Contrarian positioning",
            "Range-bound trading",
            "High frequency flips",
            "Fade extremes strategy",
            "Mean reversion signals"
        ],
        'Hedger': [
            "Long holding periods",
            "Defensive positioning",
            "Risk mitigation focus",
            "Static hedge overlays",
            "Conservative approach"
        ],
        'Trend Setter': [
            "Anticipatory positioning",
            "Leading indicators",
            "High alpha generation",
            "Contrarian timing",
            "Early trend identification"
        ]
    }
    
    # Pick 2-3 drivers
    available = driver_templates.get(segment, ["Generic trading pattern"])
    num_drivers = np.random.randint(2, min(4, len(available) + 1))
    
    return list(np.random.choice(available, num_drivers, replace=False))


def generate_risk_flags(prob, segment):
    """Generate risk flags when probability is elevated"""
    
    if prob < 0.45:
        return []  # No flags for low prob
    
    risk_templates = [
        "EUR concentration",
        "Position volatility",
        "Leverage increase",
        "Pattern instability",
        "Media-driven volatility",
        "Correlation breakdown",
        "Exposure imbalance",
        "Recent losses"
    ]
    
    # More flags for higher probability
    if prob > 0.65:
        num_flags = np.random.randint(2, 4)
    elif prob > 0.50:
        num_flags = np.random.randint(1, 3)
    else:
        num_flags = np.random.randint(0, 2)
    
    if num_flags == 0:
        return []
    
    return list(np.random.choice(risk_templates, num_flags, replace=False))


def main():
    """Generate switch probability history for all clients"""
    print("=" * 60)
    print("📈 Generating Switch Probability History")
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
        
        all_history = []
        
        np.random.seed(42)
        
        for i, (client_id, segment) in enumerate(clients, 1):
            print(f"[{i}/{len(clients)}] Generating history for {client_id}...", end=' ')
            
            history = generate_switch_prob_history(client_id, segment, days_history=90)
            all_history.extend(history)
            
            print(f"✅ ({len(history)} points)")
        
        # Insert history
        if all_history:
            print(f"\n💾 Inserting {len(all_history)} history records...")
            
            history_tuples = [
                (
                    h['client_id'],
                    h['switch_prob'],
                    h['confidence'],
                    h['segment'],
                    h['drivers'],
                    h['risk_flags'],
                    h['computed_at']
                )
                for h in all_history
            ]
            
            execute_batch(cursor, """
                INSERT INTO switch_probability_history 
                (client_id, switch_prob, confidence, segment, drivers, risk_flags, computed_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
            """, history_tuples, page_size=500)
            
            conn.commit()
            print("✅ History inserted successfully")
        
        # Summary
        cursor.execute("SELECT COUNT(*) FROM switch_probability_history")
        total = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT AVG(switch_prob), MIN(switch_prob), MAX(switch_prob) 
            FROM switch_probability_history
        """)
        avg, min_prob, max_prob = cursor.fetchone()
        
        print(f"\n📊 Summary:")
        print(f"   Total records: {total}")
        print(f"   Avg switch prob: {avg:.2%}")
        print(f"   Range: {min_prob:.2%} - {max_prob:.2%}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Switch probability history generation complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
