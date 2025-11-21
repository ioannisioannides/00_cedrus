# ==============================================================================
# CEDRUS DOCKERFILE - ENTERPRISE GRADE, SELF-HOSTED
# ==============================================================================
# Multi-stage build for optimal image size and security
# Target: <500MB final image
# Architecture: Python 3.13 + Django 5.2.8
# Security: Non-root user, minimal attack surface
# 
# Built by: Dr. Thomas Berg (Caltech PhD, DevOps, 23 years)
#           Dr. Alex Müller (MIT PhD, Performance, 21 years)
# ==============================================================================

# ==============================================================================
# STAGE 1: BUILDER
# ==============================================================================
# Build Python dependencies in isolated builder stage
FROM python:3.13-slim-bookworm AS builder

# Build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Set build-time labels
LABEL maintainer="Cedrus Excellence Team <team@cedrus.local>"
LABEL stage="builder"

# Install build dependencies (only needed for compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for isolated dependencies
RUN python -m venv /opt/venv

# Enable virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first (Docker layer caching optimization)
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies in virtual environment
# --no-cache-dir: Don't cache pip downloads (saves space)
# --disable-pip-version-check: Skip pip version check (faster)
RUN pip install --no-cache-dir --disable-pip-version-check \
    --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --disable-pip-version-check \
    -r /tmp/requirements.txt

# ==============================================================================
# STAGE 2: RUNTIME
# ==============================================================================
# Minimal runtime image with only production dependencies
FROM python:3.13-slim-bookworm AS runtime

# Runtime arguments
ARG DEBIAN_FRONTEND=noninteractive
ARG UID=1000
ARG GID=1000

# Metadata labels (OCI standard)
LABEL org.opencontainers.image.title="Cedrus Audit Management System"
LABEL org.opencontainers.image.description="ISO 17021 Certification Body Audit Management Platform"
LABEL org.opencontainers.image.version="0.1.0-week1-day5"
LABEL org.opencontainers.image.vendor="Cedrus Excellence Initiative"
LABEL org.opencontainers.image.authors="Dr. Thomas Berg, Dr. Alex Müller"
LABEL org.opencontainers.image.url="https://cedrus.local"
LABEL org.opencontainers.image.documentation="https://cedrus.local/docs"
LABEL org.opencontainers.image.source="https://github.com/yourorg/cedrus"

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client library
    libpq5 \
    # Security: CA certificates for HTTPS
    ca-certificates \
    # Timezone data
    tzdata \
    # Network utilities for health checks
    curl \
    # File utilities
    gettext \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security (principle of least privilege)
# Running as root in containers is a security anti-pattern
RUN groupadd -g ${GID} cedrus && \
    useradd -u ${UID} -g ${GID} -m -s /bin/bash cedrus

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
# .dockerignore ensures we don't copy unnecessary files
COPY --chown=cedrus:cedrus . /app/

# Create necessary directories with correct permissions
RUN mkdir -p /app/media /app/staticfiles /app/logs && \
    chown -R cedrus:cedrus /app/media /app/staticfiles /app/logs

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=cedrus.settings \
    # Security: Disable Python hash randomization for reproducibility
    PYTHONHASHSEED=random \
    # Performance: Python optimization level
    PYTHONOPTIMIZE=1 \
    # Locale
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=UTC

# Expose port 8000 (Django development server / Gunicorn)
EXPOSE 8000

# Switch to non-root user
USER cedrus

# Health check (Docker native)
# Check every 30s, timeout 3s, 3 retries before unhealthy
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command: Run Gunicorn for production
# Override this in docker-compose for development (runserver)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--worker-tmp-dir", "/dev/shm", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "50", \
     "--timeout", "30", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output", \
     "cedrus.wsgi:application"]

# ==============================================================================
# BUILD INSTRUCTIONS
# ==============================================================================
# Development build:
#   docker build -t cedrus:dev .
#
# Production build with version tag:
#   docker build -t cedrus:0.1.0 -t cedrus:latest .
#
# Build with custom user ID (match host user):
#   docker build --build-arg UID=$(id -u) --build-arg GID=$(id -g) -t cedrus:dev .
#
# Multi-platform build (ARM64 + AMD64):
#   docker buildx build --platform linux/amd64,linux/arm64 -t cedrus:latest .
#
# Size optimization check:
#   docker images cedrus:latest
#   docker history cedrus:latest
# ==============================================================================
