# 🚀 BioIntel.AI Deployment Guide

Complete deployment guide for BioIntel.AI platform across different environments and platforms.

## 🏗️ Deployment Options

### 1. Docker Compose (Recommended)
### 2. Vercel (Frontend + Serverless Backend)
### 3. Heroku (Full Stack)
### 4. AWS/GCP (Production Scale)
### 5. Manual Deployment

---

## 🐳 Docker Compose Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### Quick Start
```bash
# Clone repository
git clone https://github.com/your-org/biointel-ai.git
cd biointel-ai

# Deploy with default settings
./docker-deploy.sh

# Deploy in production mode
./docker-deploy.sh -e production --rebuild
```

### Environment Configuration
```bash
# Create .env file
cp .env.example .env

# Edit environment variables
nano .env
```

Required environment variables:
```env
# Database
DATABASE_URL=postgresql://biointel:biointel@db:5432/biointel_db

# Security
SECRET_KEY=your-super-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this

# AI APIs
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key

# Redis
REDIS_URL=redis://redis:6379/0

# Optional
SENTRY_DSN=your-sentry-dsn
```

### Service Scaling
```bash
# Scale API instances
./docker-deploy.sh --scale-api 3

# Scale frontend instances
./docker-deploy.sh --scale-frontend 2

# Scale both
./docker-deploy.sh --scale-api 3 --scale-frontend 2
```

### Monitoring
```bash
# View service status
docker-compose ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f db
```

---

## ▲ Vercel Deployment

### Prerequisites
- Vercel account
- Vercel CLI installed
- PostgreSQL database (external)
- Redis instance (external)

### Setup
```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
./deploy.sh -p vercel -e production
```

### Environment Variables Setup
```bash
# Set environment variables in Vercel
vercel env add DATABASE_URL
vercel env add SECRET_KEY
vercel env add JWT_SECRET_KEY
vercel env add ANTHROPIC_API_KEY
vercel env add OPENAI_API_KEY
vercel env add REDIS_URL
```

### Custom Domain Setup
```bash
# Add domain
vercel domains add yourdomain.com

# Add SSL certificate (automatic)
vercel certs add yourdomain.com
```

---

## 🟣 Heroku Deployment

### Prerequisites
- Heroku account
- Heroku CLI installed
- Git repository

### Setup
```bash
# Install Heroku CLI
brew install heroku/brew/heroku

# Login to Heroku
heroku login

# Deploy
./deploy.sh -p heroku -e production
```

### Add-ons Setup
```bash
# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis
heroku addons:create heroku-redis:hobby-dev

# Add monitoring
heroku addons:create papertrail:choklad
```

### Environment Variables
```bash
# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set JWT_SECRET_KEY=your-jwt-secret
heroku config:set ANTHROPIC_API_KEY=your-anthropic-key
heroku config:set OPENAI_API_KEY=your-openai-key
```

---

## ☁️ AWS/GCP Production Deployment

### AWS ECS Deployment
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t biointel-ai .

# Tag and push
docker tag biointel-ai:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/biointel-ai:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/biointel-ai:latest

# Deploy to ECS
aws ecs update-service --cluster biointel-cluster --service biointel-service --force-new-deployment
```

### GCP Cloud Run Deployment
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/your-project/biointel-ai

# Deploy to Cloud Run
gcloud run deploy biointel-ai \
    --image gcr.io/your-project/biointel-ai \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

---

## 🔧 Manual Deployment

### Prerequisites
- Ubuntu 20.04+ or CentOS 8+
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Nginx

### System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib redis-server nginx

# Create user
sudo useradd -m -s /bin/bash biointel
sudo usermod -aG sudo biointel
```

### Database Setup
```bash
# Create database
sudo -u postgres createdb biointel_db
sudo -u postgres createuser biointel
sudo -u postgres psql -c "ALTER USER biointel WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE biointel_db TO biointel;"

# Run initialization script
sudo -u postgres psql biointel_db < init.sql
```

### Application Setup
```bash
# Switch to biointel user
sudo su - biointel

# Clone repository
git clone https://github.com/your-org/biointel-ai.git
cd biointel-ai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Create systemd service
sudo tee /etc/systemd/system/biointel-api.service > /dev/null <<EOF
[Unit]
Description=BioIntel.AI API
After=network.target

[Service]
Type=simple
User=biointel
WorkingDirectory=/home/biointel/biointel-ai
Environment=PATH=/home/biointel/biointel-ai/venv/bin
ExecStart=/home/biointel/biointel-ai/venv/bin/gunicorn api.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable biointel-api
sudo systemctl start biointel-api
```

### Nginx Configuration
```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/biointel-ai > /dev/null <<EOF
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/biointel-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Setup with Let's Encrypt
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

---

## 🔍 Health Checks & Monitoring

### Health Check Endpoints
```bash
# API health check
curl http://localhost:8000/health

# Database health check
curl http://localhost:8000/health/db

# Redis health check
curl http://localhost:8000/health/redis
```

### Monitoring Setup
```bash
# Install monitoring tools
pip install sentry-sdk prometheus-client

# Configure Sentry (add to .env)
SENTRY_DSN=your-sentry-dsn

# Prometheus metrics endpoint
curl http://localhost:8000/metrics
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connection
psql -h localhost -U biointel -d biointel_db

# Reset database
sudo -u postgres psql -c "DROP DATABASE biointel_db;"
sudo -u postgres psql -c "CREATE DATABASE biointel_db;"
```

#### 2. Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis

# Test Redis connection
redis-cli ping

# Restart Redis
sudo systemctl restart redis
```

#### 3. Permission Issues
```bash
# Fix file permissions
sudo chown -R biointel:biointel /home/biointel/biointel-ai
sudo chmod +x deploy.sh docker-deploy.sh run_tests.sh
```

#### 4. Memory Issues
```bash
# Check memory usage
free -h

# Increase swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Log Locations
```bash
# Application logs
tail -f logs/biointel.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# System logs
journalctl -u biointel-api -f
```

---

## 📊 Performance Optimization

### Database Optimization
```sql
-- Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_datasets_user_id ON datasets(user_id);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM datasets WHERE user_id = 1;
```

### Redis Optimization
```bash
# Redis configuration
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Application Optimization
```bash
# Use multiple workers
gunicorn api.main:app -k uvicorn.workers.UvicornWorker -w 4

# Enable async processing
pip install celery
celery -A services.celery worker --loglevel=info
```

---

## 🔒 Security Checklist

### SSL/TLS
- [ ] SSL certificate installed
- [ ] HTTP to HTTPS redirect
- [ ] Strong cipher suites
- [ ] HSTS headers

### Application Security
- [ ] Environment variables secured
- [ ] API rate limiting enabled
- [ ] Input validation implemented
- [ ] CORS properly configured

### Infrastructure Security
- [ ] Firewall configured
- [ ] Database access restricted
- [ ] Redis access secured
- [ ] Regular security updates

---

## 📈 Scaling Considerations

### Horizontal Scaling
```bash
# Docker Compose scaling
docker-compose up --scale api=3 --scale frontend=2

# Kubernetes deployment
kubectl scale deployment biointel-api --replicas=3
```

### Vertical Scaling
```bash
# Increase container resources
docker run --memory=2g --cpus=2 biointel-ai

# Adjust worker processes
gunicorn api.main:app -w 8 -k uvicorn.workers.UvicornWorker
```

### Load Balancing
```nginx
upstream biointel_api {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    location / {
        proxy_pass http://biointel_api;
    }
}
```

---

## 🔄 Backup & Recovery

### Database Backup
```bash
# Create backup
pg_dump -U biointel -h localhost biointel_db > backup.sql

# Restore backup
psql -U biointel -h localhost biointel_db < backup.sql

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U biointel biointel_db > /backups/biointel_$DATE.sql
```

### File Backup
```bash
# Backup uploads and reports
tar -czf biointel_files_$(date +%Y%m%d).tar.gz uploads/ reports/

# Sync to cloud storage
aws s3 sync uploads/ s3://biointel-backups/uploads/
```

---

## 📞 Support

For deployment issues:
- 📧 Email: devops@biointel.ai
- 📖 Documentation: https://docs.biointel.ai/deployment
- 🐛 Issues: https://github.com/your-org/biointel-ai/issues

---

**Last Updated**: January 2024
**Version**: 1.0.0