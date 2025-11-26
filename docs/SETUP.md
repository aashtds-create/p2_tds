# Setup Guide

Complete guide to setting up the LLM Analysis Quiz Solver locally.

## Prerequisites

### Required
- **Python 3.10 or higher**
- **Gemini API Key** - [Get one here](https://aistudio.google.com/app/apikey) (Free)
- **FFmpeg** - For audio processing

### System-Specific Installation

#### Windows (WSL/Linux Subsystem)
```bash
sudo apt update
sudo apt install -y ffmpeg
```

#### Windows (Native)
```bash
choco install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt install -y ffmpeg
```

---

## Installation Steps

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd project2
```

### 2. Create Virtual Environment

**Windows (WSL/Linux):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (Native):**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browser

```bash
playwright install chromium
```

This downloads the Chromium browser for web scraping (~170MB).

### 5. Configure Environment Variables

Create `src/.env` file:

```bash
# Using text editor
nano src/.env

# Or create directly
echo "GEMINI_API_KEY=your_actual_api_key_here" > src/.env
```

**Required variables:**
```env
GEMINI_API_KEY=AIzaSy...your_actual_key...
```

**How to get Gemini API Key:**
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy and paste into `src/.env`

### 6. Verify Installation

Run quick test:

```bash
# Test Gemini API connection
python -c "import os; from dotenv import load_dotenv; load_dotenv('src/.env'); print('✅ API Key loaded' if os.getenv('GEMINI_API_KEY') else '❌ API Key not found')"

# Test Playwright installation
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright installed')"
```

---

## Running the Server

### Development Mode

```bash
python src/api/endpoint.py
```

Server starts at: `http://localhost:8000`

You should see:
```
INFO:     Started server process [1234]
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Test the Endpoint

**Using curl:**
```bash
curl -X POST http://localhost:8000/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "secret": "your_secret",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
```

**Using Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/quiz",
    json={
        "email": "your@email.com",
        "secret": "your_secret",
        "url": "https://tds-llm-analysis.s-anand.net/demo"
    }
)
print(response.json())
```

---

## Troubleshooting

### Common Issues

#### 1. "GEMINI_API_KEY not found"

**Solution:**
- Make sure `src/.env` file exists
- Check that `.env` is in the `src/` directory (not root)
- Verify API key is correct
- No quotes needed around the API key value

#### 2. "Playwright not found" or "Browser not installed"

**Solution:**
```bash
playwright install chromium
```

If still fails:
```bash
pip install playwright --force-reinstall
playwright install chromium
```

#### 3. "ffmpeg not found" (when using local Whisper)

**Solution:**
- Install ffmpeg for your OS (see Prerequisites)
- Or rely on Gemini Audio API (no ffmpeg needed)

#### 4. "Port 8000 already in use"

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in endpoint.py
```

#### 5. "Module not found" errors

**Solution:**
```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Optional: Install Local Whisper

For offline audio transcription (slower but works without internet):

```bash
pip install openai-whisper
```

**Note:** This is optional. Gemini Audio API is faster and doesn't require this.

---

## Verification Checklist

Before deploying, verify:

- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip list`)
- [ ] Playwright browser installed
- [ ] `src/.env` file exists with `GEMINI_API_KEY`
- [ ] Server starts without errors
- [ ] Test endpoint responds correctly
- [ ] FFmpeg installed (if using local Whisper)

---

## Next Steps

1. **Read Documentation:**
   - [Quick Start Guide](QUICK_START.md)
   - [Project Guide](PROJECT_GUIDE.md)
   - [Gemini Audio Setup](GEMINI_AUDIO_SETUP.md)

2. **Run Tests:**
   ```bash
   python tests/test_parser.py
   ```

3. **Deploy:**
   - See main [README.md](../README.md) for deployment instructions

---

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review logs in terminal for error messages
3. Verify all prerequisites are installed
4. Check that `src/.env` file has correct API key

---

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key | `AIzaSy...` |

---

**Ready to proceed?** Start the server with `python src/api/endpoint.py`! 🚀

