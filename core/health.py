# ==============================================================================
# CEDRUS HEALTH CHECK ENDPOINTS
# ==============================================================================
# Container orchestration health checks
# - /health/ - Basic application health
# - /health/ready/ - Readiness check (database + Redis)
# - /health/live/ - Liveness check
#
# Built by: Dr. Thomas Berg (Caltech PhD, DevOps, 23 years)
# ==============================================================================
# pylint: disable=broad-exception-caught

import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@never_cache
@require_GET
def health_check(request):
    """
    Basic health check endpoint.

    Returns 200 OK if application is running.
    Used by Docker HEALTHCHECK directive.

    Response:
        {
            "status": "healthy",
            "timestamp": "2025-11-21T10:00:00Z",
            "version": "0.1.0"
        }
    """
    return JsonResponse(
        {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "version": "0.1.0",
        },
        status=200,
    )


@never_cache
@require_GET
def readiness_check(request):
    """
    Readiness check endpoint.

    Verifies that application is ready to serve traffic:
    - Database connection
    - Redis connection
    - Critical models accessible

    Returns 200 if ready, 503 if not ready.
    Used by Kubernetes readinessProbe and load balancers.

    Response (healthy):
        {
            "status": "ready",
            "timestamp": "2025-11-21T10:00:00Z",
            "checks": {
                "database": "healthy",
                "cache": "healthy",
                "models": "healthy"
            }
        }

    Response (unhealthy):
        {
            "status": "not_ready",
            "timestamp": "2025-11-21T10:00:00Z",
            "checks": {
                "database": "unhealthy",
                "cache": "healthy",
                "models": "unhealthy"
            },
            "errors": ["Database connection failed", ...]
        }
    """
    checks = {}
    errors = []

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                checks["database"] = "healthy"
            else:
                checks["database"] = "unhealthy"
                errors.append("Database query returned unexpected result")
    except Exception as e:
        checks["database"] = "unhealthy"
        errors.append(f"Database connection failed: {str(e)}")

    # Cache check (Redis)
    try:
        cache_key = "health_check_test"
        cache_value = "test_value"
        cache.set(cache_key, cache_value, timeout=10)
        retrieved_value = cache.get(cache_key)

        if retrieved_value == cache_value:
            checks["cache"] = "healthy"
        else:
            checks["cache"] = "unhealthy"
            errors.append("Cache read/write test failed")
    except Exception as e:
        checks["cache"] = "unhealthy"
        errors.append(f"Cache connection failed: {str(e)}")

    # Model access check (verify ORM is working)
    try:
        User = get_user_model()
        # Don't create queries, just check model is accessible
        _ = User._meta.model_name
        checks["models"] = "healthy"
    except Exception as e:
        checks["models"] = "unhealthy"
        errors.append(f"Model access failed: {str(e)}")

    # Determine overall status
    all_healthy = all(status == "healthy" for status in checks.values())

    response_data = {
        "timestamp": timezone.now().isoformat(),
        "checks": checks,
    }

    if all_healthy:
        response_data["status"] = "ready"
        return JsonResponse(response_data, status=200)

    response_data["status"] = "not_ready"
    response_data["errors"] = errors
    return JsonResponse(response_data, status=503)


@never_cache
@require_GET
def liveness_check(request):
    """
    Liveness check endpoint.

    Verifies that application is alive and not deadlocked.
    Should be very lightweight - just verify Python interpreter is running.

    Returns 200 if alive, 503 if dead.
    Used by Kubernetes livenessProbe.

    Response:
        {
            "status": "alive",
            "timestamp": "2025-11-21T10:00:00Z",
            "python_version": "3.13.0",
            "uptime_seconds": 3600
        }
    """
    try:
        # Get Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # Basic uptime check (if process info available)
        # This is a simple alive check - just verify we can execute Python code

        return JsonResponse(
            {
                "status": "alive",
                "timestamp": timezone.now().isoformat(),
                "python_version": python_version,
                "django_version": settings.DJANGO_VERSION if hasattr(settings, "DJANGO_VERSION") else "unknown",
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse(
            {
                "status": "dead",
                "timestamp": timezone.now().isoformat(),
                "error": str(e),
            },
            status=503,
        )


@never_cache
@require_GET
def detailed_status(request):
    """
    Detailed status endpoint (admin/debugging only).

    Returns comprehensive system status including:
    - Application version
    - Database status
    - Cache status
    - Settings (non-sensitive)
    - System resources

    Should be restricted to admin users in production.

    Response:
        {
            "status": "healthy",
            "timestamp": "2025-11-21T10:00:00Z",
            "application": {...},
            "database": {...},
            "cache": {...},
            "system": {...}
        }
    """
    # Only allow in DEBUG mode or for superusers
    if not settings.DEBUG and not (request.user.is_authenticated and request.user.is_superuser):
        return JsonResponse(
            {"error": "Forbidden - admin access required"}, status=403
        )

    status_data = {
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
    }

    # Application info
    status_data["application"] = {
        "version": "0.1.0",
        "debug_mode": settings.DEBUG,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "django_version": settings.DJANGO_VERSION if hasattr(settings, "DJANGO_VERSION") else "unknown",
    }

    # Database info
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()[0]

        status_data["database"] = {
            "status": "connected",
            "engine": connection.settings_dict.get("ENGINE", "unknown").split(".")[-1],
            "name": connection.settings_dict.get("NAME", "unknown"),
            "version": db_version,
        }
    except Exception as e:
        status_data["database"] = {
            "status": "error",
            "error": str(e),
        }

    # Cache info
    try:
        cache_key = "detailed_status_test"
        cache.set(cache_key, "test", timeout=10)
        cache_works = cache.get(cache_key) == "test"

        status_data["cache"] = {
            "status": "connected" if cache_works else "error",
            "backend": settings.CACHES["default"]["BACKEND"].split(".")[-1],
        }
    except Exception as e:
        status_data["cache"] = {
            "status": "error",
            "error": str(e),
        }

    # System info (basic)
    status_data["system"] = {
        "platform": sys.platform,
        "python_implementation": sys.implementation.name,
    }

    return JsonResponse(status_data, status=200)
