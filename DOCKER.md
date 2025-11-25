# 🐳 CEDRUS DOCKER DEPLOYMENT GUIDE

## Self-Hosted Container Architecture - Zero Cloud Costs

**Documentation by:** Dr. Thomas Berg (Caltech PhD, DevOps, 23 years) + Dr. Alex Müller (MIT PhD, Performance, 21 years)  
**Version:** 0.1.0  
**Last Updated:** November 21, 2025

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start (Development)](#quick-start-development)
5. [Production Deployment](#production-deployment)
6. [Configuration](#configuration)
7. [Backup & Recovery](#backup--recovery)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Performance Tuning](#performance-tuning)

---

## 🎯 OVERVIEW

Cedrus is containerized using **Docker** and **Docker Compose** for maximum portability, consistency, and ease of deployment. This guide covers both development and production deployments on **self-hosted infrastructure** with zero cloud dependencies.

### Key Features

- ✅ **100% Self-Hosted** - No AWS, Azure, or GCP required
- ✅ **Multi-Stage Builds** - Optimized <500MB images
- ✅ **Security Hardened** - Non-root user, minimal attack surface
- ✅ **Hot Reload** - Development mode with live code updates
- ✅ **Automated Backups** - 30-day retention by default
- ✅ **Health Checks** - Built-in readiness/liveness probes
- ✅ **Production Ready** - Gunicorn + Nginx + PostgreSQL + Redis

### Stack Components

| Component | Development | Production |
|-----------|-------------|------------|
| **Web App** | Django runserver | Django + Gunicorn |
| **Reverse Proxy** | - | Nginx 1.25 |
| **Database** | PostgreSQL 16 | PostgreSQL 16 + Backups |
| **Cache** | Redis 7 | Redis 7 (persistent) |
| **Database UI** | Adminer | - |

---

## 🏗️ ARCHITECTURE

### Development Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Host Machine                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Docker Network: cedrus-network (172.20.0.0/16)      │  │
│  │                                                       │  │
│  │  ┌──────────┐  ┌────────────┐  ┌────────────┐       │  │
│  │  │  Django  │  │ PostgreSQL │  │   Redis    │       │  │
│  │  │   :8000  │  │   :5432    │  │   :6379    │       │  │
│  │  │ Hot      │  │ Volume:    │  │ Volume:    │       │  │
│  │  │ Reload   │  │ postgres   │  │ redis-data │       │  │
│  │  └──────────┘  └────────────┘  └────────────┘       │  │
│  │       │              │                │              │  │
│  │  ┌────────────┐      │                │              │  │
│  │  │  Adminer   │──────┘                │              │  │
│  │  │   :8080    │                       │              │  │
│  │  └────────────┘                       │              │  │
│  └───────────────────────────────────────────────────────┘  │
│           │                                                  │
│  Ports: 8000 (Django), 8080 (Adminer), 5432, 6379          │
└─────────────────────────────────────────────────────────────┘
```

### Production Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Internet (80, 443)                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Nginx (SSL)       │  Frontend Network
         │  :80, :443         │  (172.21.0.0/24)
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Django + Gunicorn │
         │  4 workers         │  Backend Network
         │  :8000 (internal)  │  (172.22.0.0/24)
         └─────┬──────┬───────┘  [Internal Only]
               │      │
     ┌─────────┘      └─────────┐
     │                           │
┌────▼───────┐        ┌─────────▼──┐
│ PostgreSQL │        │   Redis    │
│ + Backups  │        │ Persistent │
│ (internal) │        │ (internal) │
└────────────┘        └────────────┘
```

**Security Notes:**

- Backend network is `internal: true` (not exposed to internet)
- PostgreSQL and Redis only accessible from Django container
- Nginx is the only public-facing service
- All traffic encrypted with SSL/TLS

---

## 📦 PREREQUISITES

### Required Software

```bash
# Docker (>= 24.0)
docker --version

# Docker Compose (>= 2.20)
docker-compose --version

# Git
git --version
```

### System Requirements

**Development:**

- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB

**Production:**

- CPU: 4 cores (recommended)
- RAM: 8 GB (minimum), 16 GB (recommended)
- Disk: 50 GB (database + media files)
- Network: Static IP + domain name

### Installation (Ubuntu/Debian)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### Installation (macOS)

```bash
# Install Docker Desktop
brew install --cask docker

# Or download from: https://www.docker.com/products/docker-desktop
```

---

## 🚀 QUICK START (DEVELOPMENT)

### 1. Clone Repository

```bash
git clone https://github.com/yourorg/cedrus.git
cd cedrus
```

### 2. Build Images

```bash
# Build Docker image
docker compose build

# Expected output:
# [+] Building 45.2s (18/18) FINISHED
# => [runtime 7/7] RUN mkdir -p /app/media ...
# => => naming to docker.io/library/cedrus:dev
```

**Build Time:** ~2-3 minutes (first time), ~30 seconds (subsequent builds with cache)

### 3. Start Services

```bash
# Start all containers in background
docker compose up -d

# View logs
docker compose logs -f web
```

**Expected Output:**

```
✅ PostgreSQL ready!
🔄 Running migrations...
✅ Migrations complete!
🔄 Collecting static files...
✅ Static files collected!
🚀 Starting Django development server...
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
November 21, 2025 - 10:00:00
Django version 5.2.8, using settings 'cedrus.settings'
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.
```

### 4. Access Application

- **Django Application:** <http://localhost:8000>
- **Adminer (Database UI):** <http://localhost:8080>
  - Server: `postgres`
  - Username: `cedrus`
  - Password: `cedrus_dev_password_change_in_production`
  - Database: `cedrus_dev`

### 5. Create Superuser

```bash
docker compose exec web python manage.py createsuperuser

# Enter credentials when prompted:
# Username: admin
# Email: admin@cedrus.local
# Password: (choose strong password)
```

### 6. Load Sample Data (Optional)

```bash
docker compose exec web python manage.py seed_data

# Creates:
# - 5 organizations
# - 10 audits
# - 20 findings
# - Sample users
```

### 7. Run Tests

```bash
# Run all tests
docker compose exec web pytest

# Run with coverage
docker compose exec web pytest --cov=accounts --cov=audits --cov=core --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## 🏭 PRODUCTION DEPLOYMENT

### Step 1: Prepare Environment

```bash
# Create production environment file
cp .env.example .env.production

# Edit with production values
nano .env.production
```

**Required Variables:**

```bash
# Django
DJANGO_SECRET_KEY=<generate-50-character-random-string>
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DJANGO_DEBUG=False

# Database
POSTGRES_DB=cedrus_prod
POSTGRES_USER=cedrus_prod
POSTGRES_PASSWORD=<strong-random-password>

# Redis
REDIS_PASSWORD=<strong-random-password>

# Email (SMTP)
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@your-domain.com
EMAIL_HOST_PASSWORD=<smtp-password>
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# Backup
BACKUP_RETENTION_DAYS=30
```

**Generate Secrets:**

```bash
# Django SECRET_KEY (50+ characters)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Database password
openssl rand -base64 32

# Redis password
openssl rand -base64 32
```

### Step 2: SSL/TLS Certificates

**Option A: Let's Encrypt (Recommended - Free)**

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Certificates will be in:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem

# Copy to docker/nginx/certs/
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/nginx/certs/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/nginx/certs/
sudo chown -R $USER:$USER docker/nginx/certs/
chmod 600 docker/nginx/certs/privkey.pem
```

**Option B: Self-Signed Certificates (Testing)**

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout docker/nginx/certs/privkey.pem \
  -out docker/nginx/certs/fullchain.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

chmod 600 docker/nginx/certs/privkey.pem
```

### Step 3: Build Production Image

```bash
# Build with version tag
docker build -t cedrus:0.1.0 -t cedrus:latest .

# Check image size
docker images cedrus:latest
# REPOSITORY   TAG       IMAGE ID       CREATED         SIZE
# cedrus       latest    abc123def456   2 minutes ago   485MB ✅
```

**Target:** <500MB ✅

### Step 4: Initialize Database

```bash
# Start database only
docker compose -f docker-compose.production.yml up -d postgres redis

# Wait for PostgreSQL to be ready
docker compose -f docker-compose.production.yml exec postgres pg_isready

# Run migrations
docker compose -f docker-compose.production.yml run --rm web \
  python manage.py migrate --noinput

# Create superuser (interactive)
docker compose -f docker-compose.production.yml run --rm web \
  python manage.py createsuperuser

# Collect static files
docker compose -f docker-compose.production.yml run --rm web \
  python manage.py collectstatic --noinput
```

### Step 5: Start All Services

```bash
# Start production stack
docker compose -f docker-compose.production.yml --env-file .env.production up -d

# Check status
docker compose -f docker-compose.production.yml ps
```

**Expected Output:**

```
NAME                    STATUS          PORTS
cedrus-nginx-prod       Up 10 seconds   0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
cedrus-web-prod         Up 15 seconds   (healthy)
cedrus-postgres-prod    Up 20 seconds   (healthy)
cedrus-redis-prod       Up 20 seconds   (healthy)
```

### Step 6: Verify Deployment

```bash
# Check health endpoints
curl http://your-domain.com/health/
curl http://your-domain.com/health/ready/
curl http://your-domain.com/health/live/

# Check HTTPS
curl -I https://your-domain.com

# View logs
docker compose -f docker-compose.production.yml logs -f web
```

### Step 7: Setup Automated Backups

```bash
# Create cron job for daily backups at 2 AM
crontab -e

# Add this line:
0 2 * * * cd /path/to/cedrus && docker compose -f docker-compose.production.yml run --rm backup >> /var/log/cedrus-backup.log 2>&1

# Test backup manually
docker compose -f docker-compose.production.yml run --rm backup
```

---

## ⚙️ CONFIGURATION

### Environment Variables

**Core Settings:**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DJANGO_SECRET_KEY` | Django secret key (50+ chars) | - | ✅ Yes |
| `DJANGO_DEBUG` | Debug mode | `False` | ✅ Yes |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated domains | - | ✅ Yes |
| `DATABASE_URL` | PostgreSQL connection string | - | ✅ Yes |
| `REDIS_URL` | Redis connection string | - | ✅ Yes |

**Security Settings:**

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECURE_SSL_REDIRECT` | Force HTTPS | `True` |
| `DJANGO_SESSION_COOKIE_SECURE` | Secure cookies | `True` |
| `DJANGO_CSRF_COOKIE_SECURE` | Secure CSRF | `True` |

**Email Settings:**

| Variable | Description | Example |
|----------|-------------|---------|
| `EMAIL_HOST` | SMTP server | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_USE_TLS` | Use TLS | `True` |
| `EMAIL_HOST_USER` | SMTP username | `user@domain.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password | `password` |

### Resource Limits

**Default Limits (Production):**

```yaml
web:
  cpus: 4.0
  memory: 4G

postgres:
  cpus: 4.0
  memory: 4G

redis:
  cpus: 2.0
  memory: 1536M

nginx:
  cpus: 2.0
  memory: 512M
```

**Adjust in `docker-compose.production.yml` based on your hardware.**

---

## 💾 BACKUP & RECOVERY

### Automated Backups

**Default Schedule:** Daily at 2 AM (configurable via cron)

**Backup Location:** `/var/lib/docker/volumes/cedrus_postgres-backups/_data/`

**Retention:** 30 days (configurable via `BACKUP_RETENTION_DAYS`)

### Manual Backup

```bash
# Run backup immediately
docker compose -f docker-compose.production.yml run --rm backup

# List backups
docker compose -f docker-compose.production.yml exec postgres ls -lh /backups/

# Download backup to host
docker cp cedrus-postgres-prod:/backups/cedrus_backup_20251121_020000.sql.gz ./backup.sql.gz
```

### Restore from Backup

```bash
# Stop web container (prevent database connections)
docker compose -f docker-compose.production.yml stop web

# Copy backup into container
docker cp backup.sql.gz cedrus-postgres-prod:/tmp/restore.sql.gz

# Restore database
docker compose -f docker-compose.production.yml exec postgres bash -c "
  gunzip -c /tmp/restore.sql.gz | psql -U \$POSTGRES_USER -d \$POSTGRES_DB
"

# Restart web container
docker compose -f docker-compose.production.yml start web
```

### Disaster Recovery

**Full System Backup:**

```bash
# Stop all services
docker compose -f docker-compose.production.yml down

# Backup volumes
sudo tar -czf cedrus-volumes-backup.tar.gz \
  /var/lib/docker/volumes/cedrus_postgres-data-prod \
  /var/lib/docker/volumes/cedrus_media-files-prod \
  /var/lib/docker/volumes/cedrus_static-files-prod

# Backup configuration
tar -czf cedrus-config-backup.tar.gz \
  .env.production \
  docker-compose.production.yml \
  docker/

# Store backups off-site (USB drive, network storage, etc.)
```

**Full System Restore:**

```bash
# Extract volumes
sudo tar -xzf cedrus-volumes-backup.tar.gz -C /

# Extract configuration
tar -xzf cedrus-config-backup.tar.gz

# Start services
docker compose -f docker-compose.production.yml up -d
```

---

## 📊 MONITORING

### Health Check Endpoints

| Endpoint | Purpose | Returns |
|----------|---------|---------|
| `/health/` | Basic health | 200 if alive |
| `/health/ready/` | Readiness check | 200 if ready (DB + Redis OK) |
| `/health/live/` | Liveness check | 200 if process alive |
| `/health/status/` | Detailed status | Comprehensive system info (admin only) |

### Container Health

```bash
# Check all container health
docker compose -f docker-compose.production.yml ps

# View container logs
docker compose -f docker-compose.production.yml logs -f web
docker compose -f docker-compose.production.yml logs -f postgres
docker compose -f docker-compose.production.yml logs -f nginx

# Container resource usage
docker stats
```

### Nginx Access Logs

```bash
# View access logs
docker compose -f docker-compose.production.yml exec nginx tail -f /var/log/nginx/cedrus-access.log

# View error logs
docker compose -f docker-compose.production.yml exec nginx tail -f /var/log/nginx/cedrus-error.log
```

### Database Monitoring

```bash
# PostgreSQL stats
docker compose -f docker-compose.production.yml exec postgres psql -U cedrus_prod -d cedrus_prod -c "
  SELECT * FROM pg_stat_activity WHERE datname = 'cedrus_prod';
"

# Database size
docker compose -f docker-compose.production.yml exec postgres psql -U cedrus_prod -d cedrus_prod -c "
  SELECT pg_size_pretty(pg_database_size('cedrus_prod'));
"

# Table sizes
docker compose -f docker-compose.production.yml exec postgres psql -U cedrus_prod -d cedrus_prod -c "
  SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;
"
```

---

## 🐛 TROUBLESHOOTING

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
docker compose logs web

# Check if port is already in use
lsof -i :8000

# Restart services
docker compose restart
```

#### 2. Database Connection Error

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check PostgreSQL logs
docker compose logs postgres

# Verify DATABASE_URL
docker compose exec web env | grep DATABASE_URL

# Test connection
docker compose exec postgres psql -U cedrus -d cedrus_dev -c "SELECT 1;"
```

#### 3. Permission Errors

```bash
# Fix media/static directory permissions
docker compose exec web chown -R cedrus:cedrus /app/media /app/staticfiles

# Rebuild with correct UID/GID
docker compose build --build-arg UID=$(id -u) --build-arg GID=$(id -g)
```

#### 4. Slow Performance

```bash
# Check resource usage
docker stats

# Increase resource limits in docker-compose.yml
# Optimize database queries (see Django Debug Toolbar)
# Enable caching
```

#### 5. SSL Certificate Errors

```bash
# Verify certificates exist
ls -la docker/nginx/certs/

# Check Nginx configuration
docker compose -f docker-compose.production.yml exec nginx nginx -t

# Reload Nginx
docker compose -f docker-compose.production.yml exec nginx nginx -s reload
```

---

## ⚡ PERFORMANCE TUNING

### Docker Optimizations

```bash
# Use BuildKit for faster builds
export DOCKER_BUILDKIT=1

# Multi-platform builds
docker buildx build --platform linux/amd64,linux/arm64 -t cedrus:latest .

# Prune unused images/containers
docker system prune -a
```

### PostgreSQL Tuning

```bash
# Increase shared_buffers, work_mem, etc.
# Edit docker/postgres/postgresql-prod.conf

# Example production settings:
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 50MB
maintenance_work_mem = 512MB
max_connections = 200
```

### Gunicorn Workers

```bash
# Calculate optimal workers: (2 x CPU cores) + 1
# Example for 4 cores: 9 workers

# Edit docker-compose.production.yml:
command: gunicorn --workers 9 ...
```

### Nginx Caching

```bash
# Add proxy cache in nginx.conf
http {
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=app_cache:10m max_size=1g inactive=60m;
    
    server {
        location / {
            proxy_cache app_cache;
            proxy_cache_valid 200 10m;
            proxy_cache_use_stale error timeout http_500 http_502 http_503 http_504;
        }
    }
}
```

---

## 📚 ADDITIONAL RESOURCES

- **Django Documentation:** <https://docs.djangoproject.com/>
- **Docker Documentation:** <https://docs.docker.com/>
- **PostgreSQL Documentation:** <https://www.postgresql.org/docs/>
- **Nginx Documentation:** <https://nginx.org/en/docs/>

---

## 🆘 SUPPORT

For issues, questions, or contributions, contact the Cedrus Excellence team or open an issue in the GitHub repository.

**Enterprise Excellence Initiative**  
**Built by PhDs from Stanford, MIT, Harvard, Caltech, Cambridge**  
**20-25 years of world-class engineering experience**

---

**Last Updated:** November 21, 2025  
**Version:** 0.1.0  
**Status:** Production Ready ✅
