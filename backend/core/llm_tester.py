"""
LLM Tester Module
Tests queries across multiple AI models (ChatGPT, Claude, Perplexity, Gemini)
"""

import asyncio
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import httpx
import os
from datetime import datetime


class LLMTester:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.anthropic_client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.perplexity_key = os.getenv('PERPLEXITY_API_KEY')
        self.google_key = os.getenv('GOOGLE_API_KEY')
        
        # Rate limiting
        self.rate_limiters = {
            'chatgpt': RateLimiter(50),  # 50 requests per minute
            'claude': RateLimiter(50),
            'perplexity': RateLimiter(20),
            'gemini': RateLimiter(60)
        }
    
    async def query_chatgpt(self, query):
        """Query OpenAI ChatGPT-4"""
        await self.rate_limiters['chatgpt'].acquire()
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": query}],
                temperature=0.7,
                max_tokens=800
            )
            return {
                "model": "ChatGPT-4",
                "response": response.choices[0].message.content,
                "timestamp": datetime.now().isoformat(),
                "tokens": response.usage.total_tokens,
                "error": None
            }
        except Exception as e:
            return {
                "model": "ChatGPT-4",
                "response": "",
                "timestamp": datetime.now().isoformat(),
                "tokens": 0,
                "error": str(e)
            }
    
    async def query_claude(self, query):
        """Query Anthropic Claude"""
        await self.rate_limiters['claude'].acquire()
        
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{"role": "user", "content": query}]
            )
            return {
                "model": "Claude-3.5-Sonnet",
                "response": response.content[0].text,
                "timestamp": datetime.now().isoformat(),
                "tokens": response.usage.input_tokens + response.usage.output_tokens,
                "error": None
            }
        except Exception as e:
            return {
                "model": "Claude-3.5-Sonnet",
                "response": "",
                "timestamp": datetime.now().isoformat(),
                "tokens": 0,
                "error": str(e)
            }
    
    async def query_perplexity(self, query):
        """Query Perplexity AI"""
        await self.rate_limiters['perplexity'].acquire()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.perplexity_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-sonar-large-128k-online",
                        "messages": [{"role": "user", "content": query}],
                        "max_tokens": 800
                    },
                    timeout=30.0
                )
                data = response.json()
                
                return {
                    "model": "Perplexity-Sonar",
                    "response": data["choices"][0]["message"]["content"],
                    "timestamp": datetime.now().isoformat(),
                    "citations": data.get("citations", []),
                    "error": None
                }
        except Exception as e:
            return {
                "model": "Perplexity-Sonar",
                "response": "",
                "timestamp": datetime.now().isoformat(),
                "citations": [],
                "error": str(e)
            }
    
    async def query_gemini(self, query):
        """Query Google Gemini"""
        await self.rate_limiters['gemini'].acquire()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={self.google_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": query}]}],
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 800
                        }
                    },
                    timeout=30.0
                )
                data = response.json()
                
                if "candidates" in data and len(data["candidates"]) > 0:
                    response_text = data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    response_text = ""
                
                return {
                    "model": "Gemini-Pro",
                    "response": response_text,
                    "timestamp": datetime.now().isoformat(),
                    "error": None
                }
        except Exception as e:
            return {
                "model": "Gemini-Pro",
                "response": "",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def test_single_query(self, query):
        """Test a single query across all 4 models"""
        results = await asyncio.gather(
            self.query_chatgpt(query),
            self.query_claude(query),
            self.query_perplexity(query),
            self.query_gemini(query),
            return_exceptions=True
        )
        
        # Handle any exceptions that weren't caught
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "model": "Unknown",
                    "response": "",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def test_all_queries(self, queries, batch_size=10):
        """Test all queries across all models with batching"""
        all_results = []
        
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(queries)-1)//batch_size + 1}")
            
            batch_results = await asyncio.gather(
                *[self.test_single_query(query) for query in batch]
            )
            
            # Flatten results
            for query_results in batch_results:
                all_results.extend(query_results)
            
            # Small delay between batches to avoid overwhelming APIs
            await asyncio.sleep(1)
        
        return all_results


class RateLimiter:
    """Rate limiter to respect API limits"""
    def __init__(self, max_per_minute=50):
        self.max_per_minute = max_per_minute
        self.calls = []
    
    async def acquire(self):
        now = asyncio.get_event_loop().time()
        
        # Remove calls older than 60 seconds
        self.calls = [t for t in self.calls if now - t < 60]
        
        # If at limit, wait
        if len(self.calls) >= self.max_per_minute:
            sleep_time = 60 - (now - self.calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                self.calls = []
        
        self.calls.append(now)


# Example usage
async def main():
    tester = LLMTester()
    
    # Test single query
    query = "What are the best meal kit services for busy professionals?"
    results = await tester.test_single_query(query)
    
    for result in results:
        print(f"\n{result['model']}:")
        print(f"Response: {result['response'][:200]}...")
        print(f"Error: {result.get('error', 'None')}")


if __name__ == "__main__":
    asyncio.run(main())
