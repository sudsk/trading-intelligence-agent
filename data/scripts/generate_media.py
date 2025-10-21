import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_headlines(n=200):
    """Generate mock headline data"""
    np.random.seed(42)
    
    instruments = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'CL', 'SPX']
    sentiments = ['negative', 'neutral', 'positive']
    
    headline_templates = {
        'EURUSD': [
            "ECB Signals {} Rate Hold Amid Inflation Concerns",
            "EUR Volatility {} on Mixed Economic Data",
            "European Markets {} After ECB Decision",
            "Euro Zone GDP {} Expectations",
            "German Manufacturing PMI {} Forecast"
        ],
        'GBPUSD': [
            "Bank of England {} Interest Rate Decision",
            "UK Inflation Data {} Estimates",
            "Sterling {} Against Dollar on Brexit Concerns",
            "British Economy {} Growth Projections"
        ],
        'USDJPY': [
            "BOJ {} Monetary Policy Unchanged",
            "Yen {} as Fed Signals Rate Path",
            "Japanese Trade Balance {} Expectations",
            "USD/JPY {} on Risk Sentiment Shift"
        ],
        'XAUUSD': [
            "Gold {} on Safe-Haven Demand",
            "Precious Metals {} After Fed Comments",
            "Gold Prices {} Amid Dollar Strength",
            "Bullion Market {} on Inflation Data"
        ],
        'CL': [
            "Oil Prices {} on OPEC+ Decision",
            "Crude {} After Inventory Report",
            "Energy Markets {} on Geopolitical Tensions",
            "WTI {} Following Supply Concerns"
        ],
        'SPX': [
            "S&P 500 {} on Earnings Reports",
            "Tech Stocks {} Market Rally",
            "Equity Markets {} After Fed Minutes",
            "Wall Street {} on Economic Optimism"
        ]
    }
    
    verbs = {
        'negative': ['Falls', 'Drops', 'Declines', 'Weakens', 'Misses'],
        'neutral': ['Holds Steady', 'Remains Flat', 'Unchanged', 'Stable'],
        'positive': ['Rises', 'Surges', 'Gains', 'Strengthens', 'Exceeds']
    }
    
    headlines = []
    for i in range(n):
        instrument = np.random.choice(instruments)
        sentiment = np.random.choice(sentiments, p=[0.3, 0.4, 0.3])  # More neutral
        timestamp = datetime.now() - timedelta(hours=np.random.randint(0, 168))  # Last week
        
        template = np.random.choice(headline_templates[instrument])
        verb = np.random.choice(verbs[sentiment])
        title = template.format(verb)
        
        headlines.append({
            'headlineId': f"HDL{str(i).zfill(6)}",
            'instrument': instrument,
            'title': title,
            'sentiment': sentiment,
            'timestamp': timestamp.isoformat(),
            'source': np.random.choice(['Reuters', 'Bloomberg', 'FT', 'WSJ', 'CNBC']),
            'topics': ','.join(np.random.choice(['rates', 'inflation', 'gdp', 'trade', 'policy'], 2))
        })
    
    df = pd.DataFrame(headlines)
    df = df.sort_values('timestamp', ascending=False)
    df.to_csv('../raw/headlines.csv', index=False)
    print(f"Generated {n} headlines")
    return df

if __name__ == "__main__":
    generate_headlines(200)
