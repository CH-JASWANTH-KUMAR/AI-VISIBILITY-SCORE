"""
Demo Data Caching Script (DEPRECATED - Use regular analysis instead)

This script used the old LLMTester class which has been replaced by the service-oriented architecture.
To create demo data, simply run a regular analysis through the API.

RECOMMENDED APPROACH:
1. Start backend: python -m uvicorn backend.api.main:app --reload
2. Use frontend or curl to submit analysis:
   curl -X POST http://localhost:8000/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{"brand_name": "HelloFresh", "website_url": "https://hellofresh.com", "query_count": 20}'
3. Results will be cached automatically

This script is kept for reference only.
"""

import sys

def main():
    print("\n" + "="*70)
    print("⚠️  DEPRECATED SCRIPT")
    print("="*70)
    print("\nThis script uses the old LLMTester architecture.")
    print("Please use the regular analysis API instead:\n")
    print("1. Start backend:")
    print("   python -m uvicorn backend.api.main:app --reload --port 8000\n")
    print("2. Submit analysis via API:")
    print("   curl -X POST http://localhost:8000/api/v1/analyze \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"brand_name\": \"HelloFresh\", \"website_url\": \"https://hellofresh.com\", \"query_count\": 20}'\n")
    print("3. Check progress:")
    print("   curl http://localhost:8000/api/v1/status/{job_id}\n")
    print("="*70 + "\n")
    sys.exit(1)


if __name__ == "__main__":
    main()

