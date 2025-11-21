# Cedrus Deployment Guide

This guide covers production deployment of the Cedrus platform.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Production Settings](#production-settings)
- [Database Setup](#database-setup)
- [Static Files Configuration](#static-files-configuration)
- [Media Files Configuration](#media-files-configuration)
- [Web Server Configuration](#web-server-configuration)
- [Security Considerations](#security-considerations)
- [Backup Strategy](#backup-strategy)
- [Monitoring](#monitoring)

---

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Python 3.8+
- PostgreSQL 12+ (recommended) or MySQL 8+
- Nginx or Apache
- SSL certificate (Let's Encrypt recommended)

---

## Production Settings

### Environment Variables

Create a `.env` file or use environment variables:

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost/cedrus
```

### Settings Configuration

Update `cedrus/settings.py` for production:

```python
import os
from pathlib import Path

# Security
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'cedrus'),
        'USER': os.environ.get('DB_USER', 'cedrus'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Static files
STATIC_ROOT = '/var/www/cedrus/staticfiles'
MEDIA_ROOT = '/var/www/cedrus/media'

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

---

## Database Setup

### PostgreSQL Installation

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### Create Database and User

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE cedrus;
CREATE USER cedrus_user WITH PASSWORD 'secure_password';
ALTER ROLE cedrus_user SET client_encoding TO 'utf8';
ALTER ROLE cedrus_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE cedrus_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE cedrus TO cedrus_user;
\q
```

### Run Migrations

```bash
python manage.py migrate
```

---

## Static Files Configuration

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Option 1: WhiteNoise (Recommended for Simple Deployments)

Install WhiteNoise:

```bash
pip install whitenoise
```

Add to `settings.py`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    # ... other middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Option 2: Nginx (Recommended for Production)

Configure Nginx to serve static files (see Web Server Configuration below).

---

## Media Files Configuration

### Local Storage

Ensure media directory exists and is writable:

```bash
mkdir -p /var/www/cedrus/media
chown -R www-data:www-data /var/www/cedrus/media
chmod -R 755 /var/www/cedrus/media
```

### Cloud Storage (Recommended for Production)

Configure cloud storage (AWS S3, Azure Blob, etc.) using `django-storages`:

```bash
pip install django-storages boto3
```

Update `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'storages',
]

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

---

## Web Server Configuration

### Gunicorn Setup

Install Gunicorn:

```bash
pip install gunicorn
```

Create Gunicorn service file `/etc/systemd/system/cedrus.service`:

```ini
[Unit]
Description=Cedrus Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/cedrus
ExecStart=/var/www/cedrus/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/cedrus/cedrus.sock \
    cedrus.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start service:

```bash
sudo systemctl start cedrus
sudo systemctl enable cedrus
```

### Nginx Configuration

Create `/etc/nginx/sites-available/cedrus`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Static files
    location /static/ {
        alias /var/www/cedrus/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/cedrus/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Django application
    location / {
        proxy_pass http://unix:/var/www/cedrus/cedrus.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/cedrus /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Security Considerations

### SSL/TLS

Use Let's Encrypt for free SSL certificates:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Firewall

Configure UFW:

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Django Security Settings

Ensure all security settings are enabled (see Production Settings above).

### Regular Updates

- Keep Django and dependencies updated
- Monitor security advisories
- Apply security patches promptly

---

## Backup Strategy

### Database Backups

Automated PostgreSQL backup script:

```bash
#!/bin/bash
# /usr/local/bin/backup-cedrus-db.sh

BACKUP_DIR="/var/backups/cedrus"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="cedrus_db_$DATE.sql"

mkdir -p $BACKUP_DIR
pg_dump -U cedrus_user cedrus > $BACKUP_DIR/$FILENAME

# Keep only last 30 days
find $BACKUP_DIR -name "cedrus_db_*.sql" -mtime +30 -delete
```

Add to crontab:

```bash
0 2 * * * /usr/local/bin/backup-cedrus-db.sh
```

### Media Files Backup

If using local storage, backup media directory:

```bash
tar -czf /var/backups/cedrus/media_$(date +%Y%m%d).tar.gz /var/www/cedrus/media
```

---

## Monitoring

### Application Monitoring

- Set up error tracking (Sentry recommended)
- Monitor server resources (CPU, memory, disk)
- Set up log aggregation

### Logging Configuration

Update `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/cedrus/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## Troubleshooting

### Check Gunicorn Status

```bash
sudo systemctl status cedrus
```

### Check Nginx Logs

```bash
sudo tail -f /var/log/nginx/error.log
```

### Check Application Logs

```bash
sudo tail -f /var/log/cedrus/django.log
```

### Restart Services

```bash
sudo systemctl restart cedrus
sudo systemctl restart nginx
```

---

## Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Gunicorn Documentation](https://gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
