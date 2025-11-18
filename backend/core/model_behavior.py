"""
Feature #5: Model Behavior Insights
Analyze unique patterns and biases across different AI models
"""

from typing import List, Dict, Any
from collections import Counter, defaultdict


class ModelBehaviorAnalyzer:
    """Analyze model-specific behavior patterns"""
    
    def __init__(self, brand_name: str):
        self.brand_name = brand_name
        self.models = ['ChatGPT', 'Claude', 'Perplexity', 'Gemini']
    
    def analyze_model_patterns(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify unique behavioral patterns for each model
        """
        model_stats = self._calculate_model_stats(results)
        patterns = self._identify_patterns(model_stats, results)
        comparisons = self._compare_models(model_stats)
        insights = self._generate_insights(patterns, model_stats)
        
        return {
            'model_statistics': model_stats,
            'behavioral_patterns': patterns,
            'model_comparisons': comparisons,
            'key_insights': insights
        }
    
    def _calculate_model_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics per model"""
        stats = {}
        
        for model in self.models:
            model_results = [r for r in results if r.get('model') == model]
            
            if not model_results:
                continue
            
            mentions = [r for r in model_results if r.get('mentioned')]
            
            # Calculate metrics
            mention_rate = len(mentions) / len(model_results) * 100 if model_results else 0
            avg_rank = sum(r.get('rank', 0) for r in mentions) / len(mentions) if mentions else 0
            
            # Competitor patterns
            all_competitors = []
            for r in model_results:
                all_competitors.extend(r.get('competitors', []))
            competitor_dist = Counter(all_competitors)
            
            # Sentiment distribution (Feature #4 integration)
            sentiments = [r.get('sentiment', 'N/A') for r in mentions]
            sentiment_dist = Counter(sentiments)
            
            # Query category preferences
            categories = [r.get('intent_category', 'General') for r in model_results]
            category_dist = Counter(categories)
            
            stats[model] = {
                'total_queries': len(model_results),
                'mentions': len(mentions),
                'mention_rate': round(mention_rate, 1),
                'avg_rank': round(avg_rank, 1) if avg_rank > 0 else None,
                'unique_competitors': len(set(all_competitors)),
                'top_competitors': dict(competitor_dist.most_common(5)),
                'sentiment_distribution': dict(sentiment_dist),
                'category_preferences': dict(category_dist.most_common(5))
            }
        
        return stats
    
    def _identify_patterns(self, model_stats: Dict, results: List[Dict]) -> Dict[str, List[str]]:
        """Identify unique patterns per model"""
        patterns = {}
        
        for model, stats in model_stats.items():
            model_patterns = []
            
            # Mention bias
            mention_rate = stats['mention_rate']
            if mention_rate > 70:
                model_patterns.append(f"High brand affinity ({mention_rate}% mention rate)")
            elif mention_rate < 30:
                model_patterns.append(f"Low brand visibility ({mention_rate}% mention rate)")
            
            # Ranking behavior
            if stats['avg_rank'] and stats['avg_rank'] < 3:
                model_patterns.append("Tends to rank brand highly when mentioned")
            elif stats['avg_rank'] and stats['avg_rank'] > 5:
                model_patterns.append("Mentions brand but ranks it lower")
            
            # Competitor preference
            if stats['unique_competitors'] > 15:
                model_patterns.append("Mentions diverse competitor set")
            elif stats['unique_competitors'] < 8:
                model_patterns.append("Focuses on established/major competitors")
            
            # Category specialization
            top_category = max(stats['category_preferences'].items(), key=lambda x: x[1])[0] if stats['category_preferences'] else None
            if top_category:
                model_patterns.append(f"Specializes in '{top_category}' queries")
            
            # Sentiment pattern
            if 'sentiment_distribution' in stats:
                sentiments = stats['sentiment_distribution']
                if sentiments.get('Positive', 0) > sentiments.get('Negative', 0) + sentiments.get('Hesitant', 0):
                    model_patterns.append("Predominantly positive brand sentiment")
                elif sentiments.get('Negative', 0) > 0:
                    model_patterns.append("Contains negative/critical mentions")
            
            patterns[model] = model_patterns
        
        return patterns
    
    def _compare_models(self, model_stats: Dict) -> List[Dict[str, Any]]:
        """Generate model comparisons"""
        comparisons = []
        
        # Mention rate comparison
        mention_rates = {m: s['mention_rate'] for m, s in model_stats.items()}
        if mention_rates:
            best_model = max(mention_rates, key=mention_rates.get)
            worst_model = min(mention_rates, key=mention_rates.get)
            
            ratio = mention_rates[best_model] / mention_rates[worst_model] if mention_rates[worst_model] > 0 else 0
            
            comparisons.append({
                'metric': 'Brand Mention Bias',
                'finding': f"{best_model} is {ratio:.1f}x more likely to mention {self.brand_name} than {worst_model}",
                'best_model': best_model,
                'worst_model': worst_model,
                'impact': 'High' if ratio > 2 else 'Medium'
            })
        
        # Ranking comparison
        avg_ranks = {m: s['avg_rank'] for m, s in model_stats.items() if s['avg_rank']}
        if len(avg_ranks) >= 2:
            best_ranker = min(avg_ranks, key=avg_ranks.get)
            worst_ranker = max(avg_ranks, key=avg_ranks.get)
            
            comparisons.append({
                'metric': 'Ranking Behavior',
                'finding': f"{best_ranker} ranks {self.brand_name} at avg position {avg_ranks[best_ranker]:.1f} vs {worst_ranker} at {avg_ranks[worst_ranker]:.1f}",
                'best_model': best_ranker,
                'worst_model': worst_ranker,
                'impact': 'Medium'
            })
        
        # Competitor diversity
        competitor_counts = {m: s['unique_competitors'] for m, s in model_stats.items()}
        if competitor_counts:
            most_diverse = max(competitor_counts, key=competitor_counts.get)
            least_diverse = min(competitor_counts, key=competitor_counts.get)
            
            comparisons.append({
                'metric': 'Competitor Diversity',
                'finding': f"{most_diverse} mentions {competitor_counts[most_diverse]} unique competitors vs {least_diverse} with {competitor_counts[least_diverse]}",
                'best_model': most_diverse,
                'worst_model': least_diverse,
                'impact': 'Low'
            })
        
        return comparisons
    
    def _generate_insights(self, patterns: Dict, model_stats: Dict) -> List[str]:
        """Generate actionable insights"""
        insights = []
        
        # Identify best/worst models for brand
        mention_rates = {m: s['mention_rate'] for m, s in model_stats.items()}
        
        if mention_rates:
            best = max(mention_rates, key=mention_rates.get)
            worst = min(mention_rates, key=mention_rates.get)
            
            insights.append(f"🎯 **Optimize for {worst}**: {self.brand_name} has only {mention_rates[worst]}% visibility on {worst}. Focus SEO and content strategies that align with {worst}'s preferences.")
            
            insights.append(f"✅ **Leverage {best}**: Strong {mention_rates[best]}% visibility on {best}. Use {best}'s API for customer-facing tools to maximize brand exposure.")
        
        # Model-specific recommendations
        for model, model_patterns in patterns.items():
            if "Low brand visibility" in str(model_patterns):
                insights.append(f"⚠️ **{model} Challenge**: This model rarely mentions {self.brand_name}. Consider whether {model} favors established brands, specific content formats, or trust signals you may lack.")
        
        # Emerging brand bias detection
        total_queries = sum(s['total_queries'] for s in model_stats.values())
        avg_mention_rate = sum(s['mention_rate'] for s in model_stats.values()) / len(model_stats)
        
        if avg_mention_rate < 40:
            insights.append(f"📊 **General Pattern**: All models show low brand recognition ({avg_mention_rate:.1f}% avg). {self.brand_name} may benefit from AI-specific SEO optimization and brand authority building.")
        
        return insights


if __name__ == "__main__":
    analyzer = ModelBehaviorAnalyzer("TestBrand")
    
    test_results = [
        {'model': 'ChatGPT', 'mentioned': True, 'rank': 2, 'competitors': ['A', 'B'], 'intent_category': 'Price'},
        {'model': 'Claude', 'mentioned': False, 'competitors': ['A', 'C'], 'intent_category': 'Quality'},
        {'model': 'Perplexity', 'mentioned': True, 'rank': 4, 'competitors': ['B'], 'intent_category': 'Price'}
    ]
    
    analysis = analyzer.analyze_model_patterns(test_results)
    print("Model Behavior:", analysis)
