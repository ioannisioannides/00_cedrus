"""
URL configuration for certification app.
"""

from django.urls import path

from certification.api import views

app_name = "certification"

urlpatterns = [
    # Technical Review views (ISO 17021 Clause 9.5)
    path(
        "audit/<int:audit_pk>/technical-review/",
        views.TechnicalReviewView.as_view(),
        name="technical_review_create",
    ),
    path(
        "technical-review/<int:pk>/edit/",
        views.TechnicalReviewUpdateView.as_view(),
        name="technical_review_update",
    ),
    # Certification Decision views (ISO 17021 Clause 9.6)
    path(
        "audit/<int:audit_pk>/certification-decision/",
        views.CertificationDecisionView.as_view(),
        name="certification_decision_create",
    ),
    path(
        "certification-decision/<int:pk>/edit/",
        views.CertificationDecisionUpdateView.as_view(),
        name="certification_decision_update",
    ),
    # Complaints & Appeals (Phase 2A)
    path("complaints/", views.ComplaintListView.as_view(), name="complaint_list"),
    path("complaints/create/", views.ComplaintCreateView.as_view(), name="complaint_create"),
    path("complaints/<int:pk>/", views.ComplaintDetailView.as_view(), name="complaint_detail"),
    path("appeals/", views.AppealListView.as_view(), name="appeal_list"),
    path("appeals/create/", views.AppealCreateView.as_view(), name="appeal_create"),
    path("appeals/<int:pk>/", views.AppealDetailView.as_view(), name="appeal_detail"),
]
