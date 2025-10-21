import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_market_bars(n_days=180):
    """Generate OHLCV market data"""
    np.random.seed(42)
    
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
    
    for instrument in instruments:
        price = base_prices[instrument]
        volatility = price * 0.01
        
        for day in range(n_days):
            timestamp = datetime.now() - timedelta(days=n_days - day)
            
            # Random walk
            change = np.random.normal(0, volatility)
            price += change
            
            open_price = price + np.random.normal(0, volatility * 0.5)
            high_price = price + abs(np.random.normal(0, volatility))
            low_price = price - abs(np.random.normal(0, volatility))
            close_price = price
            volume = int(np.random.uniform(100000, 1000000))
            
            bars.append({
                'instrument': instrument,
                'timestamp': timestamp.isoformat(),
                'open': round(open_price, 4),
                'high': round(high_price, 4),
                'low': round(low_price, 4),
                'close': round(close_price, 4),
                'volume': volume
            })
    
    df = pd.DataFrame(bars)
    df.to_csv('../raw/market_bars.csv', index=False)
    print(f"Generated {len(bars)} market bars")
    return df

if __name__ == "__main__":
    generate_market_bars(180)
