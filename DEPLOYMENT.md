# Deployment Guide for CheckMeasureAI

This guide provides instructions for deploying CheckMeasureAI to various platforms.

## 🚀 Deployment Options

### Option 1: Vercel (Recommended for Quick Demo)

Vercel provides easy deployment for both frontend and backend:

1. **Fork/Clone the Repository**
   - Ensure your code is pushed to GitHub

2. **Import to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "Import Project"
   - Select your GitHub repository
   - Vercel will auto-detect the configuration

3. **Environment Variables**
   - Add any required environment variables in Vercel dashboard
   - No special configuration needed for basic deployment

4. **Deploy**
   - Click "Deploy"
   - Your app will be live at `https://your-app.vercel.app`

### Option 2: Railway (Full-Stack Deployment)

Railway is excellent for deploying both frontend and backend together:

1. **Create Railway Account**
   - Sign up at [railway.app](https://railway.app)

2. **New Project from GitHub**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Services**
   - Railway will auto-detect the services
   - It will create separate services for frontend and backend

4. **Environment Variables**
   - Add any required environment variables
   - Railway provides a PostgreSQL database if needed

### Option 3: Docker Deployment (AWS/GCP/Azure)

For production deployment using Docker:

1. **Build Docker Images**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
   ```

2. **Push to Container Registry**
   ```bash
   # Tag images
   docker tag checkmeasure-ai-backend:latest your-registry/checkmeasure-backend:latest
   docker tag checkmeasure-ai-frontend:latest your-registry/checkmeasure-frontend:latest
   
   # Push images
   docker push your-registry/checkmeasure-backend:latest
   docker push your-registry/checkmeasure-frontend:latest
   ```

3. **Deploy to Cloud Provider**
   - Use your cloud provider's container service
   - Configure load balancers and SSL certificates

### Option 4: Render (Simple Full-Stack)

1. **Create Render Account**
   - Sign up at [render.com](https://render.com)

2. **Create Web Services**
   - Create a new "Web Service" for backend
   - Create a "Static Site" for frontend

3. **Configure Build Commands**
   - Backend: `cd backend && pip install -r requirements.txt`
   - Frontend: `cd frontend && npm install && npm run build`

4. **Configure Start Commands**
   - Backend: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Frontend: Serve from `frontend/build`

## 📋 Pre-Deployment Checklist

- [ ] Update environment variables
- [ ] Test locally with production build
- [ ] Verify all API endpoints work
- [ ] Check CORS settings for production URL
- [ ] Update frontend API URL for production
- [ ] Test PDF upload functionality
- [ ] Verify Docker images build correctly

## 🔧 Environment Variables

Create a `.env.production` file:

```env
# Backend
PYTHONPATH=/app/backend
ENVIRONMENT=production
LOG_LEVEL=info

# Frontend (if needed)
REACT_APP_API_URL=https://your-backend-url.com
```

## 🌐 Domain Configuration

1. **Purchase Domain** (if needed)
2. **Configure DNS**
   - Point domain to your deployment platform
   - Set up SSL certificates (usually automatic)

## 📊 Monitoring

Set up monitoring for production:

1. **Application Monitoring**
   - Error tracking (Sentry)
   - Performance monitoring
   - Uptime monitoring

2. **Logging**
   - Centralized logging
   - Error alerts

## 🔒 Security Considerations

1. **Environment Variables**
   - Never commit secrets to git
   - Use platform's secret management

2. **CORS Configuration**
   - Update allowed origins for production

3. **Rate Limiting**
   - Implement API rate limiting

4. **SSL/HTTPS**
   - Ensure all traffic is encrypted

## 📞 Support

If you encounter issues during deployment:
1. Check the deployment logs
2. Verify environment variables
3. Test API endpoints independently
4. Open an issue on GitHub

---

For quick demo deployment, Vercel or Railway are recommended. For production use, consider Docker deployment on a major cloud provider.