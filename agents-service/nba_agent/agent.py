"""
NBA (Next Best Action) Agent - Pure Gemini Implementation

Uses Gemini Flash 2.5 to generate relationship manager recommendations.
"""
from google import generativeai as genai
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

from .prompts import SYSTEM_INSTRUCTION, build_recommendation_prompt

logger = logging.getLogger(__name__)


class NBAAgent:
    """
    Agent that uses Gemini to generate next best action recommendations.
    
    Pure AI approach - Gemini selects actions and products based on context.
    """
    
    def __init__(self):
        """Initialize NBA agent with Gemini."""
        try:
            # Initialize Gemini
            self.model = genai.GenerativeModel(
                model_name='gemini-2.0-flash-exp',
                system_instruction=SYSTEM_INSTRUCTION
            )
            
            self.generation_config = {
                "temperature": 0.4,  # Slightly higher for creative recommendations
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 3072,
                "response_mime_type": "application/json"
            }
            
            self.enabled = True
            logger.info("✅ NBA Agent initialized with Gemini Flash 2.5")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini for NBA Agent: {e}")
            self.enabled = False
            self.model = None
    
    def recommend(
        self,
        client_id: str,
        segment: str,
        switch_prob: float,
        risk_flags: List[str],
        media_pressure: str,
        primary_exposure: str,
        confidence: float = 0.7,
        sentiment: float = 0.0,
        drivers: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations using Gemini.
        
        Args:
            client_id: Client identifier
            segment: Client segment (Trend Follower, etc.)
            switch_prob: Switch probability (0.0-1.0)
            risk_flags: List of risk concerns
            media_pressure: HIGH/MEDIUM/LOW
            primary_exposure: Primary instrument
            confidence: Segmentation confidence
            sentiment: Media sentiment (-1 to +1)
            drivers: Key classification drivers
            
        Returns:
            List of recommendation dicts
        """
        logger.info(f"💡 NBA Agent generating recommendations for: {client_id}")
        
        if not self.enabled:
            logger.warning("Gemini not available, returning default recommendations")
            return self._get_fallback_recommendations(segment, switch_prob, risk_flags)
        
        try:
            # Build prompt with context
            prompt = build_recommendation_prompt(
                client_id=client_id,
                segment=segment,
                switch_prob=switch_prob,
                confidence=confidence,
                risk_flags=risk_flags or [],
                primary_exposure=primary_exposure,
                media_pressure=media_pressure,
                sentiment=sentiment,
                drivers=drivers or []
            )
            
            # Call Gemini
            logger.info(f"🤖 Calling Gemini for recommendations...")
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse response
            recommendations = self._parse_gemini_response(response.text, client_id)
            
            logger.info(f"✅ Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendations for {client_id}: {e}", exc_info=True)
            return self._get_fallback_recommendations(segment, switch_prob, risk_flags)
    
    def _parse_gemini_response(self, response_text: str, client_id: str) -> List[Dict[str, Any]]:
        """
        Parse and validate Gemini's recommendations JSON.
        
        Args:
            response_text: Raw text from Gemini
            client_id: Client ID (for error messages)
            
        Returns:
            List of validated recommendations
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
            
            # Extract recommendations
            recommendations = result.get('recommendations', [])
            
            if not recommendations:
                logger.warning("No recommendations in Gemini response")
                return []
            
            # Validate and normalize each recommendation
            validated = []
            for rec in recommendations:
                validated_rec = self._validate_recommendation(rec)
                if validated_rec:
                    # Add timestamp
                    validated_rec['timestamp'] = datetime.utcnow().isoformat()
                    validated.append(validated_rec)
            
            return validated
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON from Gemini: {e}")
        
        except Exception as e:
            logger.error(f"Error validating recommendations: {e}")
            raise
    
    def _validate_recommendation(self, rec: Dict) -> Dict[str, Any]:
        """
        Validate a single recommendation.
        
        Args:
            rec: Raw recommendation dict from Gemini
            
        Returns:
            Validated and normalized recommendation, or None if invalid
        """
        try:
            # Valid action types
            valid_actions = {
                'PROACTIVE_OUTREACH',
                'ENHANCED_MONITORING',
                'PROPOSE_HEDGE',
                'SEND_MARKET_UPDATE',
                'SUGGEST_OPPORTUNITY'
            }
            
            # Valid priorities
            valid_priorities = {'HIGH', 'MEDIUM', 'LOW'}
            
            # Validate required fields
            action = rec.get('action')
            if action not in valid_actions:
                logger.warning(f"Invalid action: {action}, defaulting to ENHANCED_MONITORING")
                action = 'ENHANCED_MONITORING'
            
            priority = rec.get('priority', 'MEDIUM')
            if priority not in valid_priorities:
                logger.warning(f"Invalid priority: {priority}, defaulting to MEDIUM")
                priority = 'MEDIUM'
            
            message = rec.get('message', '')
            if not message:
                logger.warning("Empty message in recommendation")
                message = f"Action required: {action}"
            
            # Build validated recommendation
            validated = {
                'action': action,
                'priority': priority,
                'message': message,
                'products': rec.get('products', []),
                'suggestedActions': rec.get('suggested_actions', []),
                'reasoning': rec.get('reasoning', '')
            }
            
            # Optional urgency field
            if 'urgency' in rec:
                valid_urgencies = {'urgent', 'high', 'medium', 'low'}
                if rec['urgency'] in valid_urgencies:
                    validated['urgency'] = rec['urgency']
            
            # Ensure lists are lists
            if not isinstance(validated['products'], list):
                validated['products'] = [str(validated['products'])] if validated['products'] else []
            
            if not isinstance(validated['suggestedActions'], list):
                validated['suggestedActions'] = [str(validated['suggestedActions'])] if validated['suggestedActions'] else []
            
            return validated
            
        except Exception as e:
            logger.error(f"Error validating recommendation: {e}")
            return None
    
    def _get_fallback_recommendations(
        self,
        segment: str,
        switch_prob: float,
        risk_flags: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate fallback recommendations using simple rules.
        
        Args:
            segment: Client segment
            switch_prob: Switch probability
            risk_flags: Risk flags
            
        Returns:
            List of basic recommendations
        """
        logger.warning("Using fallback recommendations (Gemini unavailable)")
        
        recommendations = []
        timestamp = datetime.utcnow().isoformat()
        
        # Rule 1: High switch probability
        if switch_prob > 0.50:
            recommendations.append({
                'action': 'PROACTIVE_OUTREACH',
                'priority': 'HIGH',
                'urgency': 'high' if switch_prob > 0.65 else 'medium',
                'message': f'Client showing elevated switch probability ({switch_prob:.1%}). Immediate relationship manager contact recommended.',
                'products': self._get_default_products(segment, 'high_switch'),
                'suggestedActions': [
                    'Schedule strategy review call within 48 hours',
                    'Prepare client portfolio analysis',
                    'Discuss strategy changes and concerns'
                ],
                'reasoning': f'Switch probability {switch_prob:.1%} indicates elevated churn risk.',
                'timestamp': timestamp
            })
        
        # Rule 2: Risk flags present
        if risk_flags:
            recommendations.append({
                'action': 'PROPOSE_HEDGE',
                'priority': 'HIGH' if len(risk_flags) > 2 else 'MEDIUM',
                'message': f'Risk concerns identified: {", ".join(risk_flags[:2])}. Hedging recommended.',
                'products': self._get_default_products(segment, 'hedge'),
                'suggestedActions': [
                    'Calculate optimal hedge ratio',
                    'Present hedging cost-benefit scenarios',
                    'Discuss risk tolerance with client'
                ],
                'reasoning': f'{len(risk_flags)} risk flags require attention.',
                'timestamp': timestamp
            })
        
        # Rule 3: Medium switch probability
        elif switch_prob > 0.35:
            recommendations.append({
                'action': 'ENHANCED_MONITORING',
                'priority': 'MEDIUM',
                'message': f'Client showing moderate instability ({switch_prob:.1%}). Enhanced monitoring advised.',
                'products': self._get_default_products(segment, 'monitoring'),
                'suggestedActions': [
                    'Set up daily monitoring alerts',
                    'Review position changes weekly',
                    'Prepare contingency products'
                ],
                'reasoning': f'Switch probability {switch_prob:.1%} warrants closer attention.',
                'timestamp': timestamp
            })
        
        # Rule 4: Stable client - suggest opportunity
        else:
            recommendations.append({
                'action': 'SUGGEST_OPPORTUNITY',
                'priority': 'LOW',
                'message': f'Client showing stable {segment} behavior. Good opportunity for value-add products.',
                'products': self._get_default_products(segment, 'opportunity'),
                'suggestedActions': [
                    'Schedule quarterly review meeting',
                    'Prepare enhancement product overview',
                    'Present optimization case study'
                ],
                'reasoning': f'Stable client (switch prob {switch_prob:.1%}) receptive to enhancements.',
                'timestamp': timestamp
            })
        
        return recommendations
    
    def _get_default_products(self, segment: str, scenario: str) -> List[str]:
        """
        Get default product suggestions based on segment and scenario.
        
        Args:
            segment: Client segment
            scenario: Scenario type (high_switch, hedge, monitoring, opportunity)
            
        Returns:
            List of product suggestions
        """
        playbook = {
            'Trend Follower': {
                'high_switch': ['Forward strips', 'Options collars', 'Dynamic hedging programs'],
                'hedge': ['Stop-loss overlays', 'Profit-taking automation'],
                'monitoring': ['Momentum tracking alerts'],
                'opportunity': ['Enhanced momentum products', 'Breakout algorithms']
            },
            'Mean Reverter': {
                'high_switch': ['Range-bound products', 'Volatility strategies'],
                'hedge': ['Position size limiters', 'Correlation hedges'],
                'monitoring': ['Range-breach alerts'],
                'opportunity': ['Relative value strategies', 'Pairs trading']
            },
            'Hedger': {
                'high_switch': ['Dynamic hedging programs', 'Basis swaps'],
                'hedge': ['Static hedge overlays', 'Tail risk protection'],
                'monitoring': ['Hedge effectiveness tracking'],
                'opportunity': ['Hedge optimization', 'Cost-reduction overlays']
            },
            'Trend Setter': {
                'high_switch': ['Alpha strategies', 'Thematic products'],
                'hedge': ['Portfolio diversification', 'Factor exposure management'],
                'monitoring': ['Leading indicator alerts'],
                'opportunity': ['Alternative alpha sources', 'Smart beta']
            }
        }
        
        return playbook.get(segment, {}).get(scenario, ['Generic products'])
