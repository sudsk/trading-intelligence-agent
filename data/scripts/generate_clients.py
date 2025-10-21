import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_clients(n=50):
    """Generate mock client data"""
    np.random.seed(42)
    
    segments = ['Trend Follower', 'Mean Reverter', 'Hedger', 'Trend Setter']
    rms = ['Sarah Chen', 'Michael Torres', 'Emma Wilson', 'James Park', 'Lisa Anderson']
    exposures = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'Gold', 'Crude Oil', 'S&P 500']
    
    clients = []
    for i in range(n):
        client_id = f"{np.random.choice(['ACME', 'ZEUS', 'TITAN', 'NOVA', 'APEX'])}_{np.random.choice(['FX', 'COMM', 'EQ', 'RATES'])}_{str(i).zfill(3)}"
        
        clients.append({
            'clientId': client_id,
            'name': client_id,
            'segment': np.random.choice(segments),
            'switchProb': round(np.random.uniform(0.15, 0.85), 2),
            'rm': np.random.choice(rms),
            'primaryExposure': np.random.choice(exposures),
            'sector': np.random.choice(['Financial Services', 'Energy', 'Technology', 'Commodities']),
        })
    
    df = pd.DataFrame(clients)
    df = df.sort_values('switchProb', ascending=False)
    df.to_csv('../raw/clients.csv', index=False)
    print(f"Generated {n} clients")
    return df

if __name__ == "__main__":
    generate_clients(50)
