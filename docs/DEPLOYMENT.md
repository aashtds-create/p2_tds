# 🚀 Deployment Guide

## Quick Comparison

| Platform | Playwright | Timeout | Free Tier | Setup |
|----------|------------|---------|-----------|-------|
| **Railway** ⭐ | ✅ Works | ∞ | $5 credit | Easy |
| **Render** | ✅ Works | ∞ | 750 hrs/mo | Easy |
| **Fly.io** | ✅ Works | ∞ | $5 credit | Docker |
| **Vercel** | ❌ No | 10s/60s | Limited | Complex |

**Recommendation: Use Railway** - Best for this project!

---

## 🚂 Deploy on Railway (Recommended)

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. You get $5 free credit (enough for testing)

### Step 2: Deploy from GitHub

**Option A: From GitHub Repo**

1. Push your code to GitHub
2. In Railway Dashboard: **New Project → Deploy from GitHub repo**
3. Select your repository
4. Railway auto-detects Dockerfile

**Option B: From CLI**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize and deploy
railway init
railway up
```

### Step 3: Configure Environment Variables

In Railway Dashboard → Your Project → Variables:

```
GEMINI_API_KEY=your_key_here
SECRET=your_secret_here
EMAIL=your_email@ds.study.iitm.ac.in
```

### Step 4: Get Your URL

Railway gives you a URL like:
```
https://your-project-name.up.railway.app
```

### Step 5: Test It!

```bash
curl -X POST https://your-project.up.railway.app/quiz \
  -H "Content-Type: application/json" \
  -d '{"email": "your_email", "secret": "your_secret", "url": "https://tds-llm-analysis.s-anand.net/demo"}'
```

---

## 🎨 Deploy on Render (Alternative)

### Step 1: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub

### Step 2: Create Web Service

1. **New → Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name**: quiz-solver
   - **Runtime**: Docker
   - **Plan**: Free

### Step 3: Add Environment Variables

In Render Dashboard → Environment:

```
GEMINI_API_KEY=your_key
SECRET=your_secret
EMAIL=your_email@ds.study.iitm.ac.in
```

### Step 4: Deploy

Click "Create Web Service" - it auto-deploys!

---

## 🐳 Deploy with Docker (Any Platform)

### Build Locally

```bash
# Build image
docker build -t quiz-solver .

# Run locally
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e SECRET=your_secret \
  -e EMAIL=your_email \
  quiz-solver
```

### Push to Docker Hub

```bash
docker tag quiz-solver your-dockerhub-username/quiz-solver
docker push your-dockerhub-username/quiz-solver
```

Then deploy to any Docker-compatible platform!

---

## ⚠️ Why Not Vercel?

Vercel is great for static sites and simple APIs, but has limitations for this project:

| Issue | Vercel | Our Needs |
|-------|--------|-----------|
| **Playwright** | ❌ Not supported | ✅ Required for JS rendering |
| **Timeout** | 10s free / 60s pro | 40+ seconds needed |
| **Package Size** | 50MB limit | Chromium is ~400MB |
| **Long-running** | ❌ Serverless only | ✅ Need background tasks |

**Bottom line:** Vercel is optimized for frontend, not browser automation.

---

## 🔧 Troubleshooting

### Railway: "Build Failed"

1. Check Dockerfile syntax
2. Ensure all files are committed to Git
3. Check Railway logs for specific error

### Render: "Service is unhealthy"

1. Check if `/health` endpoint returns 200
2. Verify environment variables are set
3. Check application logs

### Playwright Not Working

1. Ensure using official Playwright Docker image
2. Check browser installation: `playwright install chromium`
3. Verify headless mode is enabled

### Environment Variables Not Loading

1. In Railway: Set in Dashboard → Variables
2. In Render: Set in Dashboard → Environment
3. Don't commit `.env` file to Git!

---

## 📊 Monitoring

### Railway

- Built-in logs: Dashboard → Logs
- Metrics: Dashboard → Metrics

### Render

- Logs: Dashboard → Logs
- Metrics: Dashboard → Metrics

### Add Health Checks

Your app already has `/health` endpoint:
```bash
curl https://your-app.up.railway.app/health
# {"status": "healthy"}
```

---

## 💰 Cost Estimate

### Railway
- **Free**: $5 credit/month
- **Usage**: ~$0.01/hour for small instance
- **For testing**: Free tier is sufficient

### Render
- **Free**: 750 hours/month
- **Sleep**: Spins down after 15 min inactivity
- **For testing**: Free tier works

### Fly.io
- **Free**: $5 credit
- **Usage**: ~$2/month for small instance

---

## 🎯 Quick Start: Railway

```bash
# 1. Install CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Deploy (from project directory)
railway init
railway up

# 4. Set environment variables
railway variables set GEMINI_API_KEY=your_key
railway variables set SECRET=your_secret
railway variables set EMAIL=your_email

# 5. Get URL
railway open

# 6. Test
curl -X POST https://your-app.up.railway.app/quiz \
  -H "Content-Type: application/json" \
  -d '{"email": "your_email", "secret": "your_secret", "url": "https://tds-llm-analysis.s-anand.net/demo"}'
```

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] `.env` NOT in repository
- [ ] Dockerfile tested locally
- [ ] Railway/Render account created
- [ ] Environment variables set
- [ ] `/health` endpoint working
- [ ] `/quiz` endpoint tested
- [ ] Demo quiz passes

---

**Need help?** Check Railway/Render documentation or open an issue!

