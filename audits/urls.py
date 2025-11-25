"""
URL configuration for audits app.
"""

from django.urls import path

from . import views, views_complaints, views_program

app_name = "audits"

urlpatterns = [
    # Audit Program views (ISO 19011)
    path("programs/", views_program.AuditProgramListView.as_view(), name="program_list"),
    path("programs/create/", views_program.AuditProgramCreateView.as_view(), name="program_create"),
    path("programs/<int:pk>/", views_program.AuditProgramDetailView.as_view(), name="program_detail"),
    path("programs/<int:pk>/edit/", views_program.AuditProgramUpdateView.as_view(), name="program_update"),
    path("programs/<int:pk>/delete/", views_program.AuditProgramDeleteView.as_view(), name="program_delete"),

    # Audit views
    path("", views.AuditListView.as_view(), name="audit_list"),
    path("create/", views.AuditCreateView.as_view(), name="audit_create"),
    path("<int:pk>/", views.AuditDetailView.as_view(), name="audit_detail"),
    path("<int:pk>/edit/", views.AuditUpdateView.as_view(), name="audit_update"),
    path("<int:pk>/print/", views.audit_print, name="audit_print"),
    path(
        "<int:pk>/transition/<str:new_status>/",
        views.audit_transition_status,
        name="audit_transition_status",
    ),
    # Team Member Management views
    path("<int:audit_pk>/team/add/", views.team_member_add, name="team_member_add"),
    path("team-member/<int:pk>/edit/", views.team_member_edit, name="team_member_edit"),
    path("team-member/<int:pk>/delete/", views.team_member_delete, name="team_member_delete"),
    # Audit Documentation views
    path("<int:audit_pk>/changes/edit/", views.audit_changes_edit, name="audit_changes_edit"),
    path(
        "<int:audit_pk>/plan-review/edit/",
        views.audit_plan_review_edit,
        name="audit_plan_review_edit",
    ),
    path("<int:audit_pk>/summary/edit/", views.audit_summary_edit, name="audit_summary_edit"),
    # Recommendations & Decision views
    path(
        "<int:audit_pk>/recommendation/edit/",
        views.audit_recommendation_edit,
        name="audit_recommendation_edit",
    ),
    path("<int:audit_pk>/decision/", views.audit_make_decision, name="audit_make_decision"),
    # Evidence File views
    path(
        "<int:audit_pk>/evidence/upload/", views.evidence_file_upload, name="evidence_file_upload"
    ),
    path(
        "evidence/<int:file_pk>/download/",
        views.evidence_file_download,
        name="evidence_file_download",
    ),
    path("evidence/<int:file_pk>/delete/", views.evidence_file_delete, name="evidence_file_delete"),
    # ============================================================================
    # FINDINGS CRUD - Nonconformity, Observation, OFI (Sprint 8)
    # ============================================================================
    # Nonconformity URLs
    path(
        "audit/<int:audit_pk>/nc/create/",
        views.NonconformityCreateView.as_view(),
        name="nonconformity_create",
    ),
    path("nc/<int:pk>/", views.NonconformityDetailView.as_view(), name="nonconformity_detail"),
    path("nc/<int:pk>/edit/", views.NonconformityUpdateView.as_view(), name="nonconformity_update"),
    path(
        "nc/<int:pk>/delete/", views.NonconformityDeleteView.as_view(), name="nonconformity_delete"
    ),
    # Observation URLs
    path(
        "audit/<int:audit_pk>/observation/create/",
        views.ObservationCreateView.as_view(),
        name="observation_create",
    ),
    path("observation/<int:pk>/", views.ObservationDetailView.as_view(), name="observation_detail"),
    path(
        "observation/<int:pk>/edit/",
        views.ObservationUpdateView.as_view(),
        name="observation_update",
    ),
    path(
        "observation/<int:pk>/delete/",
        views.ObservationDeleteView.as_view(),
        name="observation_delete",
    ),
    # Opportunity for Improvement URLs
    path(
        "audit/<int:audit_pk>/ofi/create/",
        views.OpportunityForImprovementCreateView.as_view(),
        name="ofi_create",
    ),
    path("ofi/<int:pk>/", views.OpportunityForImprovementDetailView.as_view(), name="ofi_detail"),
    path(
        "ofi/<int:pk>/edit/", views.OpportunityForImprovementUpdateView.as_view(), name="ofi_update"
    ),
    path(
        "ofi/<int:pk>/delete/",
        views.OpportunityForImprovementDeleteView.as_view(),
        name="ofi_delete",
    ),
    # Client Response & Verification (Sprint 8 - Tasks 8.2 & 8.3)
    path(
        "nc/<int:pk>/respond/",
        views.NonconformityResponseView.as_view(),
        name="nonconformity_respond",
    ),
    path(
        "nc/<int:pk>/verify/", views.NonconformityVerifyView.as_view(), name="nonconformity_verify"
    ),
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
    path("complaints/", views_complaints.ComplaintListView.as_view(), name="complaint_list"),
    path("complaints/create/", views_complaints.ComplaintCreateView.as_view(), name="complaint_create"),
    path("complaints/<int:pk>/", views_complaints.ComplaintDetailView.as_view(), name="complaint_detail"),
    path("appeals/", views_complaints.AppealListView.as_view(), name="appeal_list"),
    path("appeals/create/", views_complaints.AppealCreateView.as_view(), name="appeal_create"),
    path("appeals/<int:pk>/", views_complaints.AppealDetailView.as_view(), name="appeal_detail"),
]
