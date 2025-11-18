"""
Feature #3: Improvement Simulator
Predict how visibility score would change with brand improvements
"""

import os
from typing import List, Dict, Any
from openai import OpenAI
import random


class ImprovementSimulator:
    """Simulate visibility improvements based on brand changes"""
    
    def __init__(self, brand_name: str, industry: str, current_score: float):
        self.brand_name = brand_name
        self.industry = industry
        self.current_score = current_score
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def simulate_improvement(
        self,
        results: List[Dict[str, Any]],
        improvements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate how visibility would improve with given changes
        
        improvements: {
            'new_tagline': str,
            'new_features': List[str],
            'new_keywords': List[str],
            'page_updates': List[str],
            'pricing_strategy': str
        }
        """
        # Analyze current gaps
        gap_analysis = self._analyze_gaps(results)
        
        # Calculate impact of each improvement
        impact_analysis = self._calculate_impacts(improvements, gap_analysis, results)
        
        # Predict new score
        predicted_score = self._predict_new_score(impact_analysis)
        
        # Generate timeline
        timeline = self._generate_timeline(impact_analysis, predicted_score)
        
        # Generate actionable recommendations
        recommendations = self._generate_recommendations(impact_analysis, gap_analysis)
        
        return {
            'current_score': round(self.current_score, 1),
            'predicted_score': round(predicted_score, 1),
            'improvement_delta': round(predicted_score - self.current_score, 1),
            'percentage_increase': round((predicted_score - self.current_score) / self.current_score * 100, 1),
            'impact_breakdown': impact_analysis,
            'timeline': timeline,
            'recommendations': recommendations,
            'confidence': self._calculate_confidence(improvements, gap_analysis)
        }
    
    def _analyze_gaps(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze what's missing from current brand"""
        non_mentions = [r for r in results if not r.get('mentioned', False)]
        
        # Extract themes from non-mention queries
        missing_themes = {
            'pricing': 0,
            'features': 0,
            'trust': 0,
            'availability': 0,
            'quality': 0,
            'sustainability': 0
        }
        
        for result in non_mentions:
            query_lower = result.get('query', '').lower()
            
            if any(kw in query_lower for kw in ['cheap', 'affordable', 'budget', 'price']):
                missing_themes['pricing'] += 1
            if any(kw in query_lower for kw in ['feature', 'option', 'variety']):
                missing_themes['features'] += 1
            if any(kw in query_lower for kw in ['trust', 'review', 'reliable', 'popular']):
                missing_themes['trust'] += 1
            if any(kw in query_lower for kw in ['delivery', 'shipping', 'fast', 'available']):
                missing_themes['availability'] += 1
            if any(kw in query_lower for kw in ['best', 'quality', 'premium']):
                missing_themes['quality'] += 1
            if any(kw in query_lower for kw in ['eco', 'organic', 'sustainable']):
                missing_themes['sustainability'] += 1
        
        return {
            'missing_themes': missing_themes,
            'non_mention_count': len(non_mentions),
            'total_queries': len(results)
        }
    
    def _calculate_impacts(
        self,
        improvements: Dict[str, Any],
        gap_analysis: Dict,
        results: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Calculate impact of each improvement"""
        impacts = []
        
        # Tagline impact
        if improvements.get('new_tagline'):
            impact = self._assess_tagline_impact(
                improvements['new_tagline'],
                gap_analysis,
                results
            )
            impacts.append(impact)
        
        # Features impact
        if improvements.get('new_features'):
            impact = self._assess_features_impact(
                improvements['new_features'],
                gap_analysis
            )
            impacts.append(impact)
        
        # Keywords impact
        if improvements.get('new_keywords'):
            impact = self._assess_keywords_impact(
                improvements['new_keywords'],
                gap_analysis
            )
            impacts.append(impact)
        
        # Page updates impact
        if improvements.get('page_updates'):
            impact = self._assess_page_updates_impact(
                improvements['page_updates'],
                gap_analysis
            )
            impacts.append(impact)
        
        # Pricing strategy impact
        if improvements.get('pricing_strategy'):
            impact = self._assess_pricing_impact(
                improvements['pricing_strategy'],
                gap_analysis
            )
            impacts.append(impact)
        
        return impacts
    
    def _assess_tagline_impact(self, tagline: str, gap_analysis: Dict, results: List[Dict]) -> Dict:
        """Use AI to assess tagline effectiveness"""
        # Get common query themes
        query_sample = [r['query'] for r in results[:10]]
        
        prompt = f"""Analyze this new tagline for {self.brand_name} in the {self.industry} industry:

Tagline: "{tagline}"

Sample queries where brand currently struggles:
{chr(10).join(f"- {q}" for q in query_sample[:5])}

Rate the effectiveness of this tagline on a scale of 1-10 for:
1. Addressing market gaps
2. Memorability
3. SEO value
4. Competitive differentiation

Provide overall impact score (1-10) and brief explanation (2 sentences)."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a brand strategy expert. Provide numerical ratings and concise analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            analysis = response.choices[0].message.content.strip()
            
            # Extract score (simple parsing)
            score = 7.0  # Default
            if 'score' in analysis.lower() or '/' in analysis:
                import re
                numbers = re.findall(r'(\d+(?:\.\d+)?)\s*(?:/\s*10|out of 10)', analysis)
                if numbers:
                    score = float(numbers[0])
            
        except Exception as e:
            print(f"Error assessing tagline: {e}")
            score = 6.5
            analysis = "New tagline provides moderate improvement in brand positioning."
        
        return {
            'improvement_type': 'Tagline Update',
            'description': f'New tagline: "{tagline}"',
            'impact_score': score,
            'visibility_boost': round(score * 1.5, 1),  # 1.5% boost per point
            'explanation': analysis,
            'affected_queries': int(len(results) * 0.3)  # Affects ~30% of queries
        }
    
    def _assess_features_impact(self, features: List[str], gap_analysis: Dict) -> Dict:
        """Assess impact of new features"""
        feature_gap = gap_analysis['missing_themes'].get('features', 0)
        
        impact_score = min(10, len(features) * 2 + (feature_gap * 0.5))
        visibility_boost = impact_score * 1.2
        
        return {
            'improvement_type': 'New Features',
            'description': f'Adding {len(features)} new features: {", ".join(features[:3])}',
            'impact_score': round(impact_score, 1),
            'visibility_boost': round(visibility_boost, 1),
            'explanation': f'New features address {feature_gap} queries where brand lacked functionality. Expected to improve feature-focused query performance.',
            'affected_queries': feature_gap + int(gap_analysis['total_queries'] * 0.15)
        }
    
    def _assess_keywords_impact(self, keywords: List[str], gap_analysis: Dict) -> Dict:
        """Assess SEO keyword impact"""
        impact_score = min(10, len(keywords) * 1.5)
        visibility_boost = impact_score * 2.0  # Keywords have high impact
        
        return {
            'improvement_type': 'SEO Keywords',
            'description': f'Targeting {len(keywords)} new keywords: {", ".join(keywords[:3])}',
            'impact_score': round(impact_score, 1),
            'visibility_boost': round(visibility_boost, 1),
            'explanation': f'Strong SEO optimization. Keywords directly target queries where brand is absent. High potential for AI model indexing.',
            'affected_queries': int(gap_analysis['total_queries'] * 0.4)
        }
    
    def _assess_page_updates_impact(self, pages: List[str], gap_analysis: Dict) -> Dict:
        """Assess content page impact"""
        impact_score = min(10, len(pages) * 2.5)
        visibility_boost = impact_score * 1.8
        
        return {
            'improvement_type': 'Content Pages',
            'description': f'Creating {len(pages)} new pages: {", ".join(pages[:2])}',
            'impact_score': round(impact_score, 1),
            'visibility_boost': round(visibility_boost, 1),
            'explanation': f'New dedicated pages improve AI model awareness. Comparison and guide pages especially effective for visibility.',
            'affected_queries': int(gap_analysis['total_queries'] * 0.35)
        }
    
    def _assess_pricing_impact(self, strategy: str, gap_analysis: Dict) -> Dict:
        """Assess pricing strategy change impact"""
        pricing_gap = gap_analysis['missing_themes'].get('pricing', 0)
        
        impact_score = 8.0 if pricing_gap > 5 else 5.0
        visibility_boost = impact_score * 1.3
        
        return {
            'improvement_type': 'Pricing Strategy',
            'description': f'New pricing: {strategy}',
            'impact_score': round(impact_score, 1),
            'visibility_boost': round(visibility_boost, 1),
            'explanation': f'Pricing is mentioned in {pricing_gap} non-mention queries. Strategy adjustment addresses this gap directly.',
            'affected_queries': pricing_gap
        }
    
    def _predict_new_score(self, impacts: List[Dict]) -> float:
        """Calculate predicted new score"""
        total_boost = sum(impact['visibility_boost'] for impact in impacts)
        
        # Apply diminishing returns
        effective_boost = total_boost * 0.7 if total_boost > 15 else total_boost
        
        new_score = min(100, self.current_score + effective_boost)
        
        return new_score
    
    def _generate_timeline(self, impacts: List[Dict], final_score: float) -> List[Dict]:
        """Generate improvement timeline"""
        timeline = [
            {
                'timeframe': 'Current',
                'score': round(self.current_score, 1),
                'changes': 'Baseline visibility'
            }
        ]
        
        # Sort impacts by implementation difficulty (features > pages > keywords > tagline)
        priority_order = ['Tagline Update', 'SEO Keywords', 'Content Pages', 'New Features', 'Pricing Strategy']
        sorted_impacts = sorted(impacts, key=lambda x: priority_order.index(x['improvement_type']) if x['improvement_type'] in priority_order else 999)
        
        cumulative_score = self.current_score
        timeframes = ['Week 1-2', 'Week 3-4', 'Month 2', 'Month 3']
        
        for i, impact in enumerate(sorted_impacts[:4]):
            cumulative_score += impact['visibility_boost'] * 0.7  # Diminishing returns
            cumulative_score = min(100, cumulative_score)
            
            timeline.append({
                'timeframe': timeframes[i] if i < len(timeframes) else f'Month {i}',
                'score': round(cumulative_score, 1),
                'changes': impact['improvement_type']
            })
        
        return timeline
    
    def _generate_recommendations(self, impacts: List[Dict], gap_analysis: Dict) -> List[str]:
        """Generate prioritized recommendations"""
        recommendations = []
        
        # Sort by impact
        sorted_impacts = sorted(impacts, key=lambda x: x['visibility_boost'], reverse=True)
        
        for impact in sorted_impacts[:3]:
            recommendations.append(
                f"Priority: {impact['improvement_type']} - Expected +{impact['visibility_boost']}% visibility. {impact['explanation'][:100]}"
            )
        
        return recommendations
    
    def _calculate_confidence(self, improvements: Dict, gap_analysis: Dict) -> str:
        """Calculate confidence level"""
        improvement_count = sum(1 for v in improvements.values() if v)
        gap_coverage = improvement_count / max(len(gap_analysis['missing_themes']), 1)
        
        if gap_coverage > 0.7:
            return "High (75-90%)"
        elif gap_coverage > 0.4:
            return "Medium (60-75%)"
        else:
            return "Low (40-60%)"


if __name__ == "__main__":
    # Test
    simulator = ImprovementSimulator("TestBrand", "Meal Kit", 45.0)
    
    improvements = {
        'new_tagline': 'Affordable gourmet meals delivered daily',
        'new_features': ['Custom meal plans', 'Dietary filters', 'Recipe library'],
        'new_keywords': ['budget meal kit', 'affordable delivery', 'healthy cheap meals']
    }
    
    test_results = []
    
    result = simulator.simulate_improvement(test_results, improvements)
    print("Simulation:", result)
