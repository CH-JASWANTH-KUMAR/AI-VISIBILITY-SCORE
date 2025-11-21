# Development Guide - AI Visibility Score Tracker

> Complete guide for setup, development, and troubleshooting

## Table of Contents
- [Installation](#installation)
- [Development Workflow](#development-workflow)
- [Architecture](#architecture)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ or SQLite
- API Keys: OpenAI, Anthropic (optional), Perplexity (optional), Google AI (optional)

### Quick Setup (Docker - Recommended)

```powershell
# 1. Create environment file
Copy-Item config\.env.example -Destination .env
notepad .env  # Add your API keys

# 2. Start all services
docker-compose up -d

# 3. Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend

```powershell
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Configure environment
Copy-Item ..\config\.env.example -Destination .env
notepad .env  # Add your API keys

# Start backend
python -m uvicorn api.main:app --reload --port 8000
```

#### Frontend

```powershell
cd frontend

# Install dependencies
npm install

# Configure API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Start development server
npm run dev
```

### Getting API Keys

**OpenAI (Required):**
1. https://platform.openai.com/api-keys
2. Create new secret key (starts with `sk-`)

**Anthropic Claude (Optional):**
1. https://console.anthropic.com/
2. Create API key (starts with `sk-ant-`)

**Perplexity (Optional):**
1. https://www.perplexity.ai/settings/api
2. Generate API key (starts with `pplx-`)

**Google AI Gemini (Optional):**
1. https://makersuite.google.com/app/apikey
2. Create API key (starts with `AIza`)

---

## Development Workflow

### Backend Development

```powershell
cd backend
.\venv\Scripts\activate

# Run with auto-reload
python -m uvicorn api.main:app --reload --port 8000

# Test individual modules
python core/query_generator.py
python core/mention_detector.py

# Check logs
Get-Content logs/ai_visibility_*.log -Tail 50 -Wait
```

### Frontend Development

```powershell
cd frontend

# Development mode (hot reload)
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build
npm start
```

### Database Management

```powershell
# Reset database (SQLite)
Remove-Item ai_visibility.db -Force
# Database will auto-recreate on next backend start

# Reset database (Docker PostgreSQL)
docker-compose down -v
docker-compose up -d postgres
```

### Code Style

**Python (Backend):**
- PEP 8 style guide
- Type hints for functions
- Docstrings for classes/complex functions
- Use async/await for I/O operations

**TypeScript (Frontend):**
- ESLint + Prettier
- Functional components with hooks
- TypeScript strict mode
- Client/server component separation

---

## Architecture

### Service Layer (New Architecture)

The system uses a service-oriented architecture for AI model interactions:

```
backend/
├── services/
│   ├── openai_service.py      # OpenAI GPT-4 integration
│   ├── gemini_service.py       # Google Gemini integration
│   ├── claude_service.py       # Anthropic Claude integration
│   ├── perplexity_service.py   # Perplexity integration
│   └── service_manager.py      # Coordinates all services
```

**Key Features:**
- **Parallel Execution:** Tests 5 queries simultaneously with `asyncio.gather()`
- **Aggressive Timeouts:** 12-20 seconds per request (no infinite hangs)
- **Bulk Operations:** Saves 5 results at once to database
- **Query Caching:** 24-hour TTL using MD5 hash keys
- **Graceful Fallback:** Continues if one model fails

### Core Modules

```
backend/core/
├── industry_detector.py       # Website scraping + GPT-4 classification
├── query_generator.py         # Template-based + LLM query generation
├── mention_detector.py        # NER + fuzzy matching for brand detection
├── visibility_scorer.py       # Score calculation algorithm
└── report_generator.py        # Excel/CSV export with pandas
```

### Worker System

```python
# workers/tasks.py - Background job processing
async def process_analysis_job(job_id: str):
    # 1. Detect industry
    industry = await detect_industry(website_url)
    
    # 2. Generate queries (with cache)
    queries = await generate_queries(industry, brand_name, count=40)
    
    # 3. Test queries in parallel batches
    for batch in chunks(queries, batch_size=5):
        results = await asyncio.gather(*[
            service_manager.query_all(query) for query in batch
        ])
        db.bulk_save_objects(results)  # Bulk insert
    
    # 4. Calculate score
    score = calculate_visibility_score(results)
```

### Database Schema

```sql
-- SQLite schema
CREATE TABLE analysis_jobs (
    id TEXT PRIMARY KEY,
    brand_name TEXT NOT NULL,
    website_url TEXT,
    industry TEXT,
    status TEXT,  -- pending, processing, completed, failed
    progress INTEGER DEFAULT 0,
    overall_score REAL,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE results (
    id INTEGER PRIMARY KEY,
    job_id TEXT,
    query TEXT,
    model TEXT,
    response TEXT,
    mentioned BOOLEAN,
    rank_position INTEGER,
    sentiment TEXT,        -- NEW: Positive, Neutral, Negative
    sentiment_score REAL,  -- NEW: 0.0 to 1.0
    tokens_used TEXT,      -- JSON string: {"prompt": 15, "completion": 687}
    response_time REAL,
    FOREIGN KEY (job_id) REFERENCES analysis_jobs(id)
);
```

### Performance Optimizations

**1. Parallel Execution:**
```python
# Process 5 queries simultaneously
batch_tasks = [service_manager.query_all(q) for q in batch]
results = await asyncio.gather(*batch_tasks)
```

**2. Aggressive Timeouts:**
```python
# Fail fast after 20 seconds
results = await asyncio.wait_for(
    asyncio.gather(*batch_tasks),
    timeout=20.0
)
```

**3. Query Caching:**
```python
# Cache queries for 24 hours
cache_key = hashlib.md5(f"{industry}:{brand}:{count}".encode()).hexdigest()
cached = query_cache.get(cache_key)
if cached:
    return cached
```

**4. Bulk Database Operations:**
```python
# Save 5 results at once instead of one-by-one
db.bulk_save_objects(results_batch)
db.commit()
```

### Frontend Architecture

```
frontend/
├── app/
│   ├── page.tsx                    # Home: Input form
│   ├── dashboard/[id]/page.tsx     # Results dashboard
│   └── layout.tsx                  # Root layout
├── components/
│   ├── ScoreCard.tsx               # Overall score display
│   ├── QueryTable.tsx              # Full query transparency
│   ├── ModelComparison.tsx         # Bar chart comparison
│   └── CategoryChart.tsx           # Category breakdown
└── lib/
    └── api.ts                      # API client functions
```

---

## Testing

### Unit Tests (Individual Modules)

```powershell
# Test query generation
cd backend
python core/query_generator.py
# Should output 40-60 queries for "meal delivery" industry

# Test mention detection
python core/mention_detector.py
# Should detect brand mentions in sample text

# Test industry detection
python core/industry_detector.py
# Should classify website industry
```

### Integration Tests

```powershell
# Test full analysis flow
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"brand_name": "Test Brand", "website_url": "https://example.com", "query_count": 10}'

# Get job status
curl http://localhost:8000/api/v1/status/{job_id}

# Download report
curl http://localhost:8000/api/v1/download/{job_id}/excel -o report.xlsx
```

### Performance Testing

Expected performance (40 queries, GPT-4 only):
- **First run:** 3-5 minutes
- **Cached run:** 1-2 minutes (same industry)
- **Database writes:** < 1 second (bulk operations)

Check logs for timing:
```powershell
Get-Content logs/ai_visibility_*.log | Select-String "elapsed"
```

### Validation Checklist

Before submitting analysis:
- [ ] Backend running: http://localhost:8000/health
- [ ] Frontend accessible: http://localhost:3000
- [ ] API keys configured in `.env`
- [ ] Database initialized (SQLite file or PostgreSQL)
- [ ] Logs directory exists: `logs/`

After analysis completes:
- [ ] Job status = "completed"
- [ ] Overall score calculated (0-100)
- [ ] All queries have results
- [ ] No errors in logs
- [ ] Excel/CSV downloads work

---

## Troubleshooting

### Backend Issues

**Error: "No module named 'backend'"**
```powershell
# Ensure you're in backend directory
cd backend
python -m uvicorn api.main:app --reload
```

**Error: "spacy model not found"**
```powershell
python -m spacy download en_core_web_sm
```

**Error: Database locked (SQLite)**
```powershell
# Stop all backend processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process

# Delete database and restart
Remove-Item ai_visibility.db -Force
python -m uvicorn api.main:app --reload
```

**Error: "KeyError: 'sentiment'"**
- Issue: Old database missing new columns
- Fix: Delete `ai_visibility.db` and restart backend
- Schema will auto-recreate with new columns

**Error: "SQLite type error: dict not supported"**
- Fixed in latest code
- Tokens now stored as JSON string
- Update to latest code if you see this

### Frontend Issues

**Error: "Cannot fetch from API"**
```powershell
# Check if backend is running
curl http://localhost:8000/health

# Check .env.local file
Get-Content frontend/.env.local
# Should show: NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

**Error: "Module not found"**
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item -Recurse -Force .next
npm install
```

### API Issues

**Error: "Invalid API key"**
- Check `.env` file has correct keys
- No spaces or quotes around keys
- Keys should not have line breaks
- Restart backend after changing `.env`

**Error: "Rate limit exceeded"**
- Reduce `query_count` to 10-20
- Wait a few minutes
- Check API usage at provider dashboard

**Error: "Timeout" or "Connection error"**
- Check internet connection
- Increase timeout in `services/*.py`:
  ```python
  timeout=20.0  # Increase if needed
  ```

### Performance Issues

**Analysis taking > 5 minutes:**
1. Check batch size in `workers/tasks.py` (should be 5)
2. Check timeouts in services (12-20 seconds)
3. Reduce query count to 30
4. Check logs for slow API responses

**Database writes slow:**
- Should use `db.bulk_save_objects()` (fast)
- Not `db.add()` one by one (slow)
- Check `workers/tasks.py` has bulk operations

**Queries not cached:**
```powershell
# Check cache is working
Get-Content logs/ai_visibility_*.log | Select-String "cache"
# Should see "Cache hit" on second run
```

### Migration Issues

**Old code to new service layer:**
- `llm_tester.py` is DELETED (replaced by services/)
- All core modules now use `AIServiceManager`
- Update imports if you see `from core.llm_tester import LLMTester`

**Database schema changes:**
- New columns: `sentiment`, `sentiment_score`
- Changed: `tokens_used` from INTEGER to VARCHAR(500)
- **Solution:** Delete old database, restart backend

---

## Configuration Reference

### Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...           # OpenAI API key

# Optional (system works with just OpenAI)
ANTHROPIC_API_KEY=sk-ant-...    # Claude API key
PERPLEXITY_API_KEY=pplx-...     # Perplexity API key
GOOGLE_API_KEY=AIza...          # Gemini API key

# Database (SQLite by default)
DATABASE_URL=sqlite:///./ai_visibility.db

# Server
PORT=8000
```

### Adjustable Parameters

**Query Count** (frontend/lib/api.ts):
```typescript
query_count: 40  // Default: 40 (faster), Max: 100 (comprehensive)
```

**Batch Size** (workers/tasks.py):
```python
batch_size = 5  // Parallel queries at once (5 is optimal)
```

**Timeouts** (services/*.py):
```python
timeout=15.0  # OpenAI/Claude
timeout=12.0  # Gemini/Perplexity
```

**Cache TTL** (utils/cache.py):
```python
ttl=86400  # 24 hours in seconds
```

---

## Cost Estimates

**Per Analysis (40 queries with GPT-4 only):**
- OpenAI GPT-4: ~$0.15
- **Total: ~$0.15 per report**

**With all 4 models (160 API calls):**
- OpenAI: ~$0.20
- Anthropic Claude: ~$0.15
- Perplexity: ~$0.10
- Google Gemini: ~$0.05
- **Total: ~$0.50 per report**

---

## Next Steps

### For Development:
1. Read through this guide
2. Set up local environment
3. Run test analysis (10 queries)
4. Check logs for any errors
5. Test frontend dashboard

### For Hackathon Demo:
1. Create cached results (2-3 brands)
2. Practice live demo flow
3. Have backup slides ready
4. Test API rate limits beforehand
5. Monitor costs during demo

### For Production:
1. Switch to PostgreSQL (not SQLite)
2. Add Redis for caching
3. Set up monitoring (Sentry, DataDog)
4. Implement API rate limit handling
5. Add user authentication

---

**For questions or issues, check logs first: `logs/ai_visibility_*.log`**
