"""
Segmentation Agent - Pure Gemini Implementation

Uses Gemini Flash 2.5 to analyze trading behavior and classify client segments.
Follows ADK pattern with tools, prompts, and structured outputs.
"""
from google import generativeai as genai
import json
import logging
from typing import Dict, Any
from datetime import datetime

from .prompts import SYSTEM_INSTRUCTION, build_analysis_prompt, FEW_SHOT_EXAMPLES
from .tools import fetch_trades_summary, fetch_position_snapshot, get_tool_declarations

logger = logging.getLogger(__name__)


class SegmentationAgent:
    """
    Agent that uses Gemini to analyze trading behavior and classify segments.
    
    This is a pure AI agent - no hardcoded rules, Gemini does all reasoning.
    """
    
    def __init__(self, data_service):
        """
        Initialize segmentation agent with Gemini.
        
        Args:
            data_service: DataService instance for database access
        """
        self.data_service = data_service
        
        try:
            # Initialize Gemini with system instruction
            self.model = genai.GenerativeModel(
                model_name='gemini-2.0-flash-exp',
                system_instruction=SYSTEM_INSTRUCTION
            )
            
            # Configure generation
            self.generation_config = {
                "temperature": 0.3,  # Lower for more consistent classifications
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
                "response_mime_type": "application/json"  # Force JSON output
            }
            
            self.enabled = True
            logger.info("✅ Segmentation Agent initialized with Gemini Flash 2.5")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini for Segmentation Agent: {e}")
            self.enabled = False
            self.model = None
    
    def analyze(self, client_id: str) -> Dict[str, Any]:
        """
        Analyze client trading behavior using Gemini.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dict with segment, confidence, switchProb, drivers, riskFlags
        """
        logger.info(f"🎯 Segmentation Agent analyzing: {client_id}")
        
        if not self.enabled:
            logger.warning("Gemini not available, returning default segmentation")
            return self._get_fallback_segmentation(client_id)
        
        try:
            # Step 1: Gather data using tools
            trade_summary = fetch_trades_summary(client_id, self.data_service)
            position_snapshot = fetch_position_snapshot(client_id, self.data_service)
            
            # Step 2: Build prompt with data
            prompt = build_analysis_prompt(
                client_id=client_id,
                trade_summary=trade_summary,
                position_snapshot=position_snapshot
            )
            
            # Step 3: Call Gemini
            logger.info(f"🤖 Calling Gemini for segmentation analysis...")
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Step 4: Parse response
            result = self._parse_gemini_response(response.text, client_id)
            
            # Step 5: Add metadata
            result['clientId'] = client_id
            result['primaryExposure'] = self._get_primary_exposure(position_snapshot)
            
            # Step 6: Get client metadata
            client_meta = self.data_service.get_client_metadata(client_id)
            if client_meta:
                result['name'] = client_meta.get('name', client_id)
                result['rm'] = client_meta.get('rm', 'Unassigned')
                result['sector'] = client_meta.get('sector', 'Unknown')
            
            logger.info(
                f"✅ Segmentation complete: {result['segment']} "
                f"(confidence={result['confidence']:.2f}, "
                f"switchProb={result['switchProb']:.2f})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in Gemini segmentation for {client_id}: {e}", exc_info=True)
            return self._get_fallback_segmentation(client_id)
    
    def _parse_gemini_response(self, response_text: str, client_id: str) -> Dict[str, Any]:
        """
        Parse and validate Gemini's JSON response.
        
        Args:
            response_text: Raw text from Gemini
            client_id: Client ID (for error messages)
            
        Returns:
            Validated segmentation result
        """
        try:
            # Clean response (remove markdown if present)
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
            
            # Validate required fields
            required_fields = ['segment', 'confidence', 'switchProb', 'drivers', 'riskFlags']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate segment value
            valid_segments = {'Trend Follower', 'Mean Reverter', 'Hedger', 'Trend Setter'}
            if result['segment'] not in valid_segments:
                logger.warning(f"Invalid segment '{result['segment']}', defaulting to Trend Follower")
                result['segment'] = 'Trend Follower'
            
            # Validate ranges
            result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))
            result['switchProb'] = max(0.15, min(0.85, float(result['switchProb'])))
            
            # Ensure drivers is list
            if not isinstance(result['drivers'], list):
                result['drivers'] = [str(result['drivers'])]
            
            # Ensure riskFlags is list
            if not isinstance(result['riskFlags'], list):
                result['riskFlags'] = [str(result['riskFlags'])] if result['riskFlags'] else []
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON from Gemini: {e}")
        
        except Exception as e:
            logger.error(f"Error validating Gemini response: {e}")
            raise
    
    def _get_primary_exposure(self, position_snapshot: Dict[str, float]) -> str:
        """Get the primary (largest) exposure from positions"""
        if not position_snapshot or 'error' in position_snapshot:
            return 'N/A'
        
        try:
            if position_snapshot:
                primary = max(position_snapshot.items(), key=lambda x: x[1])
                return primary[0]
            return 'N/A'
        except:
            return 'N/A'
    
    def _get_fallback_segmentation(self, client_id: str) -> Dict[str, Any]:
        """
        Return fallback segmentation when Gemini is unavailable.
        
        Uses simple heuristics based on data.
        """
        logger.warning(f"Using fallback segmentation for {client_id}")
        
        try:
            # Get basic data
            trade_summary = fetch_trades_summary(client_id, self.data_service)
            position_snapshot = fetch_position_snapshot(client_id, self.data_service)
            
            # Simple heuristic classification
            trade_count = trade_summary.get('trade_count', 0)
            avg_holding = trade_summary.get('avg_holding_days', 0)
            flips = trade_summary.get('position_flips', 0)
            
            if avg_holding > 30:
                segment = 'Hedger'
                confidence = 0.60
            elif flips > 10:
                segment = 'Mean Reverter'
                confidence = 0.55
            elif avg_holding < 5 and trade_count > 200:
                segment = 'Trend Follower'
                confidence = 0.65
            else:
                segment = 'Trend Setter'
                confidence = 0.50
            
            # Basic switch probability
            if flips > 8 or trade_count < 20:
                switch_prob = 0.60
            else:
                switch_prob = 0.35
            
            return {
                'clientId': client_id,
                'segment': segment,
                'confidence': confidence,
                'switchProb': switch_prob,
                'drivers': [
                    f"Fallback classification based on {trade_count} trades",
                    f"Average holding period: {avg_holding:.1f} days"
                ],
                'riskFlags': ['Gemini unavailable - using heuristic classification'],
                'primaryExposure': self._get_primary_exposure(position_snapshot),
                'reasoning': 'Fallback heuristic used due to Gemini unavailability'
            }
            
        except Exception as e:
            logger.error(f"Error in fallback segmentation: {e}")
            return {
                'clientId': client_id,
                'segment': 'Unclassified',
                'confidence': 0.0,
                'switchProb': 0.30,
                'drivers': ['Error in analysis'],
                'riskFlags': ['Classification failed'],
                'primaryExposure': 'N/A',
                'reasoning': f'Error: {str(e)}'
            }
