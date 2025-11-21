"""
Industry Detection Module
Scrapes website and classifies industry using GPT-4
"""

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import google.generativeai as genai
import httpx
import os
import asyncio


class IndustryDetector:
    def __init__(self):
        openai_key = os.getenv('OPENAI_API_KEY')
        self.openai_client = OpenAI(api_key=openai_key) if openai_key else None
        self.google_key = os.getenv('GOOGLE_API_KEY')
        
        self.industry_keywords = {
            "Meal Kits & Food Delivery": ["meal", "recipe", "chef", "ingredients", "cooking", "food", "delivery", "meal kit"],
            "SaaS & Software": ["platform", "dashboard", "API", "integration", "workflow", "software", "cloud", "saas"],
            "Health & Wellness": ["fitness", "nutrition", "wellness", "health", "exercise", "yoga", "meditation"],
            "E-commerce & Retail": ["shop", "store", "retail", "products", "shopping", "ecommerce", "online store"],
            "Travel & Hospitality": ["travel", "hotel", "booking", "vacation", "tourism", "hospitality"],
            "Financial Services": ["finance", "banking", "investment", "insurance", "loan", "credit", "fintech"],
            "Education & E-learning": ["education", "learning", "course", "training", "tutorial", "school", "edtech", "online learning"],
            "Startup Incubators & Accelerators": ["startup", "incubator", "accelerator", "entrepreneur", "founder", "innovator", "mentorship", "venture", "innovation"],
            "Marketing & Advertising": ["marketing", "advertising", "branding", "campaign", "social media"],
            "Real Estate": ["real estate", "property", "housing", "rental", "apartment", "home"],
            "Automotive & EV": ["electric vehicle", "ev", "automotive", "car", "vehicle", "automobile", "mobility"]
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
    
    async def classify_with_gemini(self, brand_name, website_text):
        """Use Google Gemini to classify industry"""
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
- Startup Incubators & Accelerators
- Marketing & Advertising
- Real Estate
- Automotive & EV
- Other

Respond with ONLY the industry name, nothing else.
"""
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={self.google_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.1,
                            "maxOutputTokens": 100
                        }
                    },
                    timeout=30.0
                )
                data = response.json()
                
                if "candidates" in data and len(data["candidates"]) > 0:
                    result = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return result
                return "Other"
        except Exception as e:
            print(f"Error with Gemini classification: {e}")
            return "Other"
    
    def classify_industry_with_llm(self, brand_name, website_text):
        """Use OpenAI GPT-4 to classify industry"""
        try:
            if not self.openai_client:
                return "Other"
                
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
- Startup Incubators & Accelerators
- Marketing & Advertising
- Real Estate
- Automotive & EV
- Other

Respond with ONLY the industry name, nothing else.
"""
            
            response = self.openai_client.chat.completions.create(
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
        
        # Try Google Gemini first (if available)
        if self.google_key:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                industry = loop.run_until_complete(self.classify_with_gemini(brand_name, website_text))
                loop.close()
                if industry and industry != "Other":
                    return industry
            except Exception as e:
                print(f"Gemini classification failed: {e}")
        
        # Try OpenAI if available
        if self.openai_client:
            try:
                industry = self.classify_industry_with_llm(brand_name, website_text)
                if industry and industry != "Other":
                    return industry
            except Exception as e:
                print(f"OpenAI classification failed: {e}")
        
        # Fallback to keyword matching
        return self.classify_industry_with_keywords(website_text)


# Example usage
if __name__ == "__main__":
    detector = IndustryDetector()
    result = detector.detect_industry("HelloFresh", "hellofresh.com")
    print(f"Detected Industry: {result}")
