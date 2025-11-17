"""
Visibility Scorer Module
Calculates visibility scores and competitive metrics
"""

import numpy as np
from collections import defaultdict


class VisibilityScorer:
    def __init__(self, brand_name):
        self.brand_name = brand_name
    
    def calculate_visibility_score(self, results):
        """
        Calculate overall visibility score (0-100)
        
        Scoring breakdown:
        - Mention frequency (40%)
        - Average ranking (30%)
        - Competitor dominance (20%)
        - Model consistency (10%)
        """
        
        if not results:
            return {
                "overall_score": 0,
                "mention_rate": 0,
                "rank_score": 0,
                "competitor_dominance": 0,
                "model_consistency": 0,
                "mentions": 0,
                "total_queries": 0
            }
        
        total_queries = len(results)
        mentions = sum(1 for r in results if r.get('mentioned', False))
        
        # 1. Mention rate (0-40 points)
        mention_rate = (mentions / total_queries) * 40 if total_queries > 0 else 0
        
        # 2. Average ranking (0-30 points)
        ranks = [r['rank'] for r in results if r.get('rank') is not None]
        if ranks:
            avg_rank = sum(ranks) / len(ranks)
            # Invert scoring: rank 1 = 30 points, rank 5 = 18 points, rank 10 = 3 points
            rank_score = max(0, 30 - (avg_rank - 1) * 3)
        else:
            rank_score = 0
        
        # 3. Competitor dominance (0-20 points)
        competitor_score = self.calculate_competitor_dominance(results)
        
        # 4. Model consistency (0-10 points)
        consistency_score = self.calculate_model_consistency(results)
        
        total_score = mention_rate + rank_score + competitor_score + consistency_score
        
        return {
            "overall_score": round(total_score, 2),
            "mention_rate": round(mention_rate, 2),
            "rank_score": round(rank_score, 2),
            "competitor_dominance": round(competitor_score, 2),
            "model_consistency": round(consistency_score, 2),
            "mentions": mentions,
            "total_queries": total_queries
        }
    
    def calculate_competitor_dominance(self, results):
        """
        Measure how often brand appears before competitors (0-20 points)
        Higher score = brand beats competitors more often
        """
        wins = 0
        total_comparisons = 0
        
        for result in results:
            if result.get('rank') and result.get('competitors'):
                # Check if we can extract competitor ranks
                response = result.get('response', '')
                brand_rank = result['rank']
                
                competitor_ranks = []
                for comp in result['competitors']:
                    comp_rank = self.extract_competitor_rank(response, comp)
                    if comp_rank:
                        competitor_ranks.append(comp_rank)
                
                if competitor_ranks:
                    total_comparisons += 1
                    # Count as win if brand ranks higher (lower number) than all competitors
                    if brand_rank < min(competitor_ranks):
                        wins += 1
                    # Partial credit if beats some competitors
                    elif brand_rank < max(competitor_ranks):
                        wins += 0.5
        
        if total_comparisons > 0:
            win_rate = wins / total_comparisons
            return win_rate * 20
        
        # Neutral score if no comparisons available
        return 10
    
    def calculate_model_consistency(self, results):
        """
        Measure consistency across different AI models (0-10 points)
        Lower variance in mention rates = higher consistency
        """
        model_mentions = defaultdict(lambda: {'mentioned': 0, 'total': 0})
        
        for result in results:
            model = result.get('model', 'Unknown')
            model_mentions[model]['total'] += 1
            if result.get('mentioned', False):
                model_mentions[model]['mentioned'] += 1
        
        # Calculate mention rates per model
        mention_rates = []
        for model_data in model_mentions.values():
            if model_data['total'] > 0:
                rate = model_data['mentioned'] / model_data['total']
                mention_rates.append(rate)
        
        if len(mention_rates) > 1:
            variance = np.var(mention_rates)
            # Lower variance = higher consistency
            # Variance ranges from 0 (perfect consistency) to 0.25 (maximum inconsistency)
            consistency = max(0, 10 - variance * 40)
            return consistency
        
        return 10  # Full points if only one model
    
    def extract_competitor_rank(self, text, competitor_name):
        """Extract rank for a specific competitor from text"""
        import re
        
        pattern = r'(\d+)[\.\)]\s*([^\n]+)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for rank, line in matches:
            if competitor_name.lower() in line.lower():
                return int(rank)
        
        return None
    
    def category_breakdown(self, results):
        """
        Break down scores by query category/intent
        """
        categories = defaultdict(list)
        
        for result in results:
            category = result.get('intent_category', 'Other')
            categories[category].append(result)
        
        breakdown = {}
        for category, cat_results in categories.items():
            breakdown[category] = self.calculate_visibility_score(cat_results)
        
        return breakdown
    
    def model_breakdown(self, results):
        """
        Break down scores by AI model
        """
        models = defaultdict(list)
        
        for result in results:
            model = result.get('model', 'Unknown')
            models[model].append(result)
        
        breakdown = {}
        for model, model_results in models.items():
            breakdown[model] = self.calculate_visibility_score(model_results)
        
        return breakdown
    
    def get_top_competitors(self, results, top_n=10):
        """
        Get most frequently mentioned competitors
        """
        competitor_counts = defaultdict(int)
        
        for result in results:
            competitors = result.get('competitors', [])
            for comp in competitors:
                competitor_counts[comp] += 1
        
        # Sort by frequency
        sorted_competitors = sorted(
            competitor_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return sorted_competitors[:top_n]
    
    def calculate_avg_rank(self, results):
        """Calculate average rank when brand is mentioned"""
        ranks = [r['rank'] for r in results if r.get('rank') is not None]
        return round(sum(ranks) / len(ranks), 2) if ranks else None
    
    def interpret_score(self, score):
        """Provide human-readable interpretation of visibility score"""
        if score >= 90:
            return "Dominant Presence", "Your brand consistently appears at the top of AI recommendations"
        elif score >= 70:
            return "Strong Visibility", "Your brand is frequently mentioned and well-ranked"
        elif score >= 50:
            return "Moderate Visibility", "Your brand appears regularly but with room for improvement"
        elif score >= 30:
            return "Low Visibility", "Your brand is rarely mentioned by AI models"
        else:
            return "Minimal Visibility", "Your brand has very limited presence in AI responses"


# Example usage
if __name__ == "__main__":
    scorer = VisibilityScorer("HelloFresh")
    
    # Sample results
    sample_results = [
        {
            "query": "Best meal kits for families",
            "model": "ChatGPT-4",
            "mentioned": True,
            "rank": 1,
            "competitors": ["Blue Apron", "Home Chef"],
            "response": "1. HelloFresh 2. Blue Apron 3. Home Chef",
            "intent_category": "Best-of"
        },
        {
            "query": "Affordable meal delivery",
            "model": "ChatGPT-4",
            "mentioned": True,
            "rank": 2,
            "competitors": ["EveryPlate", "Dinnerly"],
            "response": "1. EveryPlate 2. HelloFresh 3. Dinnerly",
            "intent_category": "Budget"
        },
        {
            "query": "Meal kit comparison",
            "model": "Claude-3.5-Sonnet",
            "mentioned": False,
            "rank": None,
            "competitors": ["Blue Apron", "Home Chef"],
            "response": "Blue Apron and Home Chef are popular options",
            "intent_category": "Comparison"
        }
    ]
    
    scores = scorer.calculate_visibility_score(sample_results)
    print(f"Overall Score: {scores['overall_score']}")
    print(f"Mention Rate: {scores['mention_rate']}")
    print(f"Rank Score: {scores['rank_score']}")
    
    interpretation = scorer.interpret_score(scores['overall_score'])
    print(f"\nInterpretation: {interpretation[0]}")
    print(f"Details: {interpretation[1]}")
