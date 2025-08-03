# Deployment Guide

This guide covers deploying CheckMeasureAI to production environments, from simple cloud hosting to enterprise-grade infrastructure.

## Quick Deployment Options

### Option 1: Frontend Only (Static Demo)
**Best for**: Showcasing the UI without backend functionality
**Cost**: Free
**Time**: 5 minutes

Deploy just the frontend to demonstrate the interface:

1. **Build the frontend**:
```bash
cd frontend
npm run build
```

2. **Deploy to Vercel** (recommended):
```bash
npm install -g vercel
vercel --prod
```

3. **Alternative platforms**:
   - **Netlify**: `netlify deploy --prod --dir=build`
   - **GitHub Pages**: Push to `gh-pages` branch
   - **Surge**: `surge build/`

### Option 2: Full Application (Frontend + Backend)
**Best for**: Complete functionality
**Cost**: $5-20/month
**Time**: 15-30 minutes

## Production Deployment

### Frontend Deployment

#### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Build and deploy
cd frontend
npm run build
vercel --prod
```

**Configuration** (`vercel.json`):
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "env": {
    "REACT_APP_API_URL": "https://your-backend-url.com"
  }
}
```

#### Netlify
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Build and deploy
cd frontend
npm run build
netlify deploy --prod --dir=build
```

#### Traditional Hosting
For Apache/Nginx servers:
```bash
cd frontend
npm run build
# Upload build/ contents to web server
```

### Backend Deployment

#### Railway (Recommended for Simplicity)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy from backend directory
cd backend
railway login
railway init
railway up
```

**Required files**:
- `requirements.txt` (already exists)
- `Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### Render
1. Connect GitHub repository
2. Select backend folder
3. Configure build command: `pip install -r requirements.txt`
4. Configure start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### DigitalOcean App Platform
```yaml
name: checkmeasure-ai
services:
- name: backend
  source_dir: /backend
  github:
    repo: yourusername/checkmeasure-ai
    branch: main
  run_command: uvicorn main:app --host 0.0.0.0 --port $PORT
  environment_slug: python
```

### Docker Deployment

#### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - CORS_ORIGINS=["http://localhost:3000"]
    
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - backend
```

## Environment Configuration

### Backend Environment Variables
```env
# API Configuration
CORS_ORIGINS=["https://your-frontend-domain.com"]
API_HOST=0.0.0.0
API_PORT=8000

# AI Services (Optional)
ANTHROPIC_API_KEY=your_claude_api_key

# Database (Future)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Redis (Future)
REDIS_URL=redis://host:port

# Monitoring
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=INFO
```

### Frontend Environment Variables
```env
# Production
REACT_APP_API_URL=https://your-backend-domain.com
PUBLIC_URL=https://your-frontend-domain.com

# Development
REACT_APP_API_URL=http://localhost:8000
```

## SSL/HTTPS Configuration

### Using Let's Encrypt (Free SSL)
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Cloudflare (Recommended)
1. Add your domain to Cloudflare
2. Update nameservers
3. Enable "Always Use HTTPS"
4. Configure SSL/TLS to "Full (strict)"

## Database Setup (Future Enhancement)

### PostgreSQL
```bash
# Create database
createdb checkmeasure_ai

# Run migrations (when implemented)
cd backend
python manage.py migrate
```

### MongoDB (Alternative)
```bash
# Start MongoDB
mongod --dbpath /data/db

# Configure connection
MONGODB_URL=mongodb://localhost:27017/checkmeasure_ai
```

## Monitoring and Logging

### Application Monitoring
```python
# Add to main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
)
```

### Server Monitoring
```bash
# Install monitoring tools
sudo apt-get install htop iotop

# Setup log rotation
sudo nano /etc/logrotate.d/checkmeasure-ai
```

### Health Checks
```python
# Health check endpoint (already implemented)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

## Performance Optimization

### Frontend Optimization
```json
// package.json - Add build optimization
{
  "scripts": {
    "build": "react-scripts build && npm run optimize",
    "optimize": "npx webpack-bundle-analyzer build/static/js/*.js"
  }
}
```

### Backend Optimization
```python
# Add caching
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(params):
    # Cached calculation
    pass
```

### CDN Configuration
```javascript
// CloudFront/CDN settings
{
  "origin": "your-app.vercel.app",
  "cacheBehaviors": {
    "/static/*": { "ttl": 31536000 },  // 1 year
    "/api/*": { "ttl": 0 }             // No cache
  }
}
```

## Security Hardening

### CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/calculations/joists")
@limiter.limit("10/minute")
async def calculate_joists(request: Request, data: JoistRequest):
    # Rate limited endpoint
    pass
```

### Input Validation
```python
# Already implemented with Pydantic
class JoistCalculationRequest(BaseModel):
    span_length: float = Field(gt=0, le=20, description="Span in meters")
    joist_spacing: float = Field(gt=0, le=2, description="Spacing in meters")
    # Validation is automatic
```

## Backup and Recovery

### Data Backup
```bash
# Database backup (when implemented)
pg_dump checkmeasure_ai > backup_$(date +%Y%m%d).sql

# File backup
tar -czf files_backup_$(date +%Y%m%d).tar.gz uploads/
```

### Disaster Recovery
1. **Code**: Version controlled on GitHub
2. **Database**: Automated daily backups
3. **Files**: S3/cloud storage with versioning
4. **Configuration**: Infrastructure as Code

## Scaling Considerations

### Horizontal Scaling
```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkmeasure-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: checkmeasure-backend
  template:
    metadata:
      labels:
        app: checkmeasure-backend
    spec:
      containers:
      - name: backend
        image: checkmeasure-ai:latest
        ports:
        - containerPort: 8000
```

### Load Balancing
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
    }
}
```

## Troubleshooting

### Common Issues

#### CORS Errors
```python
# Fix: Update CORS origins
CORS_ORIGINS=["https://your-actual-domain.com"]
```

#### Memory Issues
```bash
# Monitor memory usage
free -h
htop

# Increase server memory or optimize code
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew
```

### Debugging Tools
```bash
# Check application logs
journalctl -u your-app-service -f

# Test API endpoints
curl -X GET https://your-api.com/health

# Monitor performance
htop
iotop
```

## Cost Optimization

### Free Tier Options
- **Frontend**: Vercel, Netlify (free tier)
- **Backend**: Railway (free tier), Render (free tier)
- **Database**: PlanetScale, Supabase (free tier)
- **Monitoring**: Sentry (free tier)

### Estimated Monthly Costs
- **Hobby**: $0-10/month
- **Professional**: $20-50/month
- **Enterprise**: $100+/month

## Support and Maintenance

### Regular Tasks
1. **Security Updates**: Monthly dependency updates
2. **Performance Monitoring**: Weekly performance reviews
3. **Backup Verification**: Monthly backup tests
4. **SSL Renewal**: Automated with Let's Encrypt

### Emergency Procedures
1. **Service Down**: Check logs, restart services
2. **High Load**: Scale up resources
3. **Security Incident**: Rotate keys, audit logs
4. **Data Loss**: Restore from backups