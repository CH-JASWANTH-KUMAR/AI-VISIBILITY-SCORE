"""
Feature #2: AI-Powered Competitor Reverse Engineering
Ask AI models WHY they chose specific competitors
"""

import os
from typing import List, Dict, Any
from openai import OpenAI
from collections import Counter


class CompetitorInsights:
    """Reverse-engineer competitor strategies by asking AI why they were chosen"""
    
    def __init__(self, brand_name: str, industry: str):
        self.brand_name = brand_name
        self.industry = industry
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def analyze_competitors(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        For each competitor, ask AI WHY they were chosen
        Returns strategic insights about each competitor
        """
        # Get all mentioned competitors
        competitor_mentions = self._extract_competitor_mentions(results)
        
        if not competitor_mentions:
            return {
                'total_competitors': 0,
                'insights': [],
                'summary': 'No competitors detected in responses.'
            }
        
        # Get insights for top competitors
        top_competitors = self._get_top_competitors(competitor_mentions, 8)
        
        insights = []
        for competitor, data in top_competitors.items():
            insight = self._get_competitor_insight(competitor, data)
            insights.append(insight)
        
        # Generate dominance patterns
        patterns = self._identify_patterns(insights)
        
        # Generate strategic summary
        summary = self._generate_strategic_summary(insights, patterns)
        
        return {
            'total_competitors': len(competitor_mentions),
            'top_competitors_analyzed': len(insights),
            'insights': insights,
            'dominance_patterns': patterns,
            'strategic_summary': summary
        }
    
    def _extract_competitor_mentions(self, results: List[Dict]) -> Dict[str, List[Dict]]:
        """Extract all competitor mentions with context"""
        mentions = {}
        
        for result in results:
            competitors = result.get('competitors', [])
            
            for comp in competitors:
                if comp not in mentions:
                    mentions[comp] = []
                
                mentions[comp].append({
                    'query': result.get('query', ''),
                    'response': result.get('response', ''),
                    'rank': result.get('rank'),
                    'model': result.get('model', ''),
                    'intent_category': result.get('intent_category', '')
                })
        
        return mentions
    
    def _get_top_competitors(self, competitor_mentions: Dict, n: int) -> Dict[str, List]:
        """Get top N competitors by mention frequency"""
        sorted_competitors = sorted(
            competitor_mentions.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        return dict(sorted_competitors[:n])
    
    def _get_competitor_insight(self, competitor: str, mentions: List[Dict]) -> Dict[str, Any]:
        """Ask AI why this competitor was chosen"""
        # Get sample contexts
        sample_queries = [m['query'] for m in mentions[:5]]
        sample_responses = [m['response'][:300] for m in mentions[:3]]
        
        # Analyze query categories
        categories = [m['intent_category'] for m in mentions if m.get('intent_category')]
        category_distribution = Counter(categories)
        
        # Ask AI for strategic insight
        prompt = f"""Analyze why "{competitor}" is frequently recommended in the {self.industry} industry.

Sample queries where {competitor} appeared:
{chr(10).join(f"- {q}" for q in sample_queries)}

Sample AI responses:
{chr(10).join(sample_responses)}

Identify the KEY strategic advantages that make {competitor} stand out. Focus on:
1. Brand positioning (price, quality, niche)
2. Specific strengths (features, trust signals, SEO)
3. Market advantages

Provide 2-3 concise strategic insights. Be specific and actionable."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a competitive intelligence analyst. Provide sharp, strategic insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            strategy = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error getting competitor insight: {e}")
            strategy = f"{competitor} appears frequently in {len(mentions)} queries, suggesting strong market presence and brand recognition."
        
        # Identify dominance areas
        dominance_areas = self._identify_dominance_areas(mentions)
        
        return {
            'competitor_name': competitor,
            'mention_count': len(mentions),
            'strategic_insight': strategy,
            'dominance_areas': dominance_areas,
            'category_distribution': dict(category_distribution.most_common(5)),
            'average_rank': self._calculate_avg_rank(mentions),
            'key_strength': self._extract_key_strength(strategy)
        }
    
    def _identify_dominance_areas(self, mentions: List[Dict]) -> List[str]:
        """Identify where competitor dominates"""
        query_keywords = ' '.join([m['query'].lower() for m in mentions])
        
        areas = []
        
        # Price/Budget
        if any(kw in query_keywords for kw in ['cheap', 'affordable', 'budget', 'low cost', 'inexpensive']):
            areas.append('Budget/Affordability')
        
        # Quality/Premium
        if any(kw in query_keywords for kw in ['best', 'premium', 'luxury', 'high-quality', 'top']):
            areas.append('Quality/Premium')
        
        # Features
        if any(kw in query_keywords for kw in ['feature', 'option', 'variety', 'customizable']):
            areas.append('Features/Variety')
        
        # Speed/Delivery
        if any(kw in query_keywords for kw in ['fast', 'quick', 'delivery', 'shipping', 'express']):
            areas.append('Speed/Delivery')
        
        # Trust/Reviews
        if any(kw in query_keywords for kw in ['trusted', 'reliable', 'review', 'rating', 'popular']):
            areas.append('Trust/Authority')
        
        # Sustainability
        if any(kw in query_keywords for kw in ['eco', 'organic', 'sustainable', 'green', 'natural']):
            areas.append('Sustainability')
        
        # Convenience
        if any(kw in query_keywords for kw in ['easy', 'convenient', 'simple', 'hassle-free']):
            areas.append('Convenience')
        
        return areas if areas else ['General Market Presence']
    
    def _calculate_avg_rank(self, mentions: List[Dict]) -> float:
        """Calculate average ranking position"""
        ranks = [m['rank'] for m in mentions if m.get('rank') is not None]
        return round(sum(ranks) / len(ranks), 1) if ranks else 0
    
    def _extract_key_strength(self, strategy_text: str) -> str:
        """Extract primary strength from strategy text"""
        strength_keywords = {
            'pricing': ['price', 'affordable', 'budget', 'cheap', 'cost'],
            'quality': ['quality', 'premium', 'best', 'excellent'],
            'features': ['feature', 'option', 'variety', 'selection'],
            'trust': ['trust', 'reliable', 'reputation', 'review', 'popular'],
            'innovation': ['innovative', 'technology', 'modern', 'advanced'],
            'service': ['service', 'support', 'customer', 'experience'],
            'availability': ['available', 'accessible', 'coverage', 'delivery']
        }
        
        strategy_lower = strategy_text.lower()
        
        for strength, keywords in strength_keywords.items():
            if any(kw in strategy_lower for kw in keywords):
                return strength.capitalize()
        
        return 'Brand Authority'
    
    def _identify_patterns(self, insights: List[Dict]) -> Dict[str, Any]:
        """Identify patterns across competitors"""
        all_areas = []
        all_strengths = []
        
        for insight in insights:
            all_areas.extend(insight['dominance_areas'])
            all_strengths.append(insight['key_strength'])
        
        area_counts = Counter(all_areas)
        strength_counts = Counter(all_strengths)
        
        return {
            'most_competitive_areas': [
                {'area': area, 'competitor_count': count}
                for area, count in area_counts.most_common(5)
            ],
            'common_strengths': [
                {'strength': strength, 'frequency': count}
                for strength, count in strength_counts.most_common(5)
            ]
        }
    
    def _generate_strategic_summary(self, insights: List[Dict], patterns: Dict) -> str:
        """Generate executive summary of competitive landscape"""
        if not insights:
            return "No competitive insights available."
        
        top_competitor = insights[0]['competitor_name']
        top_mentions = insights[0]['mention_count']
        top_areas = ', '.join(insights[0]['dominance_areas'][:2])
        
        competitive_area = patterns['most_competitive_areas'][0]['area'] if patterns['most_competitive_areas'] else 'general market'
        
        summary = f"{top_competitor} leads with {top_mentions} mentions, dominating {top_areas}. "
        summary += f"The most competitive area is {competitive_area}. "
        
        # Check if brand has gap
        summary += f"{self.brand_name} needs to differentiate in less saturated segments or outcompete in {competitive_area}."
        
        return summary


if __name__ == "__main__":
    # Test
    analyzer = CompetitorInsights("TestBrand", "Meal Kit")
    
    test_results = [
        {
            'query': 'Best affordable meal kits',
            'competitors': ['HelloFresh', 'Blue Apron'],
            'response': 'HelloFresh offers budget-friendly options with great variety.',
            'model': 'ChatGPT',
            'intent_category': 'Price Comparison'
        }
    ]
    
    analysis = analyzer.analyze_competitors(test_results)
    print("Competitor Insights:", analysis)
