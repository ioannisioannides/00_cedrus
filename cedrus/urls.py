"""
URL configuration for cedrus project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path  # pylint: disable=no-name-in-module
from django.views.generic import RedirectView

# Health check imports
from core.health import health_check, liveness_check, readiness_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/login/", permanent=False), name="home"),
    # Health check endpoints (root level for container orchestration)
    path("health/", health_check, name="health"),
    path("health/ready/", readiness_check, name="readiness"),
    path("health/live/", liveness_check, name="liveness"),
    path("", include("accounts.urls")),
    path("core/", include("core.urls")),
    path("audits/", include("audits.urls")),
    path("reporting/", include("reporting.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Django Debug Toolbar
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
