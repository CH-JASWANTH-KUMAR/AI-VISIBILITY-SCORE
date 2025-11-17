"""
Industry Detection Module
Scrapes website and classifies industry using GPT-4
"""

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os


class IndustryDetector:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.industry_keywords = {
            "Meal Kits & Food Delivery": ["meal", "recipe", "chef", "ingredients", "cooking", "food", "delivery"],
            "SaaS & Software": ["platform", "dashboard", "API", "integration", "workflow", "software", "cloud"],
            "Health & Wellness": ["fitness", "nutrition", "wellness", "health", "exercise", "yoga", "meditation"],
            "E-commerce & Retail": ["shop", "store", "retail", "products", "shopping", "ecommerce"],
            "Travel & Hospitality": ["travel", "hotel", "booking", "vacation", "tourism", "hospitality"],
            "Financial Services": ["finance", "banking", "investment", "insurance", "loan", "credit"],
            "Education & E-learning": ["education", "learning", "course", "training", "tutorial", "school"],
            "Marketing & Advertising": ["marketing", "advertising", "branding", "campaign", "social media"],
            "Real Estate": ["real estate", "property", "housing", "rental", "apartment", "home"]
        }
    
    def scrape_website(self, url):
        """Extract text from homepage"""
        try:
            # Add https:// if not present
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts, styles, nav, footer
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract text from key sections
            text = soup.get_text(separator=' ', strip=True)
            
            # Limit to first 3000 chars to save tokens
            return text[:3000]
        except Exception as e:
            print(f"Error scraping website: {e}")
            return ""
    
    def classify_industry_with_llm(self, brand_name, website_text):
        """Use GPT-4 to classify industry"""
        try:
            prompt = f"""
Analyze this brand and website content to classify the industry.

Brand: {brand_name}
Website content: {website_text}

Choose ONE industry from:
- Meal Kits & Food Delivery
- E-commerce & Retail
- SaaS & Software
- Health & Wellness
- Travel & Hospitality
- Financial Services
- Education & E-learning
- Marketing & Advertising
- Real Estate
- Other

Respond with ONLY the industry name, nothing else.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error with LLM classification: {e}")
            return "Other"
    
    def classify_industry_with_keywords(self, text):
        """Fallback: keyword-based classification"""
        text_lower = text.lower()
        scores = {}
        
        for industry, keywords in self.industry_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[industry] = score
        
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "Other"
    
    def detect_industry(self, brand_name, url):
        """Main method: detect industry from brand and URL"""
        # Scrape website
        website_text = self.scrape_website(url)
        
        if not website_text:
            return "Other"
        
        # Try LLM classification first
        try:
            industry = self.classify_industry_with_llm(brand_name, website_text)
            return industry
        except:
            # Fallback to keyword matching
            return self.classify_industry_with_keywords(website_text)


# Example usage
if __name__ == "__main__":
    detector = IndustryDetector()
    result = detector.detect_industry("HelloFresh", "hellofresh.com")
    print(f"Detected Industry: {result}")
