# CheckMeasureAI Deployment Guide

## Quick Deployment Steps

### 1. Frontend Deployment (Vercel) - FREE

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Build and Deploy**:
   ```bash
   cd frontend
   npm run build
   vercel --prod
   ```

3. **Follow prompts**:
   - Login/Create Vercel account
   - Confirm project settings
   - Get your URL: `https://checkmeasure-ai.vercel.app`

### 2. Backend Deployment (Railway) - ~$5/month

1. **Create Railway Account**: https://railway.app

2. **Prepare Backend**:
   ```bash
   cd backend
   # Create requirements.txt if not exists
   pip freeze > requirements.txt
   ```

3. **Create Procfile**:
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Deploy via Railway CLI**:
   ```bash
   npm i -g @railway/cli
   railway login
   railway init
   railway up
   ```

5. **Set Environment Variables in Railway**:
   - `ANTHROPIC_API_KEY` (if using Claude)
   - Any other API keys

6. **Get your backend URL**: `https://checkmeasure-api.railway.app`

### 3. Update Frontend API URL

1. **Create .env.production**:
   ```
   REACT_APP_API_URL=https://checkmeasure-api.railway.app
   ```

2. **Rebuild and Redeploy**:
   ```bash
   npm run build
   vercel --prod
   ```

## Sharing Your App

Once deployed, share this link with friends:
```
https://checkmeasure-ai.vercel.app
```

They can:
1. Visit the link on their phone
2. Use the app in browser
3. Install it as a PWA:
   - Android: Menu → "Install app"
   - iOS: Share → "Add to Home Screen"

## Alternative Free Options

### Frontend:
- **Netlify**: `netlify deploy`
- **GitHub Pages**: Push to gh-pages branch
- **Cloudflare Pages**: Connect GitHub repo

### Backend:
- **Render**: Free tier with spin-down
- **Fly.io**: Free tier available
- **Heroku**: Free tier (limited)

## Custom Domain (Optional)

1. Buy domain (e.g., checkmeasureai.com)
2. Add to Vercel: Project Settings → Domains
3. Update DNS records
4. Enable HTTPS (automatic)

## Monitoring

- **Frontend**: Vercel Analytics (free)
- **Backend**: Railway Metrics
- **Errors**: Sentry (free tier)

## Cost Summary

- **Frontend**: FREE (Vercel/Netlify)
- **Backend**: ~$5-20/month (Railway/Render)
- **Domain**: ~$12/year (optional)
- **Total**: ~$5-20/month

Your app will be accessible worldwide, installable on phones, and work offline!