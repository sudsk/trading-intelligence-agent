import pandas as pd
import numpy as np

def generate_positions(clients_df):
    """Generate current positions for each client"""
    np.random.seed(42)
    
    instruments = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'CL', 'SPX']
    
    positions = []
    for _, client in clients_df.iterrows():
        n_positions = np.random.randint(1, 5)
        for instrument in np.random.choice(instruments, n_positions, replace=False):
            net_position = int(np.random.uniform(-50000, 50000))
            
            positions.append({
                'clientId': client['clientId'],
                'instrument': instrument,
                'netPosition': net_position,
                'grossPosition': abs(net_position) * 1.2,
                'leverage': round(np.random.uniform(1.0, 5.0), 2),
                'unrealizedPnL': round(np.random.uniform(-10000, 10000), 2)
            })
    
    df = pd.DataFrame(positions)
    df.to_csv('../raw/positions.csv', index=False)
    print(f"Generated {len(positions)} positions")
    return df

if __name__ == "__main__
