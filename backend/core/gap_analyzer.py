"""
Feature #1: Why You Were NOT Mentioned Analysis
Analyzes responses to identify WHY brand wasn't mentioned and what competitors have that brand lacks
"""

import re
from typing import List, Dict, Any
from openai import OpenAI
import os


class GapAnalyzer:
    """Analyzes gaps between brand and competitors when brand is not mentioned"""
    
    def __init__(self, brand_name: str):
        self.brand_name = brand_name
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Theme categories to analyze
        self.themes = [
            'pricing', 'affordability', 'budget',
            'quality', 'premium', 'luxury',
            'availability', 'shipping', 'delivery',
            'features', 'functionality', 'options',
            'reviews', 'ratings', 'trust', 'reputation',
            'sustainability', 'eco-friendly', 'organic',
            'convenience', 'ease-of-use', 'simple',
            'variety', 'selection', 'choice',
            'customer service', 'support', 'warranty',
            'innovation', 'technology', 'modern'
        ]
    
    def analyze_non_mentions(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze all queries where brand was NOT mentioned
        Returns gap analysis with reasons
        """
        non_mentions = [r for r in results if not r.get('mentioned', False)]
        
        if not non_mentions:
            return {
                'total_non_mentions': 0,
                'reasons': [],
                'theme_gaps': {},
                'summary': f'{self.brand_name} was mentioned in all queries!'
            }
        
        # Extract themes from competitor answers
        theme_analysis = self._extract_themes(non_mentions)
        
        # Generate reasons using AI
        reasons = self._generate_reasons(non_mentions, theme_analysis)
        
        # Calculate theme gaps
        theme_gaps = self._calculate_theme_gaps(theme_analysis)
        
        # Generate executive summary
        summary = self._generate_summary(len(non_mentions), len(results), theme_gaps)
        
        return {
            'total_non_mentions': len(non_mentions),
            'total_queries': len(results),
            'non_mention_rate': round(len(non_mentions) / len(results) * 100, 1),
            'reasons': reasons,
            'theme_gaps': theme_gaps,
            'summary': summary,
            'top_missing_themes': self._get_top_themes(theme_gaps, 5)
        }
    
    def _extract_themes(self, non_mentions: List[Dict]) -> Dict[str, List[str]]:
        """Extract what themes competitors emphasize in responses"""
        theme_mentions = {theme: [] for theme in self.themes}
        
        for result in non_mentions:
            response = result.get('response', '').lower()
            competitors = result.get('competitors', [])
            query = result.get('query', '')
            
            # Check which themes appear in response
            for theme in self.themes:
                if theme in response:
                    theme_mentions[theme].append({
                        'query': query,
                        'competitors': competitors,
                        'context': self._extract_context(response, theme)
                    })
        
        return theme_mentions
    
    def _extract_context(self, text: str, keyword: str, window: int = 100) -> str:
        """Extract surrounding context for a keyword"""
        idx = text.find(keyword)
        if idx == -1:
            return ""
        
        start = max(0, idx - window)
        end = min(len(text), idx + len(keyword) + window)
        return text[start:end].strip()
    
    def _calculate_theme_gaps(self, theme_analysis: Dict) -> Dict[str, Any]:
        """Calculate which themes brand is missing"""
        gaps = {}
        
        for theme, mentions in theme_analysis.items():
            if len(mentions) > 0:
                gaps[theme] = {
                    'frequency': len(mentions),
                    'percentage': round(len(mentions) / len(theme_analysis) * 100, 1),
                    'examples': mentions[:3]  # Top 3 examples
                }
        
        return dict(sorted(gaps.items(), key=lambda x: x[1]['frequency'], reverse=True))
    
    def _generate_reasons(self, non_mentions: List[Dict], theme_analysis: Dict) -> List[Dict[str, str]]:
        """Use AI to generate human-readable reasons for non-mentions"""
        reasons = []
        
        # Group by similar queries
        query_groups = self._group_similar_queries(non_mentions)
        
        for group_name, queries in list(query_groups.items())[:5]:  # Top 5 groups
            # Get sample query and response
            sample = queries[0]
            
            prompt = f"""Analyze why the brand "{self.brand_name}" was NOT mentioned in this AI response.

Query: {sample['query']}

AI Response: {sample['response'][:1000]}

Competitors Mentioned: {', '.join(sample.get('competitors', [])[:5])}

Provide a concise, actionable reason (2-3 sentences) explaining:
1. What competitors emphasized that {self.brand_name} likely lacks
2. Specific positioning gap or weakness

Format: Direct, businesslike, actionable."""

            try:
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a brand strategy analyst. Provide direct, actionable insights."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                
                reason_text = response.choices[0].message.content.strip()
                
                reasons.append({
                    'query_category': group_name,
                    'query_count': len(queries),
                    'reason': reason_text,
                    'sample_query': sample['query']
                })
            except Exception as e:
                print(f"Error generating reason: {e}")
                reasons.append({
                    'query_category': group_name,
                    'query_count': len(queries),
                    'reason': f"Competitors dominated this query category. {self.brand_name} may lack visibility or relevant positioning.",
                    'sample_query': sample['query']
                })
        
        return reasons
    
    def _group_similar_queries(self, results: List[Dict]) -> Dict[str, List[Dict]]:
        """Group queries by category/intent"""
        groups = {
            'Price/Budget': [],
            'Quality/Premium': [],
            'Delivery/Speed': [],
            'Features/Options': [],
            'Reviews/Trust': [],
            'Sustainability': [],
            'Convenience': [],
            'General': []
        }
        
        keywords = {
            'Price/Budget': ['cheap', 'affordable', 'budget', 'cost', 'price', 'inexpensive'],
            'Quality/Premium': ['best', 'quality', 'premium', 'luxury', 'top', 'high-end'],
            'Delivery/Speed': ['fast', 'delivery', 'shipping', 'quick', 'express'],
            'Features/Options': ['feature', 'option', 'variety', 'selection', 'choice'],
            'Reviews/Trust': ['review', 'rating', 'trusted', 'reliable', 'popular'],
            'Sustainability': ['eco', 'organic', 'sustainable', 'green', 'natural'],
            'Convenience': ['easy', 'convenient', 'simple', 'hassle-free']
        }
        
        for result in results:
            query_lower = result.get('query', '').lower()
            categorized = False
            
            for category, kw_list in keywords.items():
                if any(kw in query_lower for kw in kw_list):
                    groups[category].append(result)
                    categorized = True
                    break
            
            if not categorized:
                groups['General'].append(result)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _get_top_themes(self, theme_gaps: Dict, n: int) -> List[Dict]:
        """Get top N missing themes"""
        sorted_themes = sorted(
            theme_gaps.items(),
            key=lambda x: x[1]['frequency'],
            reverse=True
        )
        
        return [
            {
                'theme': theme,
                'frequency': data['frequency'],
                'impact': 'High' if data['frequency'] > 5 else 'Medium' if data['frequency'] > 2 else 'Low'
            }
            for theme, data in sorted_themes[:n]
        ]
    
    def _generate_summary(self, non_mentions: int, total: int, theme_gaps: Dict) -> str:
        """Generate executive summary"""
        if not theme_gaps:
            return f"{self.brand_name} appears to have strong visibility. No major gaps detected."
        
        top_gap = list(theme_gaps.keys())[0] if theme_gaps else 'positioning'
        rate = round(non_mentions / total * 100, 1)
        
        return f"{self.brand_name} was not mentioned in {rate}% of queries. The primary gap is '{top_gap}' - competitors consistently emphasize this while your brand positioning may lack clarity in this area. Consider strengthening messaging around {', '.join(list(theme_gaps.keys())[:3])}."


if __name__ == "__main__":
    # Test
    analyzer = GapAnalyzer("TestBrand")
    
    test_results = [
        {
            'query': 'What are the best affordable meal kits?',
            'mentioned': False,
            'response': 'HelloFresh and Blue Apron are great budget options with prices starting at $7/serving. They offer affordable meal plans.',
            'competitors': ['HelloFresh', 'Blue Apron']
        },
        {
            'query': 'Best eco-friendly meal delivery',
            'mentioned': False,
            'response': 'Green Chef uses organic ingredients and sustainable packaging.',
            'competitors': ['Green Chef']
        }
    ]
    
    analysis = analyzer.analyze_non_mentions(test_results)
    print("Gap Analysis:", analysis)
