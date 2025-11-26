# ⚡ Quick Start Guide

## 🎯 Current Status

✅ **Your app is configured to use:**
- **Groq** → Audio transcription (Whisper)
- **Gemini** → Text parsing & reasoning
- **aipipe** → (Optional) For text-based LLM calls

---

## 🔑 Get Your FREE Groq API Key (2 minutes)

1. Go to: **https://console.groq.com/**
2. Sign up (Google login works!)
3. Click **"API Keys"** → **"Create API Key"**
4. Copy your key (starts with `gsk_...`)

---

## 📝 Update Your `.env` File

Open `src/.env` and paste this:

```bash
# Required
SECRET=somethingsomethingedosomething
EMAIL=23f3003728@ds.study.iitm.ac.in

# Audio Transcription (NEW!)
GROQ_API_KEY=gsk_paste_your_actual_groq_key_here

# Text Parsing
GEMINI_API_KEY=AIzaSyC_A2KraQkIue9wWAP2_Gd24BsIQ9g8O-0

# Server
HOST=0.0.0.0
PORT=8000
```

**Replace `gsk_paste_your_actual_groq_key_here` with your real key!**

---

## 🧪 Test It

### 1. Restart Server (in WSL):
```bash
# Press Ctrl+C to stop current server
python src/api/endpoint.py
```

### 2. Run Test (in another terminal):
```bash
curl -X POST http://localhost:8000/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "23f3003728@ds.study.iitm.ac.in",
    "secret": "somethingsomethingedosomething",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
```

### 3. Check Logs - Should See:
```
✅ "Sending audio.opus (audio/opus) to Groq Whisper API"
✅ "Transcribed using Groq Whisper API"
✅ "Answer correct!"
✅ "Quiz processing completed"
```

---

## 🚫 Should NOT See:
- ❌ "400 Bad Request"
- ❌ "aipipe/OpenAI API transcription failed"
- ❌ "Transcribed using local Whisper model" (unless Groq key is missing)

---

## 🚀 Deploy Later

When ready to deploy (Render, Railway, Fly.io, etc.):

1. Set environment variable: `GROQ_API_KEY=your_key`
2. No other changes needed!
3. Fast, cloud-based transcription ⚡

---

## 📚 More Info

- **Full setup guide:** `GROQ_SETUP.md`
- **Why we switched:** `AIPIPE_INVESTIGATION_SUMMARY.md`
- **All changes:** `CHANGES_SUMMARY.md`

---

## 💡 TL;DR

1. Get Groq API key: https://console.groq.com/
2. Add to `src/.env`: `GROQ_API_KEY=gsk_...`
3. Restart server & test
4. Done! 🎉
