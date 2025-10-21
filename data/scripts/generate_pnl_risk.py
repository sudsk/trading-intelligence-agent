import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_pnl_risk(clients_df, n_days=90):
    """Generate daily PnL and risk metrics"""
    np.random.seed(42)
    
    pnl_data = []
    
    for _, client in clients_df.iterrows():
        base_pnl = np.random.uniform(-5000, 5000)
        volatility = np.random.uniform(1000, 5000)
        
        for day in range(n_days):
            date = datetime.now() - timedelta(days=n_days - day)
            daily_pnl = base_pnl + np.random.normal(0, volatility)
            
            pnl_data.append({
                'clientId': client['clientId'],
                'date': date.date().isoformat(),
                'dailyPnL': round(daily_pnl, 2),
                'cumulativePnL': round(daily_pnl * day / 10, 2),
                'var95': round(abs(daily_pnl) * 1.65, 2),
                'maxDrawdown': round(min(0, daily_pnl * 0.3), 2),
                'sharpeRatio': round(np.random.uniform(-0.5, 2.0), 2)
            })
    
    df = pd.DataFrame(pnl_data)
    df.to_csv('../raw/pnl_risk.csv', index=False)
    print(f"Generated {len(pnl_data)} PnL/Risk records")
    return df

if __name__ == "__main__":
    clients_df = pd.read_csv('../raw/clients.csv')
    generate_pnl_risk(clients_df, n_days=90)
