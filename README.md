# AI Visibility Score Tracker

![AI Visibility Score Tracker](https://img.shields.io/badge/AI-Visibility_Tracker-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-teal)

> **Measure how often your brand appears in AI model responses across ChatGPT, Claude, Perplexity, and Gemini.**

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 15+**
- **Redis** (optional, for caching)
- **API Keys:**
  - OpenAI API Key
  - Anthropic API Key
  - Perplexity API Key
  - Google AI API Key

### Installation (Local Setup)

#### 1. Clone and Setup Environment

```powershell
cd BUILATHON

# Create .env file from example
Copy-Item config\.env.example -Destination .env

# Edit .env and add your API keys
notepad .env
```

#### 2. Backend Setup

```powershell
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Initialize database
python -c "from db.database import init_db; init_db()"

# Run backend
python -m uvicorn api.main:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`

API docs: `http://localhost:8000/docs`

#### 3. Frontend Setup

```powershell
cd ../frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

---

## 🐳 Docker Setup (Recommended)

```powershell
# Create .env file with API keys
Copy-Item config\.env.example -Destination .env

# Edit and add your API keys
notepad .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services:
- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

---

## 📁 Project Structure

```
BUILATHON/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI application
│   │   ├── routes.py            # API endpoints
│   │   └── schemas.py           # Pydantic models
│   ├── core/
│   │   ├── industry_detector.py  # Industry classification
│   │   ├── query_generator.py    # Query generation
│   │   ├── llm_tester.py         # AI model testing
│   │   ├── mention_detector.py   # Brand mention detection
│   │   ├── visibility_scorer.py  # Score calculation
│   │   └── report_generator.py   # Excel/CSV reports
│   ├── db/
│   │   ├── models.py            # SQLAlchemy models
│   │   └── database.py          # DB connection
│   ├── workers/
│   │   └── tasks.py             # Background job processing
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Home page (input form)
│   │   ├── layout.tsx           # Root layout
│   │   └── dashboard/[id]/page.tsx  # Results dashboard
│   ├── components/
│   │   ├── ScoreCard.tsx        # Visibility score display
│   │   ├── QueryTable.tsx       # Full query transparency
│   │   ├── ModelComparison.tsx  # Model comparison chart
│   │   └── CategoryChart.tsx    # Category breakdown
│   ├── lib/
│   │   └── api.ts               # API client
│   └── package.json
│
├── config/
│   └── .env.example             # Environment template
├── data/
│   └── cached_results/          # Cached demo data
├── reports/                     # Generated Excel/CSV reports
├── docker-compose.yml
└── README.md
```

---

## 🎯 How It Works

### 1. **Industry Detection**
- Scrapes brand website
- Extracts text content
- Uses GPT-4 to classify industry
- Falls back to keyword matching

### 2. **Query Generation**
- Generates 50-100 industry-specific queries
- Uses templates + GPT-4 for diversity
- Deduplicates using semantic embeddings
- Covers: best-of, comparisons, reviews, how-to, budget

### 3. **AI Model Testing**
- Tests each query across 4 AI models in parallel
- Captures full responses
- Handles rate limiting automatically
- Stores raw data for transparency

### 4. **Mention Detection**
- Exact and fuzzy brand name matching
- Extracts ranking position (e.g., #1, #2)
- Identifies competitor brands using NER
- Calculates confidence scores

### 5. **Visibility Scoring**
- **Mention Rate (40%)**: How often mentioned
- **Rank Score (30%)**: Average ranking position
- **Competitor Dominance (20%)**: Beats competitors
- **Model Consistency (10%)**: Consistent across models

### 6. **Report Generation**
- Multi-sheet Excel export
- Summary statistics
- Category breakdown
- Model comparison
- Full query transparency

---

## 📊 API Endpoints

### Start Analysis
```http
POST /api/v1/analyze
Content-Type: application/json

{
  "brand_name": "HelloFresh",
  "website_url": "https://www.hellofresh.com",
  "query_count": 60
}

Response:
{
  "job_id": "abc-123-def",
  "status": "pending",
  "message": "Analysis started for HelloFresh"
}
```

### Get Job Status
```http
GET /api/v1/status/{job_id}

Response:
{
  "job_id": "abc-123-def",
  "brand_name": "HelloFresh",
  "status": "completed",
  "progress": 100,
  "overall_score": 78.5,
  "mention_rate": 65.0,
  "total_queries": 60,
  "total_mentions": 39
}
```

### Get Full Report
```http
GET /api/v1/report/{job_id}

Returns comprehensive report with all results
```

### Download Report
```http
GET /api/v1/download/{job_id}/excel
GET /api/v1/download/{job_id}/csv

Downloads Excel or CSV file
```

---

## 🎬 Demo Strategy for Hackathon

### Pre-Demo Setup

1. **Cache Example Brands** (Run 30 mins before demo)
```powershell
# Start backend
cd backend
python -m uvicorn api.main:app

# In another terminal, create test analyses
python scripts/cache_demo_data.py
```

This creates:
- **Brand A** (HelloFresh): High score ~78
- **Brand B** (Sunbasket): Moderate score ~62

### Live Demo Script (5 Minutes)

**Minute 1: Problem**
> "When you Google 'best meal kits', brands obsess over SEO rankings. But 40% of consumers now ask ChatGPT, Claude, or Perplexity. Brands have ZERO visibility into whether they're being recommended. We built the first AI Visibility Score Tracker."

**Minute 2: Show Cached Results**
- Open `http://localhost:3000/dashboard/hellofresh-cached`
- "We analyzed 100 queries across 4 AI models"
- Point to **78.5/100 score** - "Strong Visibility"
- "HelloFresh appears in 65% of queries, averaging rank #2"

**Minute 3: Transparency**
- Scroll to query table
- Click "View" on a query
- Show full AI response
- "Complete transparency - every query, every response, downloadable"

**Minute 4: Live Test**
- Enter new brand: "Factor Meals"
- Show progress bar
- Takes 1-2 minutes for 3 queries × 4 models = 12 API calls
- Dashboard loads: "Factor scores 62/100"

**Minute 5: Impact**
> "This solves three problems:
> 1. **Brand Intelligence** - Are we being recommended?
> 2. **Competitive Analysis** - Who dominates our space?
> 3. **AI Optimization** - Which content gaps exist?
> 
> Next: Track over time, A/B test changes, predict trends"

---

## 🧪 Testing

### Test Single Module
```powershell
# Backend
cd backend
python core/industry_detector.py
python core/query_generator.py
python core/llm_tester.py

# Frontend
cd frontend
npm run build
```

### Run Full Test
```powershell
# Create test analysis
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"brand_name": "Test Brand", "website_url": "https://example.com", "query_count": 10}'
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for ChatGPT | ✅ Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | ✅ Yes |
| `PERPLEXITY_API_KEY` | Perplexity API key | ✅ Yes |
| `GOOGLE_API_KEY` | Google AI API key for Gemini | ✅ Yes |
| `DATABASE_URL` | PostgreSQL connection string | ✅ Yes |
| `REDIS_URL` | Redis connection string | Optional |
| `PORT` | Backend port (default: 8000) | Optional |

### Cost Estimates

**Per Full Analysis (60 queries × 4 models = 240 API calls):**
- OpenAI (ChatGPT-4): ~$0.20
- Anthropic (Claude): ~$0.15
- Perplexity: ~$0.10
- Google (Gemini): ~$0.05
- **Total: ~$0.50 per report**

---

## 🚧 Troubleshooting

### Backend won't start
```powershell
# Check Python version
python --version  # Must be 3.11+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check database connection
python -c "from backend.db.database import engine; print(engine.connect())"
```

### Frontend errors
```powershell
# Delete node_modules and reinstall
Remove-Item -Recurse -Force node_modules
Remove-Item -Recurse -Force .next
npm install
```

### API rate limits
- Reduce `query_count` to 20-30
- Add delays in `llm_tester.py`
- Use cached results for demos

### Database errors
```powershell
# Reset database
docker-compose down -v
docker-compose up -d postgres
python -c "from backend.db.database import init_db; init_db()"
```

---

## 📈 Future Enhancements

### MVP → V1.0
- [ ] Historical tracking (monitor score changes)
- [ ] Scheduled re-analysis (weekly/monthly)
- [ ] Custom query builder
- [ ] Sentiment analysis on mentions
- [ ] Industry benchmarking
- [ ] Email alerts for score changes

### V1.0 → V2.0
- [ ] Multi-language support
- [ ] API access for developers
- [ ] Team collaboration features
- [ ] White-label reports
- [ ] Integration with marketing tools
- [ ] Predictive trend analysis

---

## 🤝 Contributing

This is a hackathon project! Contributions welcome:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- OpenAI, Anthropic, Perplexity, Google for AI APIs
- FastAPI for amazing Python web framework
- Next.js for React framework
- spaCy for NLP capabilities

---

## 📧 Contact

**Hackathon Team:** AI Visibility Trackers

For questions or demo requests, open an issue!

---

**Built with ❤️ for the BUILATHON Hackathon 2025**
