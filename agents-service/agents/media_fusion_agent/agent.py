"""
Media Fusion Agent - Pure Gemini Implementation

Uses Gemini Flash 2.5 for financial news sentiment analysis.
"""
from google import generativeai as genai
import json
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
import pandas as pd

from .prompts import SYSTEM_INSTRUCTION, build_media_analysis_prompt

logger = logging.getLogger(__name__)


class MediaFusionAgent:
    """
    Agent that uses Gemini to analyze financial news sentiment.
    
    Pure AI approach - Gemini handles all sentiment classification.
    """
    
    def __init__(self, data_service):
        """
        Initialize media fusion agent with Gemini.
        
        Args:
            data_service: DataService instance for database access
        """
        self.data_service = data_service
        self.lookback_hours = 72  # Analyze last 3 days
        
        try:
            # Initialize Gemini
            self.model = genai.GenerativeModel(
                model_name='gemini-2.0-flash-exp',
                system_instruction=SYSTEM_INSTRUCTION
            )
            
            self.generation_config = {
                "temperature": 0.2,  # Low for consistent sentiment scoring
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4096,  # More space for multiple headlines
                "response_mime_type": "application/json"
            }
            
            self.sentiment_enabled = True
            logger.info("✅ Media Fusion Agent initialized with Gemini Flash 2.5")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini for Media Fusion Agent: {e}")
            self.sentiment_enabled = False
            self.model = None
    
    def analyze(self, client_id: str, exposures: List[str]) -> Dict[str, Any]:
        """
        Analyze media relevant to client's exposures using Gemini.
        
        Args:
            client_id: Client identifier
            exposures: List of instruments client is exposed to
            
        Returns:
            Dict with pressure, sentiment metrics, headlines
        """
        logger.info(f"📰 Media Fusion Agent analyzing for: {client_id}")
        logger.info(f"   Exposures: {exposures}")
        
        try:
            # Step 1: Fetch headlines
            headlines_df = self._fetch_headlines(exposures)
            
            if headlines_df.empty:
                logger.info(f"No headlines found for {client_id}")
                return self._get_default_media_analysis()
            
            # Step 2: Prepare headlines for Gemini
            headlines_list = headlines_df.to_dict('records')
            
            # Step 3: Use Gemini for sentiment analysis
            if self.sentiment_enabled and len(headlines_list) > 0:
                result = self._gemini_sentiment_analysis(
                    client_id=client_id,
                    exposures=exposures,
                    headlines=headlines_list
                )
            else:
                result = self._fallback_sentiment_analysis(headlines_df)
            
            logger.info(
                f"✅ Media analysis complete: pressure={result['pressure']}, "
                f"headlines={result['headline_count']}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in media analysis for {client_id}: {e}", exc_info=True)
            return self._get_default_media_analysis()
    
    def _fetch_headlines(self, exposures: List[str]) -> pd.DataFrame:
        """Fetch headlines for given instruments"""
        if not exposures:
            return pd.DataFrame()
        
        headlines = self.data_service.get_headlines(
            instruments=exposures,
            hours=self.lookback_hours
        )
        
        if not headlines.empty:
            headlines['timestamp'] = pd.to_datetime(headlines['timestamp'])
            headlines = headlines.sort_values('timestamp', ascending=False)
        
        return headlines
    
    def _gemini_sentiment_analysis(
        self,
        client_id: str,
        exposures: List[str],
        headlines: List[Dict]
    ) -> Dict[str, Any]:
        """
        Use Gemini to analyze headline sentiment.
        
        Args:
            client_id: Client ID
            exposures: List of exposures
            headlines: List of headline dicts
            
        Returns:
            Media analysis result
        """
        try:
            # Build prompt
            prompt = build_media_analysis_prompt(
                client_id=client_id,
                exposures=exposures,
                headlines=headlines[:20],  # Limit to 20 for token efficiency
                time_range=f"Last {self.lookback_hours} hours"
            )
            
            # Call Gemini
            logger.info("🤖 Calling Gemini for sentiment analysis...")
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse response
            result = self._parse_gemini_media_response(response.text, headlines)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Gemini sentiment analysis: {e}", exc_info=True)
            # Fallback to rule-based
            return self._fallback_sentiment_analysis(pd.DataFrame(headlines))
    
    def _parse_gemini_media_response(
        self,
        response_text: str,
        original_headlines: List[Dict]
    ) -> Dict[str, Any]:
        """
        Parse Gemini's media analysis response.
        
        Args:
            response_text: Raw JSON from Gemini
            original_headlines: Original headline list for fallback
            
        Returns:
            Structured media analysis
        """
        try:
            # Clean response
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Parse JSON
            result = json.loads(text)
            
            # Extract aggregate section
            aggregate = result.get('aggregate', {})
            analyzed_headlines = result.get('headlines', [])
            
            # Validate and extract metrics
            sentiment_avg = float(aggregate.get('sentiment_avg', 0.0))
            sentiment_velocity = float(aggregate.get('sentiment_velocity', 0.0))
            pressure = aggregate.get('pressure', 'MEDIUM')
            
            # Validate pressure value
            if pressure not in ['HIGH', 'MEDIUM', 'LOW']:
                pressure = 'MEDIUM'
            
            # Clip sentiment values
            sentiment_avg = max(-1.0, min(1.0, sentiment_avg))
            sentiment_velocity = max(-1.0, min(1.0, sentiment_velocity))
            
            # Format headlines for response
            top_headlines = []
            for h in analyzed_headlines[:5]:  # Top 5
                # Match with original for metadata
                original = next(
                    (oh for oh in original_headlines if oh.get('headlineId') == h.get('headline_id')),
                    {}
                )
                
                top_headlines.append({
                    'headline_id': h.get('headline_id', ''),
                    'title': h.get('title', ''),
                    'sentiment': h.get('sentiment', 'neutral'),
                    'sentiment_score': float(h.get('sentiment_score', 0.0)),
                    'timestamp': original.get('timestamp', datetime.now().isoformat()),
                    'instrument': original.get('instrument', ''),
                    'source': original.get('source', ''),
                    'reasoning': h.get('reasoning', '')  # Gemini's reasoning
                })
            
            return {
                'pressure': pressure,
                'sentiment_avg': round(sentiment_avg, 3),
                'sentiment_velocity': round(sentiment_velocity, 3),
                'headlines': top_headlines,
                'headline_count': len(original_headlines),
                'reasoning': aggregate.get('reasoning', '')
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON: {e}")
            logger.debug(f"Response: {response_text}")
            raise
        except Exception as e:
            logger.error(f"Error parsing Gemini media response: {e}")
            raise
    
    def _fallback_sentiment_analysis(self, headlines_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Fallback rule-based sentiment when Gemini unavailable.
        
        Uses keyword matching for basic classification.
        """
        logger.info("Using fallback sentiment analysis")
        
        if headlines_df.empty:
            return self._get_default_media_analysis()
        
        # Sentiment keywords
        positive_kw = ['surge', 'gain', 'rise', 'rally', 'strengthen', 'exceed', 'beat', 'bullish']
        negative_kw = ['fall', 'drop', 'decline', 'weaken', 'miss', 'disappoint', 'bearish']
        
        def classify_sentiment(title: str) -> tuple:
            title_lower = title.lower()
            pos_count = sum(1 for kw in positive_kw if kw in title_lower)
            neg_count = sum(1 for kw in negative_kw if kw in title_lower)
            
            if pos_count > neg_count:
                return 'positive', min(0.7, 0.3 + pos_count * 0.2)
            elif neg_count > pos_count:
                return 'negative', max(-0.7, -0.3 - neg_count * 0.2)
            else:
                return 'neutral', 0.0
        
        # Apply classification
        headlines_df = headlines_df.copy()
        results = headlines_df['title'].apply(classify_sentiment)
        headlines_df['sentiment'] = results.apply(lambda x: x[0])
        headlines_df['sentimentScore'] = results.apply(lambda x: x[1])
        
        # Compute aggregates
        sentiment_avg = headlines_df['sentimentScore'].mean()
        
        # Velocity (recent vs earlier)
        if len(headlines_df) >= 4:
            mid = len(headlines_df) // 2
            recent_sent = headlines_df.iloc[:mid]['sentimentScore'].mean()
            earlier_sent = headlines_df.iloc[mid:]['sentimentScore'].mean()
            velocity = recent_sent - earlier_sent
        else:
            velocity = 0.0
        
        # Pressure determination
        count = len(headlines_df)
        if count > 20 and abs(sentiment_avg) > 0.5:
            pressure = 'HIGH'
        elif count > 10 and abs(sentiment_avg) > 0.3:
            pressure = 'MEDIUM'
        else:
            pressure = 'LOW'
        
        # Format top headlines
        top = headlines_df.head(5).to_dict('records')
        top_formatted = [
            {
                'headline_id': h.get('headlineId', ''),
                'title': h['title'],
                'sentiment': h['sentiment'],
                'sentiment_score': round(h['sentimentScore'], 2),
                'timestamp': h['timestamp'].isoformat() if pd.notna(h.get('timestamp')) else None,
                'instrument': h.get('instrument', ''),
                'source': h.get('source', '')
            }
            for h in top
        ]
        
        return {
            'pressure': pressure,
            'sentiment_avg': round(sentiment_avg, 3),
            'sentiment_velocity': round(velocity, 3),
            'headlines': top_formatted,
            'headline_count': count,
            'reasoning': 'Fallback rule-based sentiment (Gemini unavailable)'
        }
    
    def _get_default_media_analysis(self) -> Dict[str, Any]:
        """Default response when no headlines available"""
        return {
            'pressure': 'LOW',
            'sentiment_avg': 0.0,
            'sentiment_velocity': 0.0,
            'headlines': [],
            'headline_count': 0,
            'reasoning': 'No headlines available for analysis'
        }
