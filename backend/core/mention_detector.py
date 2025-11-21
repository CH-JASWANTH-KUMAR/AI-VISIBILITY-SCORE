"""
Mention Detector Module
Detects brand mentions, rankings, and competitors in AI responses
"""

import re
from fuzzywuzzy import fuzz
from typing import Tuple, List, Optional

# Try to import spacy, but make it optional
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not available. NER features will be limited.")


class MentionDetector:
    def __init__(self, brand_name):
        self.brand_name = brand_name
        self.brand_variations = self.generate_variations(brand_name)
        
        # Load spaCy model for NER (download with: python -m spacy download en_core_web_sm)
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                print("Warning: spaCy model not loaded. Run: python -m spacy download en_core_web_sm")
                self.nlp = None
    
    def generate_variations(self, brand):
        """Generate common brand name variations"""
        variations = [brand.lower()]
        
        # Remove common suffixes
        for suffix in [' inc', ' llc', ' corp', ' co', '.com', ' inc.', ' llc.']:
            if brand.lower().endswith(suffix):
                clean_name = brand.lower().replace(suffix, '').strip()
                if clean_name not in variations:
                    variations.append(clean_name)
        
        # Add version without spaces
        no_space = brand.lower().replace(' ', '')
        if no_space not in variations:
            variations.append(no_space)
        
        return variations
    
    def detect_brand_mention(self, text):
        """Detect if brand is mentioned (exact + fuzzy)"""
        if not text:
            return False, 0.0, "none"
            
        text_lower = text.lower()
        print(f"\n🔍 Searching for '{self.brand_name}' in response...")
        print(f"   Variations: {self.brand_variations}")
        print(f"   Text preview: {text[:200]}...")
        
        # Exact match - check each variation
        for variant in self.brand_variations:
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(variant) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                print(f"   ✅ Found exact match: '{variant}'")
                return True, 1.0, "exact"
        
        # Fuzzy match (threshold 80% - lowered for better detection)
        words = text_lower.split()
        brand_word_count = len(self.brand_name.split())
        
        for word_group in self.get_ngrams(words, max(1, brand_word_count)):
            phrase = ' '.join(word_group)
            ratio = fuzz.ratio(self.brand_name.lower(), phrase)
            if ratio >= 80:
                print(f"   ✅ Found fuzzy match: '{phrase}' (score: {ratio}%)")
                return True, ratio/100, "fuzzy"
        
        print(f"   ❌ No match found for '{self.brand_name}'")
        return False, 0.0, "none"
    
    def get_ngrams(self, words, n):
        """Generate n-grams from word list"""
        if n <= 0 or n > len(words):
            return []
        return [words[i:i+n] for i in range(len(words)-n+1)]
    
    def extract_ranking(self, text, brand_name):
        """Extract ranking position if brand is in a list"""
        # Pattern 1: Numbered lists (1. Brand, 2. Brand)
        pattern1 = r'(\d+)[\.\)]\s*\*?\*?([^\n]+)'
        matches = re.findall(pattern1, text, re.IGNORECASE)
        
        for rank, line in matches:
            if brand_name.lower() in line.lower():
                return int(rank), line.strip()
        
        # Pattern 2: Bullet points with order inference
        lines = text.split('\n')
        rank = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('•', '-', '*', '●')):
                rank += 1
                if brand_name.lower() in stripped.lower():
                    return rank, stripped
        
        # Pattern 3: "Top X" mentions
        pattern3 = r'(top|best)\s+(\d+)'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match and brand_name.lower() in text.lower():
            return None, "mentioned_in_top_section"
        
        # Pattern 4: First, Second, Third mentions
        ordinal_map = {
            'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
            '1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5
        }
        for ordinal, num in ordinal_map.items():
            pattern = rf'\b{ordinal}\b[:\s]+([^\n]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match and brand_name.lower() in match.group(1).lower():
                return num, match.group(1).strip()
        
        return None, "mentioned_not_ranked"
    
    def extract_competitors(self, text, brand_name):
        """Extract competitor names using NER + brand-like patterns"""
        competitors = set()
        
        # Use spaCy NER if available
        if self.nlp:
            doc = self.nlp(text)
            
            # Extract ORG entities
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    name = ent.text.strip()
                    # Filter out generic terms and the target brand
                    if name.lower() not in ['the', 'a', 'an', 'inc', 'llc'] and \
                       name.lower() != brand_name.lower() and \
                       len(name) > 2:
                        competitors.add(name)
        
        # Pattern matching for brand-like mentions
        # Look for capitalized words/phrases in lists
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        matches = re.findall(pattern, text)
        
        for match in matches:
            # Filter criteria
            if match.lower() != brand_name.lower() and \
               len(match) > 3 and \
               match not in ['The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'What', 'Which']:
                competitors.add(match)
        
        # Look for numbered list competitors
        numbered_pattern = r'\d+[\.\)]\s*\*?\*?([A-Z][a-zA-Z\s]+?)(?:\s*[-–—:]|\n|$)'
        numbered_matches = re.findall(numbered_pattern, text)
        
        for match in numbered_matches:
            clean_name = match.strip()
            if clean_name.lower() != brand_name.lower() and len(clean_name) > 3:
                competitors.add(clean_name)
        
        return list(competitors)[:10]  # Limit to top 10
    
    def extract_competitor_rank(self, text, competitor_name):
        """Extract rank for a specific competitor"""
        pattern = r'(\d+)[\.\)]\s*([^\n]+)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for rank, line in matches:
            if competitor_name.lower() in line.lower():
                return int(rank)
        
        return None
    
    def calculate_confidence(self, mention_found, fuzzy_score, has_rank):
        """Calculate confidence score for detection"""
        confidence = 0.0
        
        if mention_found:
            confidence += 0.5
            confidence += fuzzy_score * 0.3
            if has_rank:
                confidence += 0.2
        
        return min(confidence, 1.0)
    
    def analyze_response(self, response_text):
        """Complete analysis of a response"""
        # Detect brand mention
        mentioned, fuzzy_score, match_type = self.detect_brand_mention(response_text)
        
        # Extract ranking if mentioned
        rank = None
        rank_context = ""
        if mentioned:
            rank, rank_context = self.extract_ranking(response_text, self.brand_name)
        
        # Extract competitors
        competitors = self.extract_competitors(response_text, self.brand_name)
        
        # Calculate confidence
        confidence = self.calculate_confidence(mentioned, fuzzy_score, rank is not None)
        
        # Analyze sentiment
        sentiment = self.analyze_sentiment(response_text, mentioned)
        sentiment_score = self._calculate_sentiment_score(sentiment)
        
        return {
            "mentioned": mentioned,
            "confidence": confidence,
            "match_type": match_type,
            "rank": rank,
            "rank_context": rank_context,
            "competitors": competitors,
            "competitor_count": len(competitors),
            "sentiment": sentiment,
            "sentiment_score": sentiment_score
        }
    
    def _calculate_sentiment_score(self, sentiment: str) -> float:
        """Convert sentiment to numeric score"""
        scores = {
            'Positive': 1.0,
            'Neutral': 0.5,
            'Hesitant': 0.3,
            'Negative': 0.0,
            'N/A': 0.5
        }
        return scores.get(sentiment, 0.5)


    def analyze_sentiment(self, text: str, mentioned: bool) -> str:
        """
        Feature #4: Analyze sentiment of brand mention
        Returns: 'Positive', 'Neutral', 'Negative', 'Hesitant'
        """
        if not mentioned:
            return 'N/A'
        
        # Extract context around brand mention
        text_lower = text.lower()
        
        # Find brand mention location
        brand_idx = -1
        for variant in self.brand_variations:
            idx = text_lower.find(variant)
            if idx != -1:
                brand_idx = idx
                break
        
        if brand_idx == -1:
            return 'Neutral'
        
        # Get surrounding context
        start = max(0, brand_idx - 200)
        end = min(len(text), brand_idx + len(self.brand_name) + 200)
        context = text[start:end].lower()
        
        # Sentiment keywords
        positive_kw = ['best', 'excellent', 'great', 'top', 'recommended', 'popular', 'leading', 'trusted', 'quality', 'favorite', 'amazing', 'outstanding', 'perfect', 'ideal']
        negative_kw = ['however', 'but', 'expensive', 'limited', 'lacks', 'poor', 'disappointing', 'avoid', 'issue', 'problem', 'worst', 'bad', 'overpriced']
        hesitant_kw = ['some', 'might', 'could', 'may', 'potentially', 'sometimes', 'depending', 'mixed reviews', 'varies', 'uncertain']
        
        pos_count = sum(1 for kw in positive_kw if kw in context)
        neg_count = sum(1 for kw in negative_kw if kw in context)
        hes_count = sum(1 for kw in hesitant_kw if kw in context)
        
        if neg_count > pos_count:
            return 'Negative'
        elif hes_count >= 2:
            return 'Hesitant'
        elif pos_count > 0:
            return 'Positive'
        else:
            return 'Neutral'

# Example usage
if __name__ == "__main__":
    detector = MentionDetector("HelloFresh")
    
    sample_text = """
    Here are the top 5 meal kit services for busy professionals:
    
    1. HelloFresh - Offers great variety with easy-to-follow recipes
    2. Blue Apron - Known for premium ingredients and chef-designed meals
    3. Home Chef - Provides flexible customization options
    4. Factor - Best for pre-made meals that require no cooking
    5. Green Chef - Focuses on organic and sustainable ingredients
    
    Each of these services delivers fresh ingredients to your door weekly.
    """
    
    result = detector.analyze_response(sample_text)
    
    print(f"Brand Mentioned: {result['mentioned']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Rank: {result['rank']}")
    print(f"Competitors Found: {result['competitors']}")
