# 🔧 HOW TO FIX API QUOTA AND TEST SYSTEM

## ⚠️ CRITICAL ISSUE

**Problem:** OpenAI API key has $0 credits remaining
**Error:** `Error code: 429 - insufficient_quota`
**Impact:** System cannot run ANY analysis

---

## ✅ SOLUTION: Add OpenAI Credits

### Step 1: Check Current Quota
1. Go to https://platform.openai.com/account/usage
2. Log in with your OpenAI account
3. Check "Current usage" and "Billing limits"

### Step 2: Add Credits
1. Go to https://platform.openai.com/account/billing/overview
2. Click **"Add payment details"** or **"Add credits"**
3. Add **$5-10** (enough for 100+ analyses)
4. Wait 1-2 minutes for credits to activate

### Step 3: Verify API Key
1. Check your current API key in `.env`:
   ```
   OPENAI_API_KEY=sk-proj-wq4Px...
   ```
2. If needed, create new key at https://platform.openai.com/api-keys
3. Update `.env` file with new key
4. Restart backend:
   ```powershell
   cd f:\BUILATHON
   python -m uvicorn backend.api.main:app --reload --port 8000
   ```

---

## 🧪 TESTING AFTER FIX

### Test 1: Simple API Call (5 seconds)
```powershell
# Test OpenAI API directly
cd f:\BUILATHON
python -c "from openai import OpenAI; import os; client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')); response = client.chat.completions.create(model='gpt-4', messages=[{'role': 'user', 'content': 'Say hello'}]); print(response.choices[0].message.content)"
```

**Expected:** "Hello!" or similar greeting
**If Error 429:** Credits not activated yet, wait 2 minutes

### Test 2: Run Xentro Analysis (3-5 minutes)
1. Open frontend: http://localhost:3000
2. Submit analysis:
   - Brand Name: **Xentro**
   - Website: https://xentro.com
   - Query Count: **40**
3. Monitor progress in dashboard
4. Check logs:
   ```powershell
   Get-Content logs/ai_visibility_*.log -Tail 50
   ```

**Expected Output:**
```
✅ OpenAI GPT-4 responded successfully
💾 Cached response for ChatGPT-4
[job_id] Saved 40 results
Job status: completed
Overall Score: 45-65%
```

### Test 3: Advanced Analytics (30 seconds)
```bash
# After analysis completes, get job_id from dashboard
# Call advanced analytics endpoint
curl http://localhost:8000/api/v1/advanced-analytics/{job_id}
```

**Expected:** JSON with all 10 features:
- feature_1_gap_analysis
- feature_2_competitor_insights
- feature_5_model_behavior
- feature_7_recommendations
- etc.

---

## 💰 COST ESTIMATES

### OpenAI GPT-4 Pricing (as of 2024)
- **Input:** $0.03 per 1K tokens
- **Output:** $0.06 per 1K tokens

### Per Analysis Costs (40 queries)
- **40 queries × 4 models = 160 API calls**
- But with caching: ~80 unique calls
- Average tokens: 300 input + 500 output = 800 tokens per call
- **Total tokens:** 80 × 800 = 64,000 tokens
- **Cost per analysis:** $3-5

### $10 Credit Buys:
- **2-3 full analyses** (40 queries each)
- **100-150 individual queries**

### Optimization Tips:
1. **Use cache** (saves 50% on repeat queries)
2. **Test with 20 queries first** (costs $1.50)
3. **Clear cache** only when testing changes

---

## 🔍 TROUBLESHOOTING

### Issue 1: "Error 429" after adding credits
**Solution:** Wait 2-5 minutes for billing to update

### Issue 2: "Invalid API key"
**Solution:**
1. Regenerate key at https://platform.openai.com/api-keys
2. Update `.env` file
3. Restart backend

### Issue 3: "Rate limit exceeded"
**Solution:**
- You're on free tier (very slow)
- Upgrade to paid tier: https://platform.openai.com/account/billing/overview
- Or reduce parallel queries from 5 to 2

### Issue 4: Cache not working
**Solution:**
1. Check cache stats:
   ```bash
   curl http://localhost:8000/api/v1/cache/stats
   ```
2. If needed, clear cache:
   ```bash
   curl -X POST http://localhost:8000/api/v1/cache/clear
   ```

---

## 🎯 ALTERNATIVE: Use Gemini (Free Tier)

If you can't add OpenAI credits immediately, re-enable Gemini:

### Step 1: Get Gemini API Key (FREE)
1. Go to https://makersuite.google.com/app/apikey
2. Create new API key
3. Copy key

### Step 2: Update .env
```bash
# Uncomment this line in .env
GOOGLE_API_KEY=your_gemini_key_here
```

### Step 3: Fix Model Name
Edit `backend/services/gemini_service.py` line 22:
```python
# Try these model names:
self.model_name = "gemini-1.5-flash"  # Option 1
# OR
self.model_name = "gemini-pro"        # Option 2
```

### Step 4: Restart Backend
```powershell
cd f:\BUILATHON
python -m uvicorn backend.api.main:app --reload --port 8000
```

**Note:** Gemini is slower but FREE for 60 queries/minute.

---

## 📊 VERIFY SYSTEM STATUS

### Check 1: Backend Running
```powershell
curl http://localhost:8000/api/v1/cache/stats
```
**Expected:** JSON with cache stats

### Check 2: OpenAI Available
Check logs for:
```
🚀 AI Service Manager initialized
📊 Available models: ChatGPT-4
```

### Check 3: Database Schema
```powershell
cd f:\BUILATHON
python -c "from backend.db.database import engine; import sqlite3; conn = sqlite3.connect('ai_visibility.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(results)'); print([row[1] for row in cursor.fetchall()])"
```
**Expected:** List including 'sentiment', 'sentiment_score', 'tokens_used'

---

## 🚀 READY TO DEMO

After adding credits and testing:

1. ✅ OpenAI API working
2. ✅ Cache reducing costs
3. ✅ All 10 features accessible
4. ✅ Analysis completes in 3-5 minutes
5. ✅ Advanced analytics endpoint works

**You're ready for hackathon!** 🏆

---

## 📞 NEED HELP?

**Quick Diagnostics:**
```powershell
# Check all API keys
cd f:\BUILATHON
Get-Content .env | Select-String "API_KEY"

# Check backend logs
Get-Content logs/ai_visibility_*.log | Select-String "Error" -Context 2

# Test OpenAI directly
python -c "import os; print('OpenAI Key:', os.getenv('OPENAI_API_KEY')[:20] + '...' if os.getenv('OPENAI_API_KEY') else 'NOT FOUND')"
```

**Common Commands:**
```powershell
# Restart backend
python -m uvicorn backend.api.main:app --reload --port 8000

# Clear cache
curl -X POST http://localhost:8000/api/v1/cache/clear

# Check cache stats
curl http://localhost:8000/api/v1/cache/stats

# View recent jobs
curl http://localhost:8000/api/v1/jobs
```

---

## 💡 COST OPTIMIZATION TIPS

1. **Start with 20 queries** for testing ($1.50)
2. **Use cache** (automatic, saves 50%)
3. **Run full analysis** only for demo (40-60 queries)
4. **Demo mode:** Show cached results from previous run
5. **Judges demo:** Run fresh analysis with 30 queries ($2.50)

**Total demo cost:** $5-7 for multiple test runs + 1 live demo

---

**ONCE CREDITS ADDED, YOU'RE GOOD TO GO!** 🚀
