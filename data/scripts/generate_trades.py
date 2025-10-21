import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_trades(clients_df, n_trades_per_client=100):
    """Generate mock trade data"""
    np.random.seed(42)
    
    instruments = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'CL', 'SPX']
    sides = ['BUY', 'SELL']
    order_types = ['MARKET', 'LIMIT']
    
    trades = []
    trade_id = 1
    
    for _, client in clients_df.iterrows():
        for _ in range(n_trades_per_client):
            timestamp = datetime.now() - timedelta(days=np.random.randint(0, 180))
            
            trades.append({
                'tradeId': f"TRD{str(trade_id).zfill(8)}",
                'clientId': client['clientId'],
                'instrument': np.random.choice(instruments),
                'side': np.random.choice(sides),
                'quantity': int(np.random.uniform(1000, 100000)),
                'price': round(np.random.uniform(1.0, 2000.0), 4),
                'timestamp': timestamp.isoformat(),
                'orderType': np.random.choice(order_types),
                'venue': np.random.choice(['EBS', 'CME', 'LMAX', 'ICE'])
            })
            trade_id += 1
    
    df = pd.DataFrame(trades)
    df.to_csv('../raw/trades.csv', index=False)
    print(f"Generated {len(trades)} trades")
    return df

if __name__ == "__main__":
    clients_df = pd.read_csv('../raw/clients.csv')
    generate_trades(clients_df, n_trades_per_client=50)
