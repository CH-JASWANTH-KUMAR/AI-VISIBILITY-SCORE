"""
Features #6-10: Additional Analysis Modules
- Query Difficulty Score
- Context-Aware Recommendations
- Missed Opportunities Detector
- Competitor Dominance Clustering
- Visibility Timeline Simulator
"""

from typing import List, Dict, Any
from collections import Counter, defaultdict
import re


class QueryDifficultyAnalyzer:
    """Feature #6: Calculate competition difficulty per query"""
    
    def __init__(self, brand_name: str):
        self.brand_name = brand_name
    
    def analyze_difficulty(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assign difficulty score to each query"""
        scored_queries = []
        
        for result in results:
            difficulty = self._calculate_difficulty(result)
            scored_queries.append({
                'query': result.get('query', ''),
                'difficulty': difficulty['level'],
                'score': difficulty['score'],
                'reasoning': difficulty['reasoning'],
                'mentioned': result.get('mentioned', False),
                'competitor_count': len(result.get('competitors', []))
            })
        
        # Aggregate stats
        difficulty_distribution = Counter(q['difficulty'] for q in scored_queries)
        
        # Find opportunities (easy queries where brand isn't mentioned)
        easy_opportunities = [q for q in scored_queries if q['difficulty'] == 'Easy' and not q['mentioned']]
        
        return {
            'scored_queries': scored_queries,
            'difficulty_distribution': dict(difficulty_distribution),
            'easy_opportunities_count': len(easy_opportunities),
            'easy_opportunities': easy_opportunities[:10],  # Top 10
            'average_difficulty_score': round(sum(q['score'] for q in scored_queries) / len(scored_queries), 1) if scored_queries else 0
        }
    
    def _calculate_difficulty(self, result: Dict) -> Dict[str, Any]:
        """Calculate difficulty for single query"""
        score = 0
        factors = []
        
        # Factor 1: Competitor count (0-40 points)
        competitor_count = len(result.get('competitors', []))
        if competitor_count > 8:
            score += 40
            factors.append(f"{competitor_count} competitors")
        elif competitor_count > 4:
            score += 25
            factors.append(f"{competitor_count} competitors")
        else:
            score += 10
            factors.append(f"Only {competitor_count} competitors")
        
        # Factor 2: Brand mentioned (0-30 points)
        if not result.get('mentioned', False):
            score += 30
            factors.append("Brand absent")
        else:
            rank = result.get('rank', 999)
            if rank > 5:
                score += 20
                factors.append(f"Low rank (#{rank})")
            else:
                score += 5
                factors.append(f"Good rank (#{rank})")
        
        # Factor 3: Query specificity (0-30 points)
        query = result.get('query', '').lower()
        if any(kw in query for kw in ['best', 'top', 'vs', 'comparison', 'review']):
            score += 30
            factors.append("High-competition keywords")
        elif len(query.split()) > 8:
            score += 10
            factors.append("Niche/specific query")
        else:
            score += 20
            factors.append("General query")
        
        # Determine level
        if score >= 70:
            level = "Hard"
        elif score >= 40:
            level = "Medium"
        else:
            level = "Easy"
        
        return {
            'score': score,
            'level': level,
            'reasoning': ', '.join(factors)
        }


class RecommendationEngine:
    """Feature #7: Generate laser-targeted recommendations"""
    
    def __init__(self, brand_name: str, industry: str):
        self.brand_name = brand_name
        self.industry = industry
    
    def generate_recommendations(
        self,
        gap_analysis: Dict,
        competitor_insights: Dict,
        difficulty_analysis: Dict,
        results: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized, actionable recommendations"""
        recommendations = []
        
        # Rec 1: Target easy wins
        easy_opps = difficulty_analysis.get('easy_opportunities', [])
        if easy_opps:
            queries = ', '.join([q['query'][:40] for q in easy_opps[:3]])
            recommendations.append({
                'priority': 'High',
                'category': 'Quick Wins',
                'action': f'Create targeted content for {len(easy_opps)} low-competition queries',
                'details': f'Examples: {queries}...',
                'expected_impact': '+15-25% visibility in these segments',
                'effort': 'Low',
                'timeframe': '1-2 weeks'
            })
        
        # Rec 2: Address top theme gaps
        if gap_analysis and 'top_missing_themes' in gap_analysis:
            top_gap = gap_analysis['top_missing_themes'][0] if gap_analysis['top_missing_themes'] else None
            if top_gap:
                recommendations.append({
                    'priority': 'High',
                    'category': 'Content Gap',
                    'action': f"Create '{top_gap['theme']}' focused landing pages",
                    'details': f"Competitors emphasize {top_gap['theme']} in {top_gap['frequency']} queries where you're absent. Add 3-5 pages highlighting this aspect.",
                    'expected_impact': f"+{top_gap['frequency'] * 2}% visibility",
                    'effort': 'Medium',
                    'timeframe': '2-4 weeks'
                })
        
        # Rec 3: Learn from top competitor
        if competitor_insights and 'insights' in competitor_insights:
            top_comp = competitor_insights['insights'][0] if competitor_insights['insights'] else None
            if top_comp:
                recommendations.append({
                    'priority': 'Medium',
                    'category': 'Competitive Strategy',
                    'action': f"Adopt {top_comp['competitor_name']}'s positioning strategy",
                    'details': f"{top_comp['strategic_insight'][:150]}",
                    'expected_impact': '+10-15% visibility',
                    'effort': 'High',
                    'timeframe': '1-2 months'
                })
        
        # Rec 4: Model-specific optimization
        non_mention_rate = len([r for r in results if not r.get('mentioned')]) / len(results) * 100 if results else 0
        if non_mention_rate > 50:
            recommendations.append({
                'priority': 'High',
                'category': 'SEO Optimization',
                'action': 'Implement AI-specific SEO best practices',
                'details': 'Add structured data, FAQ schema, comparison tables, and customer testimonials. AI models heavily weight these signals.',
                'expected_impact': '+20-30% overall visibility',
                'effort': 'Medium',
                'timeframe': '3-4 weeks'
            })
        
        # Rec 5: Brand authority signals
        recommendations.append({
            'priority': 'Medium',
            'category': 'Trust Building',
            'action': 'Increase trust signals and third-party validation',
            'details': 'Get featured in industry publications, add customer reviews widget, showcase partnerships/certifications prominently.',
            'expected_impact': '+10-15% visibility, especially on Claude and Gemini',
            'effort': 'High',
            'timeframe': '1-3 months'
        })
        
        return recommendations


class OpportunityDetector:
    """Feature #8: Find missed opportunities"""
    
    def __init__(self, brand_name: str):
        self.brand_name = brand_name
    
    def detect_opportunities(self, results: List[Dict[str, Any]], brand_info: Dict = None) -> Dict[str, Any]:
        """Detect queries where brand SHOULD appear but doesn't"""
        opportunities = []
        
        for result in results:
            if result.get('mentioned'):
                continue  # Already mentioned
            
            # Check if brand is relevant
            relevance = self._check_relevance(result, brand_info)
            
            if relevance['should_appear']:
                opportunities.append({
                    'query': result.get('query', ''),
                    'reason': relevance['reason'],
                    'competitors_present': result.get('competitors', [])[:5],
                    'priority': relevance['priority'],
                    'model': result.get('model', '')
                })
        
        # Sort by priority
        opportunities.sort(key=lambda x: {'High': 3, 'Medium': 2, 'Low': 1}.get(x['priority'], 0), reverse=True)
        
        return {
            'total_opportunities': len(opportunities),
            'high_priority': len([o for o in opportunities if o['priority'] == 'High']),
            'opportunities': opportunities[:20],  # Top 20
            'summary': self._generate_summary(opportunities)
        }
    
    def _check_relevance(self, result: Dict, brand_info: Dict) -> Dict[str, Any]:
        """Check if brand should appear in this query"""
        query = result.get('query', '').lower()
        competitors = result.get('competitors', [])
        
        # Same-segment competitors present
        if len(competitors) >= 2:
            return {
                'should_appear': True,
                'reason': f"Multiple similar competitors ({', '.join(competitors[:2])}) appear, but {self.brand_name} doesn't",
                'priority': 'High'
            }
        
        # Industry keywords in query
        industry_keywords = ['meal kit', 'delivery', 'subscription', 'service', 'platform', 'app']
        if any(kw in query for kw in industry_keywords) and competitors:
            return {
                'should_appear': True,
                'reason': f"Industry-relevant query with competitors present",
                'priority': 'Medium'
            }
        
        # Specific features mentioned
        if any(kw in query for kw in ['affordable', 'organic', 'fast', 'easy', 'best']):
            return {
                'should_appear': True,
                'reason': f"Query emphasizes features brand likely offers",
                'priority': 'Medium'
            }
        
        return {
            'should_appear': False,
            'reason': '',
            'priority': 'Low'
        }
    
    def _generate_summary(self, opportunities: List[Dict]) -> str:
        """Generate executive summary"""
        if not opportunities:
            return "No significant missed opportunities detected."
        
        high_pri = len([o for o in opportunities if o['priority'] == 'High'])
        
        return f"Found {len(opportunities)} missed opportunities where {self.brand_name} should appear but doesn't. {high_pri} are high-priority (direct competitors present). Prioritize these for immediate content creation."


class CompetitorClustering:
    """Feature #9: Cluster competitor dominance by theme"""
    
    def __init__(self):
        self.clusters = {
            'Price-Sensitive': ['cheap', 'affordable', 'budget', 'cost', 'inexpensive', 'discount'],
            'Health-Conscious': ['healthy', 'nutrition', 'organic', 'diet', 'wellness', 'fitness'],
            'Fast-Delivery': ['fast', 'quick', 'express', 'same-day', 'speed', 'delivery'],
            'Family-Sized': ['family', 'large', 'kids', 'children', 'portions', 'bulk'],
            'Eco-Friendly': ['eco', 'sustainable', 'green', 'organic', 'environment', 'carbon']
        }
    
    def cluster_competitors(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Group competitor mentions by intent clusters"""
        cluster_data = defaultdict(lambda: defaultdict(int))
        
        for result in results:
            query = result.get('query', '').lower()
            competitors = result.get('competitors', [])
            
            # Identify cluster
            for cluster_name, keywords in self.clusters.items():
                if any(kw in query for kw in keywords):
                    for comp in competitors:
                        cluster_data[cluster_name][comp] += 1
        
        # Format results
        formatted_clusters = {}
        for cluster, competitors in cluster_data.items():
            sorted_comps = sorted(competitors.items(), key=lambda x: x[1], reverse=True)
            dominant_competitor = sorted_comps[0][0] if sorted_comps else 'None'
            
            formatted_clusters[cluster] = {
                'dominant_competitor': dominant_competitor,
                'mention_count': sorted_comps[0][1] if sorted_comps else 0,
                'top_competitors': dict(sorted_comps[:5]),
                'total_mentions': sum(competitors.values())
            }
        
        # Generate insights
        insights = self._generate_cluster_insights(formatted_clusters)
        
        return {
            'clusters': formatted_clusters,
            'insights': insights
        }
    
    def _generate_cluster_insights(self, clusters: Dict) -> List[str]:
        """Generate insights from cluster data"""
        insights = []
        
        for cluster, data in clusters.items():
            if data['mention_count'] > 0:
                insights.append(
                    f"**{cluster}**: {data['dominant_competitor']} dominates with {data['mention_count']} mentions. "
                    f"{'Your brand should target this cluster.' if data['mention_count'] > 5 else 'Moderate competition.'}"
                )
        
        return insights


class TimelineSimulator:
    """Feature #10: Simulate visibility improvement over time"""
    
    def __init__(self, brand_name: str, current_score: float):
        self.brand_name = brand_name
        self.current_score = current_score
    
    def simulate_timeline(self, planned_improvements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Project visibility improvement timeline"""
        timeline = [
            {'month': 0, 'score': self.current_score, 'changes': 'Baseline', 'cumulative_effort': 0}
        ]
        
        cumulative_score = self.current_score
        cumulative_effort = 0
        
        for i, improvement in enumerate(planned_improvements, 1):
            # Extract impact
            impact = improvement.get('expected_impact', '+10%')
            effort = improvement.get('effort', 'Medium')
            
            # Parse impact
            import re
            impact_nums = re.findall(r'(\d+)', impact)
            impact_value = float(impact_nums[0]) if impact_nums else 10
            
            # Apply diminishing returns
            effective_impact = impact_value * (0.9 ** (i - 1))
            cumulative_score = min(100, cumulative_score + effective_impact)
            
            # Calculate effort
            effort_points = {'Low': 1, 'Medium': 2, 'High': 3}.get(effort, 2)
            cumulative_effort += effort_points
            
            timeline.append({
                'month': i,
                'score': round(cumulative_score, 1),
                'changes': improvement.get('action', 'Improvement'),
                'cumulative_effort': cumulative_effort
            })
        
        return {
            'timeline': timeline,
            'final_projected_score': round(cumulative_score, 1),
            'total_improvement': round(cumulative_score - self.current_score, 1),
            'estimated_duration_months': len(planned_improvements),
            'effort_level': 'High' if cumulative_effort > 8 else 'Medium' if cumulative_effort > 4 else 'Low'
        }


# Unified interface
class AdvancedAnalytics:
    """Unified interface for all advanced features"""
    
    def __init__(self, brand_name: str, industry: str, current_score: float):
        self.brand_name = brand_name
        self.industry = industry
        self.current_score = current_score
        
        self.difficulty_analyzer = QueryDifficultyAnalyzer(brand_name)
        self.rec_engine = RecommendationEngine(brand_name, industry)
        self.opp_detector = OpportunityDetector(brand_name)
        self.clustering = CompetitorClustering()
        self.timeline_sim = TimelineSimulator(brand_name, current_score)
    
    def run_full_analysis(
        self,
        results: List[Dict[str, Any]],
        gap_analysis: Dict = None,
        competitor_insights: Dict = None
    ) -> Dict[str, Any]:
        """Run all advanced analytics"""
        
        # Feature #6: Query Difficulty
        difficulty = self.difficulty_analyzer.analyze_difficulty(results)
        
        # Feature #7: Recommendations
        recommendations = self.rec_engine.generate_recommendations(
            gap_analysis or {},
            competitor_insights or {},
            difficulty,
            results
        )
        
        # Feature #8: Missed Opportunities
        opportunities = self.opp_detector.detect_opportunities(results)
        
        # Feature #9: Competitor Clustering
        clusters = self.clustering.cluster_competitors(results)
        
        # Feature #10: Timeline
        timeline = self.timeline_sim.simulate_timeline(recommendations[:5])
        
        return {
            'query_difficulty': difficulty,
            'recommendations': recommendations,
            'missed_opportunities': opportunities,
            'competitor_clusters': clusters,
            'improvement_timeline': timeline
        }


if __name__ == "__main__":
    analytics = AdvancedAnalytics("TestBrand", "Meal Kit", 45.0)
    test_results = []
    analysis = analytics.run_full_analysis(test_results)
    print("Advanced Analytics:", analysis)
