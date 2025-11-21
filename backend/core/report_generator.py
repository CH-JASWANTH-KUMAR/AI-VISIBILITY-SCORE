"""
Report Generator Module
Generates Excel/CSV reports with comprehensive analysis
"""

import pandas as pd
from datetime import datetime
import os


class ReportGenerator:
    def __init__(self, brand_name, industry):
        self.brand_name = brand_name
        self.industry = industry
        self.timestamp = datetime.now().isoformat()
    
    def generate_report(self, results, visibility_scores):
        """
        Generate comprehensive report with all data
        """
        rows = []
        
        for result in results:
            row = {
                # Query Info
                "query_text": result.get('query', ''),
                "intent_category": result.get('intent_category', 'General'),
                
                # Model Info
                "model": result.get('model', 'Unknown'),
                "timestamp": result.get('timestamp', ''),
                
                # Brand Detection
                "brand_mentioned": "Yes" if result.get('mentioned', False) else "No",
                "mention_confidence": round(result.get('confidence', 0), 3),
                "match_type": result.get('match_type', 'N/A'),
                
                # Ranking
                "brand_rank": result.get('rank') if result.get('rank') else "Not Ranked",
                "ranking_context": result.get('rank_context', ''),
                
                # Competitors
                "competitors_found": result.get('competitor_count', 0),
                "competitor_list": ", ".join(result.get('competitors', [])),
                "top_competitor": result.get('competitors', ['None'])[0] if result.get('competitors') else 'None',
                
                # Raw Data
                "full_response": result.get('response', '')[:1000] + "..." if len(result.get('response', '')) > 1000 else result.get('response', ''),
                "response_length": len(result.get('response', '')),
                "tokens_used": result.get('tokens', 'N/A'),
                
                # Metadata
                "error": result.get('error', ''),
                "citations": str(result.get('citations', ''))
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Create summary sheet
        summary_df = self.create_summary_sheet(results, visibility_scores)
        
        # Create category breakdown
        category_df = self.create_category_breakdown(df)
        
        # Create model comparison
        model_df = self.create_model_comparison(df)
        
        return df, summary_df, category_df, model_df
    
    def create_summary_sheet(self, results, visibility_scores):
        """Create summary statistics sheet"""
        # Calculate additional metrics
        total_queries = len(results)
        mentions = sum(1 for r in results if r.get('mentioned', False))
        avg_rank = self.calculate_avg_rank(results)
        
        # Get unique competitors
        all_competitors = set()
        for r in results:
            all_competitors.update(r.get('competitors', []))
        
        # Model with most mentions
        most_consistent = self.get_most_consistent_model(results)
        least_consistent = self.get_least_consistent_model(results)
        
        summary = {
            "Metric": [
                "Brand Name",
                "Industry",
                "Report Generated",
                "Total Queries Tested",
                "Total Models Tested",
                "",
                "Overall Visibility Score",
                "Interpretation",
                "",
                "Mention Rate (%)",
                "Total Mentions",
                "Average Rank (when mentioned)",
                "",
                "Competitor Analysis",
                "Total Unique Competitors Found",
                "Most Consistent Model",
                "Least Consistent Model",
            ],
            "Value": [
                self.brand_name,
                self.industry,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_queries,
                len(set(r.get('model', 'Unknown') for r in results)),
                "",
                visibility_scores['overall_score'],
                self.interpret_score(visibility_scores['overall_score']),
                "",
                round(mentions / total_queries * 100, 1) if total_queries > 0 else 0,
                mentions,
                avg_rank,
                "",
                "",
                len(all_competitors),
                most_consistent,
                least_consistent,
            ]
        }
        
        return pd.DataFrame(summary)
    
    def create_category_breakdown(self, df):
        """Create category-level analysis"""
        if 'intent_category' not in df.columns:
            return pd.DataFrame()
        
        category_stats = df.groupby('intent_category').agg({
            'query_text': 'count',
            'brand_mentioned': lambda x: (x == 'Yes').sum(),
            'brand_rank': lambda x: pd.to_numeric(x, errors='coerce').mean(),
            'competitors_found': 'mean'
        }).reset_index()
        
        category_stats.columns = [
            'Category',
            'Total Queries',
            'Brand Mentions',
            'Avg Rank',
            'Avg Competitors Found'
        ]
        
        category_stats['Mention Rate (%)'] = (
            (category_stats['Brand Mentions'].astype(float) / category_stats['Total Queries'].astype(float)) * 100
        ).round(1)
        
        return category_stats
    
    def create_model_comparison(self, df):
        """Create model-level comparison"""
        if 'model' not in df.columns:
            return pd.DataFrame()
        
        model_stats = df.groupby('model').agg({
            'query_text': 'count',
            'brand_mentioned': lambda x: (x == 'Yes').sum(),
            'brand_rank': lambda x: pd.to_numeric(x, errors='coerce').mean(),
            'response_length': 'mean',
            'error': lambda x: (x != '').sum()
        }).reset_index()
        
        model_stats.columns = [
            'Model',
            'Total Queries',
            'Brand Mentions',
            'Avg Rank',
            'Avg Response Length',
            'Errors'
        ]
        
        model_stats['Mention Rate (%)'] = round(
            (model_stats['Brand Mentions'] / model_stats['Total Queries']) * 100, 1
        )
        
        return model_stats
    
    def save_excel(self, df, summary_df, category_df, model_df, output_dir='reports'):
        """Save comprehensive Excel report"""
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"AI_Visibility_Report_{self.brand_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Write all sheets
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            df.to_excel(writer, sheet_name='Detailed Results', index=False)
            
            if not category_df.empty:
                category_df.to_excel(writer, sheet_name='Category Breakdown', index=False)
            
            if not model_df.empty:
                model_df.to_excel(writer, sheet_name='Model Comparison', index=False)
            
            # Add competitor sheet
            competitor_df = self.create_competitor_analysis(df)
            if not competitor_df.empty:
                competitor_df.to_excel(writer, sheet_name='Top Competitors', index=False)
        
        return filepath
    
    def save_csv(self, df, output_dir='reports'):
        """Save simple CSV report"""
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"AI_Visibility_Report_{self.brand_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(output_dir, filename)
        
        df.to_csv(filepath, index=False)
        return filepath
    
    def create_competitor_analysis(self, df):
        """Create competitor frequency analysis"""
        competitors = []
        
        for _, row in df.iterrows():
            comp_list = row.get('competitor_list', '')
            if comp_list and comp_list != 'None':
                for comp in comp_list.split(', '):
                    competitors.append({
                        'Competitor': comp.strip(),
                        'Query': row.get('query_text', ''),
                        'Model': row.get('model', '')
                    })
        
        if not competitors:
            return pd.DataFrame()
        
        comp_df = pd.DataFrame(competitors)
        comp_summary = comp_df.groupby('Competitor').agg({
            'Query': 'count',
            'Model': lambda x: ', '.join(sorted(set(x)))
        }).reset_index()
        
        comp_summary.columns = ['Competitor', 'Mention Count', 'Models']
        comp_summary = comp_summary.sort_values('Mention Count', ascending=False)
        
        return comp_summary
    
    def calculate_avg_rank(self, results):
        """Calculate average rank"""
        ranks = [r['rank'] for r in results if r.get('rank') is not None]
        return round(sum(ranks) / len(ranks), 2) if ranks else "N/A"
    
    def get_most_consistent_model(self, results):
        """Get model with highest mention rate"""
        from collections import defaultdict
        
        model_mentions = defaultdict(lambda: {'mentioned': 0, 'total': 0})
        
        for result in results:
            model = result.get('model', 'Unknown')
            model_mentions[model]['total'] += 1
            if result.get('mentioned', False):
                model_mentions[model]['mentioned'] += 1
        
        if not model_mentions:
            return "N/A"
        
        mention_rates = {
            model: data['mentioned'] / data['total'] if data['total'] > 0 else 0
            for model, data in model_mentions.items()
        }
        
        return max(mention_rates, key=mention_rates.get)
    
    def get_least_consistent_model(self, results):
        """Get model with lowest mention rate"""
        from collections import defaultdict
        
        model_mentions = defaultdict(lambda: {'mentioned': 0, 'total': 0})
        
        for result in results:
            model = result.get('model', 'Unknown')
            model_mentions[model]['total'] += 1
            if result.get('mentioned', False):
                model_mentions[model]['mentioned'] += 1
        
        if not model_mentions:
            return "N/A"
        
        mention_rates = {
            model: data['mentioned'] / data['total'] if data['total'] > 0 else 0
            for model, data in model_mentions.items()
        }
        
        return min(mention_rates, key=mention_rates.get)
    
    def interpret_score(self, score):
        """Get score interpretation"""
        if score >= 90:
            return "Dominant Presence"
        elif score >= 70:
            return "Strong Visibility"
        elif score >= 50:
            return "Moderate Visibility"
        elif score >= 30:
            return "Low Visibility"
        else:
            return "Minimal Visibility"


# Example usage
if __name__ == "__main__":
    generator = ReportGenerator("HelloFresh", "Meal Kits & Food Delivery")
    
    # Sample data
    sample_results = [
        {
            "query": "Best meal kits",
            "model": "ChatGPT-4",
            "mentioned": True,
            "confidence": 1.0,
            "match_type": "exact",
            "rank": 1,
            "rank_context": "1. HelloFresh",
            "competitors": ["Blue Apron", "Home Chef"],
            "competitor_count": 2,
            "response": "HelloFresh is a top choice...",
            "timestamp": datetime.now().isoformat(),
            "tokens": 150,
            "error": "",
            "intent_category": "Best-of"
        }
    ]
    
    visibility_scores = {
        "overall_score": 78.5,
        "mention_rate": 32.0,
        "rank_score": 28.0,
        "competitor_dominance": 12.0,
        "model_consistency": 6.5,
        "mentions": 40,
        "total_queries": 50
    }
    
    df, summary_df, category_df, model_df = generator.generate_report(sample_results, visibility_scores)
    
    print("Summary:")
    print(summary_df)
    
    # Save reports
    # excel_path = generator.save_excel(df, summary_df, category_df, model_df)
    # print(f"\nExcel saved to: {excel_path}")
