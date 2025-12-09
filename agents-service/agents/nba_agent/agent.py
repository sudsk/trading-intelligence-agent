"""
NBA (Next Best Action) Agent - Pure Gemini Implementation

Uses Gemini Flash 2.5 to generate relationship manager recommendations.
Aligned with business spec: 5 action types, segment-specific playbooks, priority determination.
"""
from google import generativeai as genai
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .prompts import SYSTEM_INSTRUCTION, build_recommendation_prompt

logger = logging.getLogger(__name__)


class NBAAgent:
    """
    Agent that uses Gemini to generate next best action recommendations.
    
    Pure AI approach - Gemini selects actions and products based on:
    - Client segment (Trend Follower / Mean Reverter / Hedger / Trend Setter)
    - Switch probability (0.15-0.85)
    - Risk flags (concentration, leverage, volatility)
    - Media pressure (HIGH/MEDIUM/LOW)
    - Primary exposure
    
    Returns 1-5 prioritized recommendations with specific products and action steps.
    """
    
    def __init__(self):
        """Initialize NBA agent with Gemini."""
        try:
            # Initialize Gemini
            self.model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                system_instruction=SYSTEM_INSTRUCTION
            )
            
            self.generation_config = {
                "temperature": 0.4,  # Higher for creative recommendations
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4096,  # More space for multiple recommendations
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
        Generate next best action recommendations using Gemini.
        
        Business Logic:
        - High switch prob (>0.50) → PROACTIVE_OUTREACH
        - Medium switch (0.35-0.50) + high media → ENHANCED_MONITORING
        - Risk flags present → PROPOSE_HEDGE
        - High media pressure → SEND_MARKET_UPDATE
        - Stable client (<0.35) → SUGGEST_OPPORTUNITY
        
        Args:
            client_id: Client identifier
            segment: Client segment (Trend Follower, Mean Reverter, Hedger, Trend Setter)
            switch_prob: Switch probability (0.0-1.0, typically 0.15-0.85)
            risk_flags: List of risk concerns (e.g., ["EUR concentration 72%", "Leverage drift"])
            media_pressure: HIGH/MEDIUM/LOW
            primary_exposure: Primary instrument (e.g., "EURUSD")
            confidence: Segmentation confidence (0.0-1.0)
            sentiment: Media sentiment average (-1.0 to +1.0)
            drivers: Key classification drivers (e.g., ["High momentum-beta", "Short holds"])
            
        Returns:
            List of 1-5 recommendation dicts, each with:
            - action: Action type (PROACTIVE_OUTREACH, etc.)
            - priority: HIGH/MEDIUM/LOW
            - urgency: urgent/high/medium/low (optional)
            - message: Human-readable recommendation
            - products: List of 2-4 specific products
            - suggested_actions: List of 3-5 concrete action steps
            - reasoning: Why this recommendation
            - timestamp: ISO timestamp
        """
        logger.info(f"💡 NBA Agent generating recommendations for: {client_id}")
        logger.info(
            f"   Context: segment={segment}, switch_prob={switch_prob:.2f}, "
            f"media={media_pressure}, flags={len(risk_flags)}"
        )
        
        if not self.enabled:
            logger.warning("Gemini not available, returning fallback recommendations")
            return self._get_fallback_recommendations(
                client_id, segment, switch_prob, risk_flags, media_pressure
            )
        
        try:
            # Build prompt with full context
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
            logger.info("🤖 Calling Gemini for recommendations...")
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse and validate response
            recommendations = self._parse_gemini_response(response.text, client_id)
            
            # Ensure we have 1-5 recommendations
            if not recommendations:
                logger.warning("Gemini returned no recommendations, using fallback")
                return self._get_fallback_recommendations(
                    client_id, segment, switch_prob, risk_flags, media_pressure
                )
            
            # Limit to 5 recommendations
            recommendations = recommendations[:5]
            
            logger.info(f"✅ Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendations for {client_id}: {e}", exc_info=True)
            return self._get_fallback_recommendations(
                client_id, segment, switch_prob, risk_flags, media_pressure
            )
    
    def _parse_gemini_response(self, response_text: str, client_id: str) -> List[Dict[str, Any]]:
        """
        Parse and validate Gemini's recommendations JSON.
        
        Expected format:
        {
          "recommendations": [
            {
              "action": "PROACTIVE_OUTREACH",
              "priority": "HIGH",
              "urgency": "urgent",
              "message": "Client showing elevated switch probability...",
              "products": ["Forward strips", "Options collars"],
              "suggested_actions": ["Call client today", "Prepare analysis"],
              "reasoning": "High switch prob indicates churn risk..."
            }
          ],
          "overall_assessment": "Client showing moderate instability..."
        }
        
        Args:
            response_text: Raw JSON text from Gemini
            client_id: Client ID (for error context)
            
        Returns:
            List of validated recommendations
        """
        try:
            # Clean response (remove markdown code blocks if present)
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
            
            # Extract recommendations array
            recommendations = result.get('recommendations', [])
            
            if not recommendations:
                logger.warning("No recommendations array in Gemini response")
                return []
            
            if not isinstance(recommendations, list):
                logger.error("Recommendations is not a list")
                return []
            
            # Validate and normalize each recommendation
            validated = []
            for idx, rec in enumerate(recommendations):
                try:
                    validated_rec = self._validate_recommendation(rec, idx)
                    if validated_rec:
                        # Add timestamp
                        validated_rec['timestamp'] = datetime.utcnow().isoformat()
                        validated.append(validated_rec)
                except Exception as e:
                    logger.warning(f"Failed to validate recommendation {idx}: {e}")
                    continue
            
            return validated
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON from Gemini: {e}")
        
        except Exception as e:
            logger.error(f"Error parsing recommendations: {e}")
            raise
    
    def _validate_recommendation(self, rec: Dict, idx: int = 0) -> Optional[Dict[str, Any]]:
        """
        Validate and normalize a single recommendation.
        
        Ensures:
        - action is one of 5 valid types
        - priority is HIGH/MEDIUM/LOW
        - message is non-empty
        - products is a list (2-4 items preferred)
        - suggested_actions is a list (3-5 items preferred)
        - reasoning is present
        
        Args:
            rec: Raw recommendation dict from Gemini
            idx: Index in recommendations array (for logging)
            
        Returns:
            Validated and normalized recommendation, or None if invalid
        """
        try:
            # Valid action types (per spec)
            valid_actions = {
                'PROACTIVE_OUTREACH',      # Switch prob > 0.50
                'ENHANCED_MONITORING',     # Switch prob 0.35-0.50 OR high media
                'PROPOSE_HEDGE',           # Risk flags present
                'SEND_MARKET_UPDATE',      # High media pressure
                'SUGGEST_OPPORTUNITY'      # Stable client
            }
            
            # Valid priorities
            valid_priorities = {'HIGH', 'MEDIUM', 'LOW'}
            
            # Valid urgency levels (optional)
            valid_urgencies = {'urgent', 'high', 'medium', 'low'}
            
            # Validate action
            action = rec.get('action', '').upper()
            if action not in valid_actions:
                logger.warning(
                    f"Rec {idx}: Invalid action '{action}', defaulting to ENHANCED_MONITORING"
                )
                action = 'ENHANCED_MONITORING'
            
            # Validate priority
            priority = rec.get('priority', 'MEDIUM').upper()
            if priority not in valid_priorities:
                logger.warning(f"Rec {idx}: Invalid priority '{priority}', defaulting to MEDIUM")
                priority = 'MEDIUM'
            
            # Validate message
            message = rec.get('message', '').strip()
            if not message:
                logger.warning(f"Rec {idx}: Empty message")
                message = f"Action required: {action.replace('_', ' ').title()}"
            
            # Validate products
            products = rec.get('products', [])
            if not isinstance(products, list):
                products = [str(products)] if products else []
            
            # Validate suggested_actions
            suggested_actions = rec.get('suggested_actions', [])
            if not isinstance(suggested_actions, list):
                suggested_actions = [str(suggested_actions)] if suggested_actions else []
            
            # Build validated recommendation
            validated = {
                'action': action,
                'priority': priority,
                'message': message,
                'products': products,
                'suggested_actions': suggested_actions,
                'reasoning': rec.get('reasoning', '').strip()
            }
            
            # Add optional urgency field
            urgency = rec.get('urgency', '').lower()
            if urgency and urgency in valid_urgencies:
                validated['urgency'] = urgency
            
            return validated
            
        except Exception as e:
            logger.error(f"Error validating recommendation {idx}: {e}")
            return None
    
    def _get_fallback_recommendations(
        self,
        client_id: str,
        segment: str,
        switch_prob: float,
        risk_flags: List[str],
        media_pressure: str
    ) -> List[Dict[str, Any]]:
        """
        Generate fallback recommendations using rule-based logic.
        
        Used when Gemini is unavailable or returns invalid response.
        
        Decision Tree:
        1. Switch prob > 0.65 → URGENT outreach
        2. Switch prob > 0.50 → HIGH priority outreach
        3. Risk flags (>2) → HIGH priority hedge
        4. Risk flags (1-2) → MEDIUM priority hedge
        5. Switch prob 0.35-0.50 OR high media → MEDIUM monitoring
        6. High media pressure → LOW market update
        7. Switch prob < 0.35 → LOW opportunity
        
        Args:
            client_id: Client identifier
            segment: Client segment
            switch_prob: Switch probability
            risk_flags: Risk flags
            media_pressure: Media pressure level
            
        Returns:
            List of 1-3 rule-based recommendations
        """
        logger.warning(f"Using fallback recommendations for {client_id} (Gemini unavailable)")
        
        recommendations = []
        timestamp = datetime.utcnow().isoformat()
        
        # Rule 1: Very high switch probability (URGENT)
        if switch_prob > 0.65:
            recommendations.append({
                'action': 'PROACTIVE_OUTREACH',
                'priority': 'HIGH',
                'urgency': 'urgent',
                'message': (
                    f'{client_id} showing very high switch probability ({switch_prob:.0%}). '
                    f'URGENT: Immediate relationship manager intervention required to prevent churn.'
                ),
                'products': self._get_segment_products(segment, 'high_switch'),
                'suggested_actions': [
                    'Call client TODAY to discuss concerns',
                    'Prepare detailed portfolio analysis showing risks',
                    'Present alternative strategy scenarios with specific products',
                    'Schedule in-person meeting if possible'
                ],
                'reasoning': (
                    f'Switch probability {switch_prob:.0%} is in critical range (>65%). '
                    f'Client is highly likely to change strategy or churn within 14 days. '
                    f'Immediate proactive engagement is critical.'
                ),
                'timestamp': timestamp
            })
        
        # Rule 2: High switch probability
        elif switch_prob > 0.50:
            recommendations.append({
                'action': 'PROACTIVE_OUTREACH',
                'priority': 'HIGH',
                'urgency': 'high',
                'message': (
                    f'{client_id} showing elevated switch probability ({switch_prob:.0%}). '
                    f'Proactive relationship manager contact recommended within 48 hours.'
                ),
                'products': self._get_segment_products(segment, 'high_switch'),
                'suggested_actions': [
                    'Schedule strategy review call within 48 hours',
                    'Prepare client concentration and risk analysis',
                    'Present hedging and diversification options',
                    'Discuss recent market moves affecting their positions'
                ],
                'reasoning': (
                    f'Switch probability {switch_prob:.0%} indicates elevated churn risk. '
                    f'Client may be reconsidering strategy. Early intervention can prevent departure.'
                ),
                'timestamp': timestamp
            })
        
        # Rule 3: Significant risk flags
        if risk_flags and len(risk_flags) > 2:
            recommendations.append({
                'action': 'PROPOSE_HEDGE',
                'priority': 'HIGH',
                'message': (
                    f'Multiple risk concerns identified for {client_id}: '
                    f'{", ".join(risk_flags[:3])}. Hedging products strongly recommended.'
                ),
                'products': self._get_segment_products(segment, 'hedge'),
                'suggested_actions': [
                    'Calculate optimal hedge ratio for primary exposures',
                    'Model cost-benefit scenarios (hedge vs no hedge)',
                    'Present hedging product comparison with pricing',
                    'Discuss client risk tolerance and objectives'
                ],
                'reasoning': (
                    f'{len(risk_flags)} risk flags indicate elevated portfolio risk. '
                    f'Key concerns: {", ".join(risk_flags[:2])}. Hedging can mitigate downside.'
                ),
                'timestamp': timestamp
            })
        
        # Rule 4: Some risk flags
        elif risk_flags:
            recommendations.append({
                'action': 'PROPOSE_HEDGE',
                'priority': 'MEDIUM',
                'message': (
                    f'Risk concern identified for {client_id}: {risk_flags[0]}. '
                    f'Hedging may be appropriate.'
                ),
                'products': self._get_segment_products(segment, 'hedge'),
                'suggested_actions': [
                    'Review risk exposure in detail',
                    'Prepare hedging cost analysis',
                    'Discuss with client at next check-in'
                ],
                'reasoning': f'Risk flag "{risk_flags[0]}" warrants hedging consideration.',
                'timestamp': timestamp
            })
        
        # Rule 5: Medium switch probability OR high media pressure
        if switch_prob > 0.35 or media_pressure == 'HIGH':
            if not any(r['action'] == 'PROACTIVE_OUTREACH' for r in recommendations):
                recommendations.append({
                    'action': 'ENHANCED_MONITORING',
                    'priority': 'MEDIUM',
                    'message': (
                        f'{client_id} showing moderate instability '
                        f'(switch prob: {switch_prob:.0%}, media: {media_pressure}). '
                        f'Enhanced monitoring advised.'
                    ),
                    'products': self._get_segment_products(segment, 'monitoring'),
                    'suggested_actions': [
                        'Set up daily monitoring alerts for position changes',
                        'Review client activity weekly',
                        'Prepare contingency product recommendations',
                        'Watch for further deterioration signals'
                    ],
                    'reasoning': (
                        f'Switch probability {switch_prob:.0%} or media pressure {media_pressure} '
                        f'warrants closer attention. Early detection prevents escalation.'
                    ),
                    'timestamp': timestamp
                })
        
        # Rule 6: High media pressure (if not already covered)
        if media_pressure == 'HIGH' and len(recommendations) < 2:
            recommendations.append({
                'action': 'SEND_MARKET_UPDATE',
                'priority': 'LOW',
                'message': (
                    f'High media pressure detected on {client_id}\'s exposures. '
                    f'Market update recommended to demonstrate expertise.'
                ),
                'products': ['Market research report', 'Trading desk insights', 'Webinar invitation'],
                'suggested_actions': [
                    'Share recent research on relevant instruments',
                    'Provide trading desk commentary on market moves',
                    'Offer call to discuss market outlook'
                ],
                'reasoning': (
                    f'High media activity on client exposures. Proactive communication '
                    f'builds trust and positions firm as expert.'
                ),
                'timestamp': timestamp
            })
        
        # Rule 7: Stable client - opportunity
        if switch_prob < 0.35 and not risk_flags and not recommendations:
            recommendations.append({
                'action': 'SUGGEST_OPPORTUNITY',
                'priority': 'LOW',
                'message': (
                    f'{client_id} showing stable {segment} behavior (switch prob: {switch_prob:.0%}). '
                    f'Good opportunity to deepen relationship with value-add products.'
                ),
                'products': self._get_segment_products(segment, 'opportunity'),
                'suggested_actions': [
                    'Schedule quarterly relationship review meeting',
                    'Prepare portfolio enhancement product overview',
                    'Share case study of similar client success',
                    'Discuss additional services firm can provide'
                ],
                'reasoning': (
                    f'Stable client (switch prob {switch_prob:.0%}) with predictable {segment} '
                    f'strategy is receptive to value-add enhancements. Low risk of disrupting relationship.'
                ),
                'timestamp': timestamp
            })
        
        # Ensure we have at least one recommendation
        if not recommendations:
            recommendations.append({
                'action': 'ENHANCED_MONITORING',
                'priority': 'LOW',
                'message': f'Standard monitoring for {client_id}.',
                'products': ['Monitoring alerts'],
                'suggested_actions': ['Continue regular monitoring'],
                'reasoning': 'No significant concerns detected.',
                'timestamp': timestamp
            })
        
        # Limit to 3 fallback recommendations
        return recommendations[:3]
    
    def _get_segment_products(self, segment: str, scenario: str) -> List[str]:
        """
        Get segment-specific product suggestions for a given scenario.
        
        Playbooks aligned with business spec:
        - Trend Follower: Momentum products, forward strips, options collars
        - Mean Reverter: Range products, volatility strategies, pairs trading
        - Hedger: Hedging programs, basis swaps, tail risk protection
        - Trend Setter: Alpha strategies, thematic products, smart beta
        
        Args:
            segment: Client segment (Trend Follower, Mean Reverter, Hedger, Trend Setter)
            scenario: Scenario type (high_switch, hedge, monitoring, opportunity)
            
        Returns:
            List of 2-4 specific product suggestions
        """
        # Comprehensive playbook (per business spec)
        playbook = {
            'Trend Follower': {
                'high_switch': [
                    'EURUSD forward strips (3-month ladder structure)',
                    'Options collars to protect current profits',
                    'Dynamic delta hedging program',
                    'Momentum-based algorithmic strategy'
                ],
                'hedge': [
                    'Stop-loss overlays on major positions',
                    'Profit-taking automation triggers',
                    'Trailing stop strategies',
                    'Diversification into uncorrelated pairs'
                ],
                'monitoring': [
                    'Momentum tracking alerts',
                    'Trend reversal detection',
                    'Position size recommendations'
                ],
                'opportunity': [
                    'Enhanced momentum products',
                    'Breakout detection algorithms',
                    'Systematic trend-following fund',
                    'Momentum factor ETF strategies'
                ]
            },
            'Mean Reverter': {
                'high_switch': [
                    'Range-bound structured products',
                    'Volatility products (straddles/strangles)',
                    'Statistical arbitrage strategies',
                    'Mean-reversion algorithms'
                ],
                'hedge': [
                    'Position size limiters',
                    'Correlation hedges',
                    'Market-neutral overlays',
                    'Stop-loss on range breaches'
                ],
                'monitoring': [
                    'Range breach alerts',
                    'Correlation breakdown detection',
                    'Mean reversion opportunity signals'
                ],
                'opportunity': [
                    'Relative value strategies',
                    'Pairs trading programs',
                    'Convertible arbitrage',
                    'Statistical arbitrage fund'
                ]
            },
            'Hedger': {
                'high_switch': [
                    'Dynamic hedging programs',
                    'Basis swaps and cross-hedges',
                    'Options-based protection',
                    'Multi-asset hedging baskets'
                ],
                'hedge': [
                    'Static hedge overlays',
                    'Tail risk protection (put spreads)',
                    'Comprehensive hedging review',
                    'Natural hedges identification'
                ],
                'monitoring': [
                    'Hedge effectiveness tracking',
                    'Basis risk monitoring',
                    'Hedge rebalancing alerts'
                ],
                'opportunity': [
                    'Hedge optimization strategies',
                    'Cost-reduction overlays',
                    'Natural hedges identification',
                    'Hedging efficiency analysis'
                ]
            },
            'Trend Setter': {
                'high_switch': [
                    'Alpha-generation strategies',
                    'Thematic investment products',
                    'Systematic trend identification',
                    'Leading indicator strategies'
                ],
                'hedge': [
                    'Portfolio diversification review',
                    'Factor exposure management',
                    'Risk parity approaches',
                    'Tail risk hedging'
                ],
                'monitoring': [
                    'Leading indicator alerts',
                    'Factor exposure tracking',
                    'Alpha decay monitoring'
                ],
                'opportunity': [
                    'Alternative alpha sources',
                    'Smart beta strategies',
                    'Proprietary signal integration',
                    'Multi-factor investment strategies'
                ]
            }
        }
        
        # Get products for segment + scenario
        products = playbook.get(segment, {}).get(scenario, [])
        
        # Fallback if segment not found
        if not products:
            logger.warning(f"No products found for segment={segment}, scenario={scenario}")
            products = [
                'Customized hedging solutions',
                'Portfolio optimization strategies',
                'Risk management products'
            ]
        
        # Return 2-4 products
        return products[:4]
