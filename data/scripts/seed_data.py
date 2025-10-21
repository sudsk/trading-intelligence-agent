"""Master script to generate all mock data"""
import sys
sys.path.append('..')

from generate_clients import generate_clients
from generate_trades import generate_trades
from generate_positions import generate_positions
from generate_media import generate_headlines
from generate_pnl_risk import generate_pnl_risk
from generate_market_bars import generate_market_bars
import pandas as pd

def seed_all_data():
    """Generate all mock data files"""
    print("=" * 60)
    print("Generating Trading Intelligence Mock Data")
    print("=" * 60)
    
    # 1. Generate clients
    print("\n1. Generating clients...")
    clients_df = generate_clients(n=50)
    
    # 2. Generate trades
    print("\n2. Generating trades...")
    trades_df = generate_trades(clients_df, n_trades_per_client=50)
    
    # 3. Generate positions
    print("\n3. Generating positions...")
    positions_df = generate_positions(clients_df)
    
    # 4. Generate headlines
    print("\n4. Generating headlines...")
    headlines_df = generate_headlines(n=200)
    
    # 5. Generate PnL/Risk
    print("\n5. Generating PnL/Risk data...")
    pnl_df = generate_pnl_risk(clients_df, n_days=90)
    
    # 6. Generate market bars
    print("\n6. Generating market bars...")
    bars_df = generate_market_bars(n_days=180)
    
    print("\n" + "=" * 60)
    print("Data Generation Complete!")
    print("=" * 60)
    print(f"\nGenerated files in ../raw/:")
    print(f"  - clients.csv ({len(clients_df)} records)")
    print(f"  - trades.csv ({len(trades_df)} records)")
    print(f"  - positions.csv ({len(positions_df)} records)")
    print(f"  - headlines.csv ({len(headlines_df)} records)")
    print(f"  - pnl_risk.csv ({len(pnl_df)} records)")
    print(f"  - market_bars.csv ({len(bars_df)} records)")
    print("\nReady for demo!")

if __name__ == "__main__":
    seed_all_data()
