"""
Mention Detector Module
Detects brand mentions, rankings, and competitors in AI responses
"""

import re
from fuzzywuzzy import fuzz
import spacy
from typing import Tuple, List, Optional


class MentionDetector:
    def __init__(self, brand_name):
        self.brand_name = brand_name
        self.brand_variations = self.generate_variations(brand_name)
        
        # Load spaCy model for NER (download with: python -m spacy download en_core_web_sm)
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
        text_lower = text.lower()
        
        # Exact match
        for variant in self.brand_variations:
            if variant in text_lower:
                return True, 1.0, "exact"
        
        # Fuzzy match (threshold 85%)
        words = text_lower.split()
        brand_word_count = len(self.brand_name.split())
        
        for word_group in self.get_ngrams(words, brand_word_count):
            phrase = ' '.join(word_group)
            ratio = fuzz.ratio(self.brand_name.lower(), phrase)
            if ratio >= 85:
                return True, ratio/100, "fuzzy"
        
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
        
        return {
            "mentioned": mentioned,
            "confidence": confidence,
            "match_type": match_type,
            "rank": rank,
            "rank_context": rank_context,
            "competitors": competitors,
            "competitor_count": len(competitors)
        }


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
