"""
Query Generator Module
Generates 50-100 diverse industry-specific queries using templates and GPT-4
"""

from openai import OpenAI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os
import json
from ..utils.cache import query_cache


class QueryGenerator:
    def __init__(self):
        openai_key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=openai_key) if openai_key else None
        
        # Query templates by industry
        self.templates = {
            "Meal Kits & Food Delivery": [
                "What are the best meal kit services for {audience}?",
                "Compare meal kit delivery options for {need}",
                "Most affordable meal kit subscriptions",
                "Healthiest meal delivery services",
                "Which meal kit is best for {diet_type}?",
                "Top-rated meal kit services with {feature}",
                "How to choose a meal kit for {scenario}",
                "Meal kit services that deliver to {location}",
                "Best organic meal delivery options",
                "Quick and easy meal kits for {lifestyle}"
            ],
            "Startup Incubators & Accelerators": [
                "Best startup incubators for {stage}",
                "Compare accelerator programs for {industry}",
                "Top-rated startup accelerators in {location}",
                "How to get into a startup incubator",
                "Best programs for {founder_type}",
                "Startup incubators with mentorship",
                "Which accelerator is best for {startup_type}?",
                "Student startup incubators and programs",
                "Early-stage startup accelerators",
                "Digital incubators for entrepreneurs",
                "Best resources for startup founders",
                "How to find investors for startups",
                "Startup mentorship programs",
                "Innovation hubs for entrepreneurs"
            ],
            "SaaS & Software": [
                "Best {software_type} for {use_case}",
                "Compare {software_type} platforms",
                "Most affordable {software_type} tools",
                "Top-rated {software_type} software for {industry}",
                "Which {software_type} has the best {feature}?",
                "How to choose the right {software_type}",
                "{software_type} for {company_size}",
                "Cloud-based {software_type} solutions",
                "Best {software_type} with integrations",
                "Enterprise {software_type} recommendations"
            ],
            "Health & Wellness": [
                "Best {product} for {goal}",
                "Compare {product} options",
                "Most affordable {product} programs",
                "Top-rated {product} apps",
                "Which {product} is best for {audience}?",
                "How to choose {product} for {need}",
                "{product} for {lifestyle}",
                "Online {product} platforms",
                "Best {product} subscriptions",
                "{product} reviews and recommendations"
            ],
            "E-commerce & Retail": [
                "Best online stores for {product_category}",
                "Where to buy {product_category} online",
                "Most affordable {product_category} retailers",
                "Top-rated {product_category} shops",
                "Compare {product_category} online stores",
                "Best {product_category} deals and discounts",
                "Online shopping for {product_category}",
                "Trusted {product_category} retailers",
                "Best {product_category} subscription boxes",
                "Where to find quality {product_category}"
            ],
            "Education & E-learning": [
                "Best online courses for {subject}",
                "Compare e-learning platforms for {audience}",
                "Most affordable online education programs",
                "Top-rated learning platforms",
                "Best courses for {skill}",
                "Online education for {level}"
            ]
        }
        
        # Variation placeholders
        self.variations = {
            # Meal Kits
            "audience": ["busy professionals", "families", "couples", "beginners", "seniors", "singles"],
            "need": ["weight loss", "muscle building", "convenience", "variety", "quality", "nutrition"],
            "diet_type": ["keto", "vegan", "paleo", "gluten-free", "low-carb", "vegetarian"],
            "feature": ["organic ingredients", "quick prep", "dietary customization", "chef recipes", "family-friendly"],
            "scenario": ["small kitchens", "first time", "picky eaters", "tight budgets", "busy schedules"],
            "location": ["rural areas", "cities", "suburbs", "apartments", "India", "Bangalore", "Mumbai"],
            "lifestyle": ["busy parents", "college students", "remote workers", "fitness enthusiasts", "health-conscious"],
            
            # Startup Incubators
            "stage": ["early-stage startups", "student founders", "first-time entrepreneurs", "tech startups"],
            "industry": ["tech", "edtech", "fintech", "healthtech", "AI/ML", "blockchain"],
            "founder_type": ["student entrepreneurs", "first-time founders", "technical founders", "non-technical founders"],
            "startup_type": ["software startups", "hardware startups", "service businesses", "product companies"],
            
            # SaaS
            "software_type": ["CRM", "project management", "marketing automation", "analytics", "collaboration"],
            "use_case": ["small businesses", "enterprises", "startups", "remote teams", "agencies"],
            "company_size": ["startups", "small businesses", "mid-size companies", "enterprises"],
            
            # Health & Wellness
            "product": ["fitness apps", "meal planning", "workout programs", "meditation apps", "wellness coaching"],
            "goal": ["weight loss", "muscle gain", "stress relief", "better sleep", "flexibility"],
            
            # E-commerce
            "product_category": ["electronics", "clothing", "home goods", "beauty products", "sporting goods"],
            
            # Education
            "subject": ["programming", "business", "design", "marketing", "data science"],
            "skill": ["coding", "entrepreneurship", "digital marketing", "data analysis"],
            "level": ["beginners", "professionals", "students", "career changers"]
        }
    
    def expand_template(self, template):
        """Fill template placeholders with variations"""
        expanded = []
        
        if "{" not in template:
            return [template]
        
        # Generate 5 variations per template
        for _ in range(5):
            filled = template
            for key, values in self.variations.items():
                placeholder = f"{{{key}}}"
                if placeholder in filled:
                    filled = filled.replace(placeholder, np.random.choice(values))
            expanded.append(filled)
        
        return expanded
    
    def generate_with_templates(self, industry):
        """Generate queries from templates"""
        templates = self.templates.get(industry, self.templates.get("E-commerce & Retail", []))
        
        queries = []
        for template in templates:
            queries.extend(self.expand_template(template))
        
        return queries
    
    def generate_with_llm(self, industry, brand_name, count=30):
        """Use GPT-4 to generate additional diverse queries"""
        if not self.client:
            print("OpenAI not available, skipping LLM query generation")
            return []
        
        try:
            prompt = f"""
Generate {count} diverse search queries that consumers would ask when looking for products/services in the {industry} industry.

Focus on:
- Product comparisons ("X vs Y")
- Best-of lists ("best X for Y")
- Reviews and recommendations
- Buying guides ("how to choose")
- Budget-focused queries ("most affordable")
- Specific use cases

Make queries natural and varied. Consider the brand: {brand_name}

Return as a numbered list, one query per line.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=1000
            )
            
            text = response.choices[0].message.content.strip()
            queries = []
            
            for line in text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Remove numbering
                    query = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                    if query:
                        queries.append(query)
            
            return queries
        except Exception as e:
            print(f"Error generating LLM queries: {e}")
            return []
    
    def get_embeddings(self, texts):
        """Get embeddings for deduplication"""
        if not self.client:
            return []
        
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error getting embeddings: {e}")
            return []
    
    def deduplicate_queries(self, queries, threshold=0.85):
        """Remove semantically similar queries using embeddings"""
        if len(queries) <= 1:
            return queries
        
        try:
            # Get embeddings in batches
            batch_size = 50
            all_embeddings = []
            
            for i in range(0, len(queries), batch_size):
                batch = queries[i:i+batch_size]
                embeddings = self.get_embeddings(batch)
                all_embeddings.extend(embeddings)
            
            if not all_embeddings:
                return queries
            
            # Keep queries with cosine similarity < threshold
            unique_queries = [queries[0]]
            unique_embeddings = [all_embeddings[0]]
            
            for i in range(1, len(queries)):
                if i >= len(all_embeddings):
                    break
                
                similarities = cosine_similarity(
                    [all_embeddings[i]], 
                    unique_embeddings
                )[0]
                
                if max(similarities) < threshold:
                    unique_queries.append(queries[i])
                    unique_embeddings.append(all_embeddings[i])
            
            return unique_queries
        except Exception as e:
            print(f"Error in deduplication: {e}")
            return queries
    
    def generate_queries(self, industry, brand_name, target_count=60):
        """Main method: generate diverse queries for the industry"""
        # Check cache first
        cached = query_cache.get(industry, brand_name, target_count)
        if cached:
            print(f"✅ Using cached queries for {industry}")
            return cached
        
        print(f"Generating queries for {industry}...")
        
        # Step 1: Generate from templates (fast)
        template_queries = self.generate_with_templates(industry)
        print(f"Generated {len(template_queries)} queries from templates")
        
        # Step 2: Only use LLM if we need more queries
        if len(template_queries) < target_count:
            llm_count = max(0, target_count - len(template_queries) + 10)
            llm_queries = self.generate_with_llm(industry, brand_name, llm_count)
            print(f"Generated {len(llm_queries)} queries with LLM")
        else:
            llm_queries = []
        
        # Step 3: Combine and deduplicate
        all_queries = template_queries + llm_queries
        unique_queries = self.deduplicate_queries(all_queries)
        print(f"After deduplication: {len(unique_queries)} unique queries")
        
        # Step 4: Return target count
        result = unique_queries[:target_count]
        
        # Cache for future use
        query_cache.set(industry, brand_name, target_count, result)
        
        return result


# Example usage
if __name__ == "__main__":
    generator = QueryGenerator()
    queries = generator.generate_queries("Meal Kits & Food Delivery", "HelloFresh", 60)
    
    print(f"\nGenerated {len(queries)} queries:")
    for i, query in enumerate(queries[:10], 1):
        print(f"{i}. {query}")
