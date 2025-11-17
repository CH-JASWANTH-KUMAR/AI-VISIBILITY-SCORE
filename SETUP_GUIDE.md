# SETUP GUIDE - AI Visibility Score Tracker

## Quick Setup (Windows PowerShell)

### Option 1: Docker Setup (Easiest - Recommended)

1. **Install Prerequisites**
   - Install Docker Desktop for Windows
   - Download from: https://www.docker.com/products/docker-desktop

2. **Configure Environment**
```powershell
cd F:\BUILATHON

# Copy environment template
Copy-Item config\.env.example -Destination .env

# Edit .env file and add your API keys
notepad .env
```

3. **Add Your API Keys to .env**
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...
GOOGLE_API_KEY=AIza...
```

4. **Start Everything**
```powershell
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

5. **Stop When Done**
```powershell
docker-compose down
```

---

### Option 2: Manual Setup (More Control)

#### Step 1: Setup Backend

```powershell
cd F:\BUILATHON\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

#### Step 2: Setup PostgreSQL

**Option A: Use Docker**
```powershell
docker run -d \
  --name ai_visibility_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ai_visibility \
  -p 5432:5432 \
  postgres:15-alpine
```

**Option B: Install PostgreSQL**
1. Download: https://www.postgresql.org/download/windows/
2. Install and create database:
```sql
CREATE DATABASE ai_visibility;
```

#### Step 3: Configure Environment

```powershell
# Copy template
Copy-Item ..\config\.env.example -Destination .env

# Edit and add your API keys
notepad .env
```

Update `.env`:
```env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_visibility
```

#### Step 4: Initialize Database

```powershell
python -c "from db.database import init_db; init_db()"
```

#### Step 5: Start Backend

```powershell
python -m uvicorn api.main:app --reload --port 8000
```

Backend running at: http://localhost:8000

#### Step 6: Setup Frontend

Open new PowerShell window:

```powershell
cd F:\BUILATHON\frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Start development server
npm run dev
```

Frontend running at: http://localhost:3000

---

## Testing Your Setup

### 1. Check Backend Health

```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "services": {
    "api": "running",
    "worker": "available"
  }
}
```

### 2. Test Frontend

Open browser: http://localhost:3000

You should see the input form.

### 3. Run Test Analysis

```powershell
# Create test analysis
$body = @{
    brand_name = "Test Brand"
    website_url = "https://example.com"
    query_count = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/analyze" -Method Post -Body $body -ContentType "application/json"
```

---

## Getting API Keys

### OpenAI (ChatGPT)
1. Go to: https://platform.openai.com/api-keys
2. Sign up / Log in
3. Click "Create new secret key"
4. Copy key (starts with `sk-`)

### Anthropic (Claude)
1. Go to: https://console.anthropic.com/
2. Sign up / Log in
3. Go to API Keys section
4. Create new key (starts with `sk-ant-`)

### Perplexity
1. Go to: https://www.perplexity.ai/settings/api
2. Sign up / Log in
3. Generate API key (starts with `pplx-`)

### Google AI (Gemini)
1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Create API key (starts with `AIza`)

---

## Create Demo Data (Optional)

This creates cached results for instant demos:

```powershell
cd F:\BUILATHON

# Make sure backend is running
python scripts\cache_demo_data.py
```

This will:
- Create analysis for HelloFresh
- Create analysis for Sunbasket
- Take ~10-15 minutes (real API calls)
- Store results in database

---

## Troubleshooting

### Backend Issues

**Error: "No module named 'backend'"**
```powershell
# Make sure you're in the backend directory
cd F:\BUILATHON\backend
python -m uvicorn api.main:app --reload
```

**Error: "Could not connect to database"**
```powershell
# Check if PostgreSQL is running
docker ps  # Should show postgres container

# Or check PostgreSQL service
Get-Service postgresql*
```

**Error: "spacy model not found"**
```powershell
python -m spacy download en_core_web_sm
```

### Frontend Issues

**Error: "Cannot find module 'next'"**
```powershell
Remove-Item -Recurse -Force node_modules
npm install
```

**Error: "API calls failing"**
- Check if backend is running: http://localhost:8000/health
- Check `.env.local` has correct API URL
- Check browser console for CORS errors

### API Key Issues

**Error: "Invalid API key"**
- Check `.env` file has correct keys
- No spaces or quotes around keys
- Keys should not have line breaks

**Error: "Rate limit exceeded"**
- Reduce `query_count` to 10-20
- Wait a few minutes and try again
- Check your API usage limits

---

## Development Workflow

### Backend Development

```powershell
cd backend

# Activate venv
.\venv\Scripts\activate

# Run with auto-reload
python -m uvicorn api.main:app --reload --port 8000

# Run tests
pytest

# Check single module
python core\query_generator.py
```

### Frontend Development

```powershell
cd frontend

# Development mode (hot reload)
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Database Management

```powershell
# Reset database
docker-compose down -v
docker-compose up -d postgres

# Re-initialize
cd backend
python -c "from db.database import init_db; init_db()"

# Check database
docker exec -it ai_visibility_db psql -U postgres -d ai_visibility -c "SELECT * FROM analysis_jobs LIMIT 5;"
```

---

## Production Deployment

### Deploy Backend (Railway/Render)

1. Push to GitHub
2. Connect to Railway/Render
3. Add environment variables
4. Deploy

### Deploy Frontend (Vercel)

1. Push to GitHub
2. Import to Vercel
3. Add `NEXT_PUBLIC_API_URL` environment variable
4. Deploy

---

## Next Steps

1. ✅ Setup complete
2. 📝 Test with a real brand
3. 🎨 Customize UI/branding
4. 📊 Create demo data for hackathon
5. 🚀 Practice your pitch!

---

**Need help? Check README.md or open an issue!**
