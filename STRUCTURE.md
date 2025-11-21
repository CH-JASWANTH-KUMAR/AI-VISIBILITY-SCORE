# Project Structure - AI Visibility Score Tracker

> Clean, organized architecture after optimization and refactoring

---

## 📁 Directory Overview

```
BUILATHON/
├── 📄 Documentation (3 files - consolidated)
│   ├── README.md              # Main project overview, quickstart, features
│   ├── DEVELOPMENT.md         # Setup, architecture, testing, troubleshooting
│   └── CHANGELOG.md           # Bug fixes, optimizations, version history
│
├── 🖥️ Backend (Python/FastAPI)
│   ├── api/                   # REST API layer
│   ├── core/                  # Business logic
│   ├── db/                    # Database models
│   ├── services/              # AI service integrations (NEW)
│   ├── utils/                 # Shared utilities (NEW)
│   └── workers/               # Background job processing
│
├── 🎨 Frontend (Next.js/TypeScript)
│   ├── app/                   # Pages (App Router)
│   ├── components/            # React components
│   └── lib/                   # API client
│
├── ⚙️ Configuration
│   └── config/                # Environment templates
│
└── 📊 Generated Files
    ├── logs/                  # Application logs
    ├── reports/               # Excel/CSV exports
    └── ai_visibility.db       # SQLite database
```

---

## 🖥️ Backend Structure (Python)

### `/backend/api/` - REST API Layer
```
api/
├── main.py              (88 lines)   # FastAPI app initialization, CORS
├── routes.py            (412 lines)  # All API endpoints
├── schemas.py           (77 lines)   # Pydantic request/response models
└── __init__.py
```

**Key Endpoints:**
- `POST /api/v1/analyze` - Start brand analysis
- `GET /api/v1/status/{job_id}` - Check job progress
- `GET /api/v1/report/{job_id}` - Get full report
- `GET /api/v1/download/{job_id}/excel` - Download Excel report

---

### `/backend/services/` - AI Service Layer (NEW ✨)
```
services/
├── openai_service.py       (179 lines)  # OpenAI GPT-4 integration
├── gemini_service.py       (155 lines)  # Google Gemini integration
├── claude_service.py       (108 lines)  # Anthropic Claude integration
├── perplexity_service.py   (137 lines)  # Perplexity integration
├── service_manager.py      (179 lines)  # Coordinates all services
└── __init__.py
```

**Architecture:**
- **Each service:** Independent, timeout-protected, error-handling
- **Service Manager:** Parallel execution, fallback logic, model selection
- **Features:** Async/await, retry logic, token tracking, structured responses

**Why This Was Created:**
Replaced monolithic `llm_tester.py` (275 lines) with clean service-oriented design.

---

### `/backend/core/` - Business Logic
```
core/
├── industry_detector.py       (232 lines)  # Website scraping + GPT-4 classification
├── query_generator.py         (384 lines)  # Template + LLM query generation
├── mention_detector.py        (345 lines)  # Brand mention detection + sentiment analysis
├── visibility_scorer.py       (278 lines)  # Score calculation algorithm
├── report_generator.py        (377 lines)  # Excel/CSV export with pandas
│
├── 🎯 Advanced Features (Optional)
├── gap_analyzer.py            (305 lines)  # Why brand NOT mentioned analysis
├── competitor_insights.py     (293 lines)  # Reverse-engineer AI reasoning
├── improvement_simulator.py   (388 lines)  # Predict score changes
├── model_behavior.py          (299 lines)  # Per-model bias detection
├── advanced_analytics.py      (510 lines)  # All advanced features bundled
└── __init__.py
```

**Core Pipeline:**
1. `industry_detector.py` → Scrape website → Classify industry
2. `query_generator.py` → Generate 40 industry-specific queries
3. `mention_detector.py` → Detect brand in AI responses + sentiment
4. `visibility_scorer.py` → Calculate 0-100 visibility score
5. `report_generator.py` → Export to Excel/CSV

---

### `/backend/db/` - Database Layer
```
db/
├── database.py     (51 lines)   # SQLAlchemy engine, session management
├── models.py       (133 lines)  # AnalysisJob, Result models
└── __init__.py
```

**Schema (SQLite):**
```sql
-- Jobs table
analysis_jobs (
    id, brand_name, website_url, industry, status,
    progress, overall_score, created_at, completed_at
)

-- Results table  
results (
    id, job_id, query, model, response,
    mentioned, rank_position, 
    sentiment, sentiment_score,  -- NEW in v2.0
    tokens_used,                 -- Changed to JSON string
    response_time
)
```

---

### `/backend/utils/` - Shared Utilities (NEW ✨)
```
utils/
├── cache.py      (46 lines)   # Query caching with 24hr TTL
├── logger.py     (66 lines)   # Structured logging with file rotation
└── __init__.py
```

**Query Cache:**
- Uses MD5 hash keys: `{industry}:{brand}:{count}`
- 24-hour TTL (86400 seconds)
- Second run = instant retrieval

**Logging:**
- File: `logs/ai_visibility_YYYYMMDD.log` (DEBUG level)
- Console: INFO level only
- Auto-rotation: Daily

---

### `/backend/workers/` - Background Processing
```
workers/
├── tasks.py       (275 lines)  # Async job processing with parallel execution
└── __init__.py
```

**Job Flow:**
```python
async def process_analysis_job(job_id):
    1. Update status → "processing"
    2. Detect industry (30s timeout)
    3. Generate queries (with cache, 30s timeout)
    4. Test queries in parallel batches of 5 (20s timeout per batch)
       - asyncio.gather() for true parallelism
       - Bulk database inserts every 5 queries
    5. Calculate visibility score
    6. Update status → "completed"
```

---

## 🎨 Frontend Structure (Next.js)

### `/frontend/app/` - Pages (App Router)
```
app/
├── page.tsx                    (163 lines)  # Home: Input form
├── dashboard/[id]/page.tsx     (447 lines)  # Results dashboard
├── layout.tsx                  (43 lines)   # Root layout + metadata
└── globals.css                 (82 lines)   # Tailwind styles
```

**Routes:**
- `/` - Input form (brand name, website URL, query count)
- `/dashboard/{job_id}` - Results dashboard with charts

---

### `/frontend/components/` - React Components
```
components/
├── ScoreCard.tsx          (91 lines)   # Overall score display with color coding
├── QueryTable.tsx         (156 lines)  # Full query transparency table
├── ModelComparison.tsx    (103 lines)  # Bar chart comparison of models
└── CategoryChart.tsx      (118 lines)  # Category breakdown pie chart
```

**Component Features:**
- TypeScript strict mode
- Tailwind CSS styling
- Responsive design
- Loading states

---

### `/frontend/lib/` - API Client
```
lib/
└── api.ts                 (114 lines)  # Fetch functions for backend API
```

**Functions:**
```typescript
submitAnalysis(brand, url, count)  // POST /analyze
getJobStatus(job_id)               // GET /status/{id}
getFullReport(job_id)              // GET /report/{id}
downloadExcel(job_id)              // GET /download/{id}/excel
downloadCSV(job_id)                // GET /download/{id}/csv
```

---

## ⚙️ Configuration Files

```
config/
└── .env.example            # Environment variable template

Root:
├── docker-compose.yml      (PostgreSQL + Redis setup)
├── requirements.txt        # Python dependencies
└── requirements-minimal.txt # Minimal backend dependencies
```

**Environment Variables:**
```env
# Required
OPENAI_API_KEY=sk-...

# Optional (system works with just OpenAI)
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...
GOOGLE_API_KEY=AIza...

# Database (SQLite default)
DATABASE_URL=sqlite:///./ai_visibility.db
```

---

## 📊 Generated Files & Logs

```
logs/
└── ai_visibility_YYYYMMDD.log   # Daily rotating logs (DEBUG level)

reports/
├── {job_id}_report.xlsx         # Excel report with multiple sheets
└── {job_id}_report.csv          # CSV report (all data)

Root:
└── ai_visibility.db             # SQLite database (auto-created)
```

---

## 🗑️ Files Deleted (Cleanup)

### Removed Legacy Code:
- ❌ `backend/core/llm_tester.py` (275 lines) - Replaced by service layer

### Consolidated Documentation:
- ❌ `SETUP_GUIDE.md` - Merged into DEVELOPMENT.md
- ❌ `TESTING_GUIDE.md` - Merged into DEVELOPMENT.md  
- ❌ `MIGRATION_GUIDE.md` - Merged into CHANGELOG.md
- ❌ `REFACTORING_SUMMARY.md` - Merged into CHANGELOG.md
- ❌ `BUGS_FIXED.md` - Merged into CHANGELOG.md
- ❌ `PERFORMANCE_OPTIMIZATIONS.md` - Merged into CHANGELOG.md
- ❌ `PROJECT_OVERVIEW.md` - Merged into README.md
- ❌ `ADVANCED_FEATURES.md` - Merged into README.md

**Before:** 9 markdown files (confusing)  
**After:** 3 markdown files (clear)

---

## 📈 Code Statistics

### Backend (Python)
- **Total Files:** 30 Python files
- **Total Lines:** ~6,000 lines
- **Services Layer:** 758 lines (NEW)
- **Core Logic:** ~2,500 lines
- **API Layer:** 577 lines

### Frontend (TypeScript/React)
- **Total Files:** 20 TypeScript files
- **Total Lines:** ~1,800 lines
- **Components:** 468 lines
- **Pages:** 653 lines

### Documentation
- **3 Markdown files:** README, DEVELOPMENT, CHANGELOG
- **Total:** ~2,000 lines of documentation

---

## 🔄 Architecture Flow

### Complete Analysis Pipeline

```
1. User Input (Frontend)
   ↓
2. POST /api/v1/analyze (API)
   ↓
3. Create Job in Database
   ↓
4. Background Worker Starts
   ↓
5. Industry Detection (core/industry_detector.py)
   - Scrape website
   - GPT-4 classification
   ↓
6. Query Generation (core/query_generator.py)
   - Check cache first (utils/cache.py)
   - Generate 40 queries with templates
   ↓
7. Parallel AI Testing (workers/tasks.py + services/)
   - Batch size: 5 queries at once
   - asyncio.gather() for parallelism
   - Timeout: 20s per batch
   - Save to DB: bulk_save_objects()
   ↓
8. Mention Detection (core/mention_detector.py)
   - Detect brand name (exact + fuzzy)
   - Extract ranking (#1, #2, etc.)
   - Sentiment analysis (NEW)
   ↓
9. Score Calculation (core/visibility_scorer.py)
   - Mention Rate (40%)
   - Rank Score (30%)
   - Competitor Dominance (20%)
   - Model Consistency (10%)
   ↓
10. Report Generation (core/report_generator.py)
    - Excel multi-sheet export
    - CSV export
    ↓
11. Dashboard Display (Frontend)
    - Score card
    - Query table
    - Model comparison
    - Category breakdown
```

---

## 🎯 Key Design Decisions

### Why Service Layer?
- **Before:** Monolithic `llm_tester.py` mixed all 4 AI models
- **After:** Each model in separate service (OpenAI, Gemini, Claude, Perplexity)
- **Benefits:** Easy to add models, better error isolation, cleaner testing

### Why Query Caching?
- **Problem:** Generating 40 queries took 30-60 seconds
- **Solution:** Cache by `{industry}:{brand}:{count}` with 24hr TTL
- **Result:** Second run = <1 second (50x faster)

### Why Bulk Database Operations?
- **Problem:** Saving results one-by-one took 2-3 seconds per batch
- **Solution:** `db.bulk_save_objects()` saves 5 at once
- **Result:** <0.5 seconds per batch (6x faster)

### Why Aggressive Timeouts?
- **Problem:** Jobs would hang for 30+ minutes on slow API calls
- **Solution:** 12-20 second timeouts on all operations
- **Result:** No infinite waits, always complete or fail fast

### Why SQLite?
- **Choice:** SQLite for simplicity (can switch to PostgreSQL)
- **Benefits:** No separate database server, easy setup
- **Limitation:** No concurrent writes (fine for single-user/demo)

---

## 🚀 Performance Characteristics

### Speed (40 queries, GPT-4 only):
- **First run:** 3-5 minutes
- **Cached run:** 1-2 minutes
- **Database writes:** <0.5 seconds per batch

### Scalability:
- **Parallel queries:** 5 at once (configurable)
- **Batch processing:** 5 queries per batch
- **Memory usage:** ~200MB backend, ~50MB frontend

### Cost (per analysis):
- **OpenAI only:** ~$0.15
- **All 4 models:** ~$0.50

---

## 📝 Development Guidelines

### Adding New AI Model:
1. Create `backend/services/newmodel_service.py`
2. Inherit from base service pattern
3. Implement `query()` method with timeout
4. Add to `service_manager.py`

### Adding New Feature:
1. Create module in `backend/core/`
2. Add API endpoint in `backend/api/routes.py`
3. Add schema in `backend/api/schemas.py`
4. Add frontend component in `frontend/components/`

### Database Schema Change:
1. Update `backend/db/models.py`
2. Delete old database: `Remove-Item ai_visibility.db -Force`
3. Restart backend (auto-creates new schema)

---

## ✅ Clean Project Checklist

- [x] No unused legacy code (llm_tester.py deleted)
- [x] Documentation consolidated (9 files → 3 files)
- [x] Service layer implemented (clean architecture)
- [x] All performance optimizations applied
- [x] All critical bugs fixed
- [x] Consistent code style
- [x] Comprehensive error handling
- [x] Structured logging
- [x] Query caching
- [x] Parallel execution

---

**This structure is hackathon-ready! 🎉**

For setup: See `DEVELOPMENT.md`  
For changes: See `CHANGELOG.md`  
For overview: See `README.md`
