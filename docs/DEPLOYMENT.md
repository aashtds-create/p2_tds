# 🚀 Deployment Guide: Railway.app

## Why Railway (Not Vercel)?

| Feature | Vercel | Railway |
|---------|--------|---------|
| Timeout | 10s (free) / 30s (pro) | Unlimited |
| Playwright | ❌ Not supported | ✅ Works |
| Docker | ❌ Limited | ✅ Full support |
| Background tasks | ❌ Stateless | ✅ Persistent |
| Free tier | Limited | $5/month credit |

---

## 📋 **Quick Deployment (5 minutes)**

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub (recommended)
3. Verify your account

### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Connect your GitHub account (if not already)
4. Select your repository

### Step 3: Configure Environment Variables

In Railway dashboard:
1. Click on your service
2. Go to **"Variables"** tab
3. Add these variables:

```
GEMINI_API_KEY=your_gemini_api_key_here
SECRET=your_secret_here
EMAIL=your_email@example.com
```

### Step 4: Deploy!

Railway auto-deploys on push. Just push your code:

```bash
git add .
git commit -m "Add Railway deployment"
git push origin main
```

### Step 5: Get Your URL

1. Go to Railway dashboard
2. Click **"Settings"**
3. Under **"Domains"**, click **"Generate Domain"**
4. Your URL: `https://your-app.up.railway.app`

---

## 🧪 **Testing Your Deployment**

### Test Health Endpoint

```bash
curl https://your-app.up.railway.app/health
```

Expected response:
```json
{"status": "healthy"}
```

### Test Quiz Endpoint

```bash
curl -X POST https://your-app.up.railway.app/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "secret": "your_secret",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
```

Expected response:
```json
{"status": "accepted", "message": "Quiz task received and processing started"}
```

---

## 🔧 **Railway Dashboard Features**

### Logs (Most Important!)

1. Click your service
2. Go to **"Logs"** tab
3. Watch real-time processing

### Metrics

- CPU usage
- Memory usage
- Network I/O

### Variables

- Securely store API keys
- Changes trigger redeploy

### Domains

- Get free `*.up.railway.app` domain
- Or add custom domain

---

## 📊 **Resource Estimates**

| Resource | Usage | Railway Free Tier |
|----------|-------|-------------------|
| Memory | ~512MB peak | 512MB included |
| CPU | Low (spikes during processing) | Shared CPU |
| Build time | ~3-5 minutes | 500 hours/month |
| Execution | ~40-50s per quiz | No timeout |

**Cost estimate:** $0-3/month with light usage (free tier covers most cases)

---

## 🐛 **Troubleshooting**

### Build Fails

**Check Docker logs:**
1. Go to Railway dashboard
2. Click "Build Logs"
3. Look for error messages

**Common issues:**
- Missing dependency → Add to `requirements.txt`
- Playwright install failed → Check Dockerfile

### Runtime Errors

**Check application logs:**
1. Go to "Logs" tab
2. Filter by error level
3. Look for stack traces

**Common issues:**
- Missing env var → Add in Variables tab
- API key invalid → Check GEMINI_API_KEY
- Timeout → Check network/Gemini API status

### Container Won't Start

**Check:**
1. Port configuration (`$PORT` env var)
2. Health check passing
3. Start command correct

---

## 🔄 **CI/CD: Auto-Deploy on Push**

Railway automatically deploys when you push to main branch:

```bash
# Make changes
git add .
git commit -m "Update something"
git push origin main

# Railway detects push → rebuilds → deploys
# ~3-5 minutes for new version to be live
```

---

## 🌐 **Custom Domain (Optional)**

### Step 1: Add Domain in Railway

1. Go to Settings → Domains
2. Click "Add Custom Domain"
3. Enter: `quiz-solver.yourdomain.com`

### Step 2: Update DNS

Add CNAME record:
```
quiz-solver.yourdomain.com → your-app.up.railway.app
```

### Step 3: Wait for SSL

Railway auto-provisions SSL certificate (5-10 minutes)

---

## 📝 **Files Created for Deployment**

```
project/
├── Dockerfile          ← Container configuration
├── railway.json        ← Railway-specific settings
├── .dockerignore       ← Files to exclude from container
└── requirements.txt    ← Python dependencies
```

---

## 🎯 **Post-Deployment Checklist**

- [ ] Health endpoint returns 200
- [ ] Quiz endpoint accepts requests
- [ ] Logs show processing activity
- [ ] Demo quiz passes
- [ ] Environment variables set correctly
- [ ] No error logs in dashboard

---

## 💡 **Tips**

### Keep Logs Clean
```python
# Use appropriate log levels
logger.info("Normal operation")
logger.warning("Something to watch")
logger.error("Something failed")
```

### Monitor Costs
- Check Railway dashboard weekly
- Free tier: $5 credit/month
- Most light usage stays free

### Debugging Production
```bash
# Test locally with same env vars
export GEMINI_API_KEY=xxx
export SECRET=xxx
export EMAIL=xxx
python -m uvicorn src.api.endpoint:app --port 8000
```

---

## 🚀 **Alternative Platforms**

If Railway doesn't work for you:

| Platform | Pros | Cons |
|----------|------|------|
| **Render.com** | Free tier, easy | Slower cold starts |
| **Fly.io** | Fast, global | More complex setup |
| **Google Cloud Run** | Scalable | Requires GCP account |
| **DigitalOcean Apps** | Simple | $5/month minimum |

---

## 📞 **Need Help?**

1. Check Railway docs: [docs.railway.app](https://docs.railway.app)
2. Check build/deploy logs
3. Test locally first
4. Verify environment variables

---

**Happy deploying! 🎉**

