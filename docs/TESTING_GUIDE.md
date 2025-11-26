# 🧪 Testing Guide

## 🚀 **Quick Test Commands**

### **Step 1: Start the Server**

```bash
# Make sure you're in project root
cd D:\Ashish\ug\iitmbs\2025_sept_term\tds\project2

# Activate virtual environment (if using one)
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Run the server
python src/api/endpoint.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### **Step 2: Test with Demo Quiz** (Open new terminal)

#### **Simple Demo (Scraping Task):**
```bash
curl -X POST http://localhost:8000/quiz ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"23f3003728@ds.study.iitm.ac.in\", \"secret\": \"somethingsomethingedosomething\", \"url\": \"https://tds-llm-analysis.s-anand.net/demo\"}"
```

**Expected Response (immediate):**
```json
{
  "status": "accepted",
  "message": "Quiz task received and processing started"
}
```

**Expected Logs (in server terminal):**
```
INFO - Received quiz request for email: 23f3003728@ds.study.iitm.ac.in
INFO - Starting quiz solver with deadline: 2025-11-26 12:03:00
INFO - Processing quiz at URL: https://tds-llm-analysis.s-anand.net/demo
INFO - Rendering page: https://tds-llm-analysis.s-anand.net/demo
INFO - Extracted 150 characters from page
INFO - Parsed question: ...
INFO - Task type: scraping
INFO - Generated answer: 12345
INFO - Submitting answer to https://tds-llm-analysis.s-anand.net/submit
INFO - Answer submitted successfully
INFO - Quiz processing completed
```

---

#### **Audio Demo (More Complex):**
```bash
curl -X POST http://localhost:8000/quiz ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"23f3003728@ds.study.iitm.ac.in\", \"secret\": \"somethingsomethingedosomething\", \"url\": \"https://tds-llm-analysis.s-anand.net/demo-audio?id=test123\"}"
```

**This tests:**
- Audio transcription (Gemini)
- CSV processing
- Data filtering
- Answer submission

---

### **Step 3: Health Check**

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "healthy"
}
```

---

## 🎯 **Test Different Scenarios**

### **1. Test API Task**
```bash
curl -X POST http://localhost:8000/quiz ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"23f3003728@ds.study.iitm.ac.in\", \"secret\": \"somethingsomethingedosomething\", \"url\": \"https://tds-llm-analysis.s-anand.net/demo-api\"}"
```

### **2. Test PDF Task**
```bash
curl -X POST http://localhost:8000/quiz ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"23f3003728@ds.study.iitm.ac.in\", \"secret\": \"somethingsomethingedosomething\", \"url\": \"https://tds-llm-analysis.s-anand.net/demo-pdf\"}"
```

### **3. Test CSV Task**
```bash
curl -X POST http://localhost:8000/quiz ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"23f3003728@ds.study.iitm.ac.in\", \"secret\": \"somethingsomethingedosomething\", \"url\": \"https://tds-llm-analysis.s-anand.net/demo-csv\"}"
```

---

## 🔍 **What to Look For**

### **✅ Success Indicators:**

**1. API Response:**
- Status code: 200
- Response time: < 1 second
- JSON with "status": "accepted"

**2. Server Logs:**
- "Received quiz request" appears
- "Processing quiz at URL" appears
- No error messages
- "Quiz processing completed" at the end

**3. Task Execution:**
- Page rendered successfully
- Data fetched/processed
- Answer generated
- Submission successful

### **❌ Common Issues:**

**1. 403 Forbidden:**
```json
{"detail": "Invalid secret"}
```
**Fix:** Check your `.env` file has correct SECRET

**2. Connection Refused:**
```
curl: (7) Failed to connect to localhost port 8000
```
**Fix:** Server not running. Start it with `python src/api/endpoint.py`

**3. Playwright Error:**
```
ERROR - Playwright not installed
```
**Fix:** Run `playwright install chromium`

**4. Gemini API Error:**
```
ERROR - Gemini API error 400
```
**Fix:** Check GEMINI_API_KEY in `.env`

---

## 📊 **Understanding the Logs**

### **Normal Flow:**
```
1. INFO - Received quiz request
   → API got your curl request

2. INFO - Starting quiz solver with deadline
   → Background task started (3-minute timer)

3. INFO - Rendering page: https://...
   → Playwright opening page

4. INFO - Extracted N characters
   → Page content extracted

5. INFO - Parsed question: ...
   → Instructions understood

6. INFO - Task type: X
   → Identified task type (api/scraping/pdf/audio/csv)

7. INFO - Generated answer: Y
   → LLM produced answer

8. INFO - Submitting answer
   → Posting to professor's server

9. INFO - Answer submitted successfully
   → Professor's server accepted it

10. INFO - Quiz processing completed
    → Done! ✅
```

### **Error Flow:**
```
1. ERROR - Gemini API error
   → Check API key

2. ERROR - Cannot navigate to invalid URL
   → URL issue (check if relative URL needs base_url)

3. ERROR - Audio processing failed
   → Audio file format issue or API problem

4. ERROR - CSV processing failed
   → CSV download or parsing issue
```

---

## 🛠️ **Debugging Tips**

### **1. Enable Verbose Logging**

Edit `src/api/endpoint.py`:
```python
# Change this:
logging.basicConfig(level=logging.INFO)

# To this:
logging.basicConfig(level=logging.DEBUG)
```

### **2. Check Playwright Browser**

Make Playwright visible (not headless):

Edit `src/quiz_solver/renderer.py`:
```python
# Change this:
browser = await playwright.chromium.launch(headless=True)

# To this:
browser = await playwright.chromium.launch(headless=False)
```

Now you'll see the browser window!

### **3. Add Breakpoints**

Add this where you want to pause:
```python
import pdb; pdb.set_trace()
```

---

## 📈 **Performance Benchmarks**

| Task Type | Expected Time |
|-----------|---------------|
| API Response | < 1s |
| Page Render | 2-3s |
| Scraping | 5-10s |
| PDF Processing | 10-15s |
| CSV Processing | 15-20s |
| Audio (Gemini) | 20-30s |
| Full Quiz (3 pages) | 40-60s |

If times are much longer, check:
- Internet connection
- API rate limits
- System resources

---

## 🧪 **Test Checklist**

Before submission, test all these:

- [ ] Health check works
- [ ] Demo endpoint works
- [ ] Scraping task works
- [ ] API task works
- [ ] PDF task works (if available)
- [ ] CSV task works (if available)
- [ ] Audio task works (if available)
- [ ] Error handling works (test with wrong secret)
- [ ] Logs are clean and informative
- [ ] Response time is fast (< 1s for API)

---

## 🎯 **Quick Test Script**

Save this as `test_all.ps1`:

```powershell
# Test script for all endpoints

Write-Host "`n🧪 Testing Quiz Solver API`n" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "1️⃣ Testing health check..." -ForegroundColor Yellow
$health = curl -s http://localhost:8000/health
Write-Host "Response: $health`n" -ForegroundColor Green

# Test 2: Demo Quiz
Write-Host "2️⃣ Testing demo quiz..." -ForegroundColor Yellow
$demo = curl -X POST http://localhost:8000/quiz `
  -H "Content-Type: application/json" `
  -d '{"email": "23f3003728@ds.study.iitm.ac.in", "secret": "somethingsomethingedosomething", "url": "https://tds-llm-analysis.s-anand.net/demo"}'
Write-Host "Response: $demo`n" -ForegroundColor Green

Write-Host "✅ Tests completed! Check server logs for details.`n" -ForegroundColor Cyan
```

Run it:
```bash
./test_all.ps1
```

---

## 📝 **Notes**

1. **First run might be slower** (Playwright downloads browser)
2. **Audio tasks take longer** (transcription time)
3. **Watch server logs** for detailed progress
4. **Keep terminal open** to see logs in real-time

---

**Ready to test? Start your server and run the curl commands!** 🚀

