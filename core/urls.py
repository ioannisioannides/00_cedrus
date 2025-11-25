"""
URL configuration for core app.
"""

from django.urls import path

from . import health, views

app_name = "core"

urlpatterns = [
    # Health check endpoints
    path("health/", health.health_check, name="health_check"),
    path("health/ready/", health.readiness_check, name="readiness_check"),
    path("health/live/", health.liveness_check, name="liveness_check"),
    path("health/status/", health.detailed_status, name="detailed_status"),
    # Organizations
    path("organizations/", views.OrganizationListView.as_view(), name="organization_list"),
    path(
        "organizations/<int:pk>/",
        views.OrganizationDetailView.as_view(),
        name="organization_detail",
    ),
    path(
        "organizations/create/", views.OrganizationCreateView.as_view(), name="organization_create"
    ),
    path(
        "organizations/<int:pk>/edit/",
        views.OrganizationUpdateView.as_view(),
        name="organization_update",
    ),
    # Sites
    path("sites/", views.SiteListView.as_view(), name="site_list"),
    path("sites/create/", views.SiteCreateView.as_view(), name="site_create"),
    path("sites/<int:pk>/edit/", views.SiteUpdateView.as_view(), name="site_update"),
    # Standards
    path("standards/", views.StandardListView.as_view(), name="standard_list"),
    path("standards/create/", views.StandardCreateView.as_view(), name="standard_create"),
    path("standards/<int:pk>/edit/", views.StandardUpdateView.as_view(), name="standard_update"),
    # Certifications
    path("certifications/", views.CertificationListView.as_view(), name="certification_list"),
    path(
        "certifications/create/",
        views.CertificationCreateView.as_view(),
        name="certification_create",
    ),
    path(
        "certifications/<int:pk>/edit/",
        views.CertificationUpdateView.as_view(),
        name="certification_update",
    ),
    path(
        "certifications/<int:pk>/",
        views.CertificationDetailView.as_view(),
        name="certification_detail",
    ),
    path(
        "certifications/<int:certification_pk>/history/add/",
        views.CertificateHistoryCreateView.as_view(),
        name="certificate_history_create",
    ),
    path(
        "surveillance/<int:pk>/edit/",
        views.SurveillanceScheduleUpdateView.as_view(),
        name="surveillance_schedule_update",
    ),
]
