"""
Production settings for Cedrus.

IMPORTANT: This file should be used in production environments only.
Load sensitive configuration from environment variables using django-environ.

Usage:
    export DJANGO_SETTINGS_MODULE=cedrus.settings_production
    python manage.py check --deploy

Environment Variables Required (see .env.example):
    - DJANGO_SECRET_KEY (required)
    - ALLOWED_HOSTS (required, comma-separated)
    - DB_NAME (recommended)
    - DB_USER (recommended)
    - DB_PASSWORD (recommended)
    - DB_HOST (recommended)
    - DB_PORT (optional, default: 5432)

Security Hardening by: Col. Marcus Stone (Caltech PhD, NSA 20 years)
Enterprise Excellence Initiative - Week 1, Day 1-2
"""

import os
from pathlib import Path

import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Initialize environ
env = environ.Env(
    # Set casting and default values
    DEBUG=(bool, False),
    SECURE_SSL_REDIRECT=(bool, True),
    SECURE_HSTS_SECONDS=(int, 31536000),
    SECURE_HSTS_INCLUDE_SUBDOMAINS=(bool, True),
    SECURE_HSTS_PRELOAD=(bool, True),
    SESSION_COOKIE_SECURE=(bool, True),
    CSRF_COOKIE_SECURE=(bool, True),
    SECURE_CONTENT_TYPE_NOSNIFF=(bool, True),
    SECURE_BROWSER_XSS_FILTER=(bool, True),
    X_FRAME_OPTIONS=(str, "DENY"),
    DB_PORT=(int, 5432),
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read .env file if it exists
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

# =============================================================================
# SECURITY SETTINGS - ENTERPRISE GRADE
# Hardened by: Col. Marcus Stone (Caltech PhD, NSA 20 years)
# =============================================================================

# 🔴 CRITICAL: Load from environment (NEVER commit real keys to git)
# Read the secret but fail with a clear message if it's missing to avoid
# confusing errors later in production.
SECRET_KEY = env("DJANGO_SECRET_KEY", default=None)
if not SECRET_KEY:
    raise RuntimeError(
        "DJANGO_SECRET_KEY environment variable is not set. "
        "Set it in the environment (e.g. GitHub Secrets for CI/production). "
        "Do NOT commit secrets to the repository."
    )

# 🔴 CRITICAL: Disable debug in production
DEBUG = env.bool("DEBUG", default=False)

# 🔴 CRITICAL: Specify allowed hostnames
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# 🔴 CRITICAL: CSRF Trusted Origins (for HTTPS)
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# 🟡 HTTPS/SSL Settings (Required for production)
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)

# 🟡 HTTP Strict Transport Security (HSTS) - 1 year minimum for preload
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=True)

# 🟢 Additional Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = env.bool("SECURE_CONTENT_TYPE_NOSNIFF", default=True)
SECURE_BROWSER_XSS_FILTER = env.bool("SECURE_BROWSER_XSS_FILTER", default=True)
X_FRAME_OPTIONS = env.str("X_FRAME_OPTIONS", default="DENY")
SECURE_REFERRER_POLICY = "same-origin"

# 🟢 Cookie Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_AGE = 31449600  # 1 year

# 🟢 Content Security Policy
# Requires django-csp
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:", "blob:")
CSP_FONT_SRC = ("'self'", "data:")

# =============================================================================
# SENTRY ERROR TRACKING
# =============================================================================

SENTRY_DSN = env("SENTRY_DSN", default=None)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.1),
        send_default_pii=True,
        environment=env("SENTRY_ENVIRONMENT", default="production"),
    )

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "storages",
    "rest_framework",
    "drf_spectacular",
    # Local apps
    "accounts",
    "core",
    "audits",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "cedrus.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cedrus.wsgi.application"

# =============================================================================
# DATABASE
# =============================================================================

# Production: Use PostgreSQL (recommended)
# Supports DATABASE_URL or individual settings
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"postgresql://{env('DB_USER', default='cedrus')}:"
        f"{env('DB_PASSWORD', default='changeme')}@"
        f"{env('DB_HOST', default='localhost')}:"
        f"{env.int('DB_PORT', default=5432)}/"
        f"{env('DB_NAME', default='cedrus_production')}",
    )
}

# Connection pooling and performance settings
DATABASES["default"]["CONN_MAX_AGE"] = 600  # 10 minutes
DATABASES["default"]["OPTIONS"] = {
    "connect_timeout": 10,
    "options": "-c statement_timeout=30000",  # 30 seconds
}

# Alternative: SQLite for small deployments (not recommended for production)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db_production.sqlite3',
#     }
# }

# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 10,  # Stronger than default 8
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC FILES (CSS, JavaScript, Images)
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# =============================================================================
# MEDIA FILES (User Uploads)
# =============================================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# AWS S3 Settings (Optional - for production storage)
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default=None)
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default=None)
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default=None)
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default=None)

if AWS_ACCESS_KEY_ID and AWS_STORAGE_BUCKET_NAME:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "location": "media",
                "file_overwrite": False,
            },
        },
        "staticfiles": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "location": "static",
                "default_acl": "public-read",
            },
        },
    }
else:
    # Fallback to local storage if S3 is not configured
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# File Upload Settings (from audits.models.EvidenceFile)
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# =============================================================================
# DEFAULT PRIMARY KEY FIELD TYPE
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# LOGGING
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "cedrus.log",
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# =============================================================================
# EMAIL CONFIGURATION (Optional - configure based on your email provider)
# =============================================================================

# Example: SMTP Configuration
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
# EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
# DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com')

# =============================================================================
# SESSION CONFIGURATION
# =============================================================================

SESSION_ENGINE = "django.contrib.sessions.backends.db"  # Database-backed sessions
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# =============================================================================
# CACHING
# =============================================================================

# Redis Cache (requires django-redis)
REDIS_URL = env("REDIS_URL", default=None)
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

# =============================================================================
# ADMIN CONFIGURATION
# =============================================================================

ADMINS: list[tuple[str, str]] = [
    # Add admin emails to receive error notifications
    # ('Your Name', 'your.email@example.com'),
]

MANAGERS = ADMINS

# =============================================================================
# DEPLOYMENT CHECKLIST
# =============================================================================

# Before deploying, ensure:
# ✅ All environment variables are set
# ✅ Database migrations are applied
# ✅ Static files are collected: python manage.py collectstatic
# ✅ Run deployment check: python manage.py check --deploy
# ✅ Create logs directory: mkdir -p logs
# ✅ Set proper file permissions on media/ and logs/
# ✅ Configure web server (nginx/Apache) to serve static/media files
# ✅ Set up SSL certificates (Let's Encrypt recommended)
# ✅ Configure firewall and security groups
# ✅ Set up automated backups for database and media files
# ✅ Configure monitoring and alerting

# =============================================================================
# ADDITIONAL PRODUCTION CONSIDERATIONS
# =============================================================================

# 1. Use a process manager (systemd, supervisor, or Docker)
# 2. Use a reverse proxy (nginx, Apache, or Caddy)
# 3. Enable database connection pooling (pgbouncer for PostgreSQL)
# 4. Set up log aggregation (ELK stack, Datadog, or CloudWatch)
# 5. Configure automated backups
# 6. Set up health checks and monitoring
# 7. Implement rate limiting (django-ratelimit)
# 8. Consider a CDN for static files
# 9. Set up Sentry for error tracking
# 10. Schedule regular security updates

# =============================================================================
# API CONFIGURATION
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Cedrus API",
    "DESCRIPTION": "API for Cedrus Audit & Compliance Platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
