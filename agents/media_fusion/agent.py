"""
Media Fusion Agent - Analyzes news headlines and sentiment
"""
import pandas as pd
from typing import Dict, List, Any

class MediaFusionAgent:
    def __init__(self, data_service):
        self.data_service = data_service
    
    def analyze(self, client_id: str, exposures: List[str]) -> Dict[str, Any]:
        """
        Analyze media relevant to client's exposures
        """
        # Fetch headlines for relevant instruments
        headlines = self.data_service.get_headlines(instruments=exposures, hours=24)
        
        # Compute sentiment metrics
        sentiment_avg = self._compute_sentiment_avg(headlines)
        sentiment_velocity = self._compute_sentiment_velocity(headlines)
        
        # Determine media pressure
        pressure = self._compute_media_pressure(sentiment_avg, sentiment_velocity, len(headlines))
        
        # Get top headlines
        top_headlines = self._get_top_headlines(headlines, n=3)
        
        return {
            'pressure': pressure,
            'sentimentAvg': sentiment_avg,
            'sentimentVelocity': sentiment_velocity,
            'headlines': top_headlines,
            'headlineCount': len(headlines)
        }
    
    def _compute_sentiment_avg(self, headlines: pd.DataFrame) -> float:
        """Compute average sentiment (-1 to 1)"""
        sentiment_map = {'negative': -1, 'neutral': 0, 'positive': 1}
        return headlines['sentiment'].map(sentiment_map).mean()
    
    def _compute_sentiment_velocity(self, headlines: pd.DataFrame) -> float:
        """Compute rate of sentiment change"""
        # Placeholder - implement rolling window comparison
        return 0.05
    
    def _compute_media_pressure(self, sentiment_avg: float, velocity: float, count: int) -> str:
        """Determine overall media pressure level"""
        if count > 10 and abs(sentiment_avg) > 0.5:
            return 'HIGH'
        elif count > 5 and abs(sentiment_avg) > 0.3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_top_headlines(self, headlines: pd.DataFrame, n: int) -> List[Dict]:
        """Get top N most relevant headlines"""
        return headlines.head(n).to_dict('records')
