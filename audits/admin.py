"""
Django admin configuration for audits app.
"""

from django.contrib import admin

from .models import (  # Phase 2 models
    Audit,
    AuditChanges,
    AuditorCompetenceWarning,
    AuditPlanReview,
    AuditRecommendation,
    AuditStatusLog,
    AuditSummary,
    AuditTeamMember,
    CertificationDecision,
    EvidenceFile,
    FindingRecurrence,
    Nonconformity,
    Observation,
    OpportunityForImprovement,
    RootCauseCategory,
    TechnicalReview,
)


class AuditTeamMemberInline(admin.TabularInline):
    """Inline admin for AuditTeamMember."""

    model = AuditTeamMember
    extra = 1
    fields = ["user", "name", "title", "role", "date_from", "date_to"]


class NonconformityInline(admin.TabularInline):
    """Inline admin for Nonconformity (read-only for overview)."""

    model = Nonconformity
    extra = 0
    fields = ["clause", "category", "verification_status", "due_date"]
    readonly_fields = ["clause", "category", "verification_status", "due_date"]
    can_delete = False
    show_change_link = True


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    """Admin for Audit model."""

    list_display = [
        "organization",
        "audit_type",
        "status",
        "total_audit_date_from",
        "total_audit_date_to",
        "lead_auditor",
        "created_at",
    ]
    list_filter = ["status", "audit_type", "created_at", "organization"]
    search_fields = ["organization__name", "lead_auditor__username"]
    readonly_fields = ["created_at", "updated_at"]
    filter_horizontal = ["certifications", "sites"]
    inlines = [AuditTeamMemberInline]
    fieldsets = (
        ("Basic Information", {"fields": ("organization", "audit_type", "status")}),
        ("Certifications & Sites", {"fields": ("certifications", "sites")}),
        (
            "Dates & Duration (IAF MD5)",
            {
                "fields": (
                    "total_audit_date_from",
                    "total_audit_date_to",
                    "planned_duration_hours",
                    "actual_duration_hours",
                    "duration_justification",
                )
            },
        ),
        ("Personnel", {"fields": ("created_by", "lead_auditor")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(AuditTeamMember)
class AuditTeamMemberAdmin(admin.ModelAdmin):
    """Admin for AuditTeamMember model."""

    list_display = ["name", "audit", "role", "date_from", "date_to"]
    list_filter = ["role", "audit__organization"]
    search_fields = ["name", "user__username", "audit__organization__name"]


@admin.register(AuditChanges)
class AuditChangesAdmin(admin.ModelAdmin):
    """Admin for AuditChanges model."""

    list_display = ["audit", "change_of_name", "change_of_scope", "change_of_sites"]
    list_filter = ["change_of_name", "change_of_scope", "change_of_sites"]
    search_fields = ["audit__organization__name"]


@admin.register(AuditPlanReview)
class AuditPlanReviewAdmin(admin.ModelAdmin):
    """Admin for AuditPlanReview model."""

    list_display = ["audit", "deviations_yes_no", "issues_affecting_yes_no", "next_audit_date_from"]
    search_fields = ["audit__organization__name"]


@admin.register(AuditSummary)
class AuditSummaryAdmin(admin.ModelAdmin):
    """Admin for AuditSummary model."""

    list_display = ["audit", "objectives_met", "ms_meets_requirements", "ms_effective"]
    search_fields = ["audit__organization__name"]
    fieldsets = (
        (
            "Objectives & Scope",
            {
                "fields": (
                    "objectives_met",
                    "objectives_comments",
                    "scope_appropriate",
                    "scope_comments",
                )
            },
        ),
        (
            "Management System",
            {
                "fields": (
                    "ms_meets_requirements",
                    "ms_comments",
                    "ms_effective",
                    "ms_effective_comments",
                )
            },
        ),
        (
            "Review & Audit",
            {
                "fields": (
                    "management_review_effective",
                    "management_review_comments",
                    "internal_audit_effective",
                    "internal_audit_comments",
                )
            },
        ),
        (
            "Other",
            {
                "fields": (
                    "correct_use_of_logos",
                    "logos_comments",
                    "promoted_to_committee",
                    "committee_comments",
                    "general_commentary",
                )
            },
        ),
    )


@admin.register(Nonconformity)
class NonconformityAdmin(admin.ModelAdmin):
    """Admin for Nonconformity model."""

    list_display = [
        "audit",
        "clause",
        "category",
        "verification_status",
        "due_date",
        "created_by",
        "created_at",
    ]
    list_filter = ["category", "verification_status", "created_at", "audit__organization"]
    search_fields = ["clause", "statement_of_nc", "audit__organization__name"]
    readonly_fields = ["created_at"]
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("audit", "standard", "clause", "category", "created_by", "created_at")},
        ),
        (
            "Nonconformity Details",
            {"fields": ("objective_evidence", "statement_of_nc", "auditor_explanation")},
        ),
        (
            "Client Response",
            {
                "fields": (
                    "client_root_cause",
                    "client_correction",
                    "client_corrective_action",
                    "due_date",
                )
            },
        ),
        ("Verification", {"fields": ("verification_status", "verified_by", "verified_at")}),
    )


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    """Admin for Observation model."""

    list_display = ["audit", "clause", "created_by", "created_at"]
    list_filter = ["created_at", "audit__organization"]
    search_fields = ["clause", "statement", "audit__organization__name"]
    readonly_fields = ["created_at"]


@admin.register(OpportunityForImprovement)
class OpportunityForImprovementAdmin(admin.ModelAdmin):
    """Admin for OpportunityForImprovement model."""

    list_display = ["audit", "clause", "created_by", "created_at"]
    list_filter = ["created_at", "audit__organization"]
    search_fields = ["clause", "description", "audit__organization__name"]
    readonly_fields = ["created_at"]


@admin.register(AuditRecommendation)
class AuditRecommendationAdmin(admin.ModelAdmin):
    """Admin for AuditRecommendation model."""

    list_display = [
        "audit",
        "special_audit_required",
        "suspension_recommended",
        "revocation_recommended",
        "stage2_required",
    ]
    search_fields = ["audit__organization__name"]
    fieldsets = (
        ("Special Audit", {"fields": ("special_audit_required", "special_audit_details")}),
        ("Suspension", {"fields": ("suspension_recommended", "suspension_certificates")}),
        ("Revocation", {"fields": ("revocation_recommended", "revocation_certificates")}),
        ("Other", {"fields": ("stage2_required", "decision_notes")}),
    )


@admin.register(EvidenceFile)
class EvidenceFileAdmin(admin.ModelAdmin):
    """Admin for EvidenceFile model."""

    list_display = [
        "audit",
        "finding",
        "evidence_type",
        "uploaded_by",
        "uploaded_at",
        "purge_after",
    ]
    list_filter = ["evidence_type", "uploaded_at", "audit__organization"]
    search_fields = ["audit__organization__name", "uploaded_by__username", "description"]
    readonly_fields = ["uploaded_at", "purge_after"]
    fieldsets = (
        ("Basic Information", {"fields": ("audit", "finding", "evidence_type", "description")}),
        ("File", {"fields": ("file", "uploaded_by", "uploaded_at")}),
        ("Retention Policy", {"fields": ("retention_years", "purge_after")}),
    )


@admin.register(AuditStatusLog)
class AuditStatusLogAdmin(admin.ModelAdmin):
    """Admin for AuditStatusLog model."""

    list_display = ["audit", "from_status", "to_status", "changed_by", "changed_at"]
    list_filter = ["from_status", "to_status", "changed_at"]
    search_fields = ["audit__organization__name", "changed_by__username", "notes"]
    readonly_fields = ["audit", "from_status", "to_status", "changed_by", "changed_at"]

    def has_add_permission(self, request):
        """Prevent manual creation - logs are auto-generated."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - logs are immutable."""
        return False


@admin.register(TechnicalReview)
class TechnicalReviewAdmin(admin.ModelAdmin):
    """Admin for TechnicalReview model."""

    list_display = ["audit", "reviewer", "status", "reviewed_at"]
    list_filter = ["status", "reviewed_at"]
    search_fields = ["audit__organization__name", "reviewer__username"]
    readonly_fields = ["reviewed_at"]
    fieldsets = (
        ("Basic Information", {"fields": ("audit", "reviewer", "status", "reviewed_at")}),
        (
            "ISO 17021-1 Clause 9.4.8 Checklist",
            {
                "fields": (
                    "scope_verified",
                    "objectives_verified",
                    "findings_reviewed",
                    "conclusion_clear",
                )
            },
        ),
        ("Notes", {"fields": ("reviewer_notes", "clarification_requested")}),
    )


@admin.register(CertificationDecision)
class CertificationDecisionAdmin(admin.ModelAdmin):
    """Admin for CertificationDecision model."""

    list_display = ["audit", "decision", "decision_maker", "decided_at"]
    list_filter = ["decision", "decided_at"]
    search_fields = ["audit__organization__name", "decision_maker__username"]
    readonly_fields = ["decided_at"]
    filter_horizontal = ["certifications_affected"]
    fieldsets = (
        ("Basic Information", {"fields": ("audit", "decision_maker", "decided_at")}),
        ("Decision", {"fields": ("decision", "decision_notes")}),
        ("Affected Certifications", {"fields": ("certifications_affected",)}),
    )


# ============================================================================
# PHASE 2 ADMIN INTERFACES: Root Cause Analysis & Competence Tracking
# ============================================================================


@admin.register(RootCauseCategory)
class RootCauseCategoryAdmin(admin.ModelAdmin):
    """Admin for RootCauseCategory model."""

    list_display = ["code", "name", "parent", "is_active", "created_at"]
    list_filter = ["is_active", "parent", "created_at"]
    search_fields = ["code", "name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Category Information", {"fields": ("code", "name", "description", "parent")}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        """Optimize query with parent relationships."""
        qs = super().get_queryset(request)
        return qs.select_related("parent")


@admin.register(FindingRecurrence)
class FindingRecurrenceAdmin(admin.ModelAdmin):
    """Admin for FindingRecurrence model."""

    list_display = [
        "finding",
        "recurrence_count",
        "first_occurrence",
        "last_occurrence",
        "corrective_actions_effective",
        "escalation_required",
    ]
    list_filter = [
        "corrective_actions_effective",
        "escalation_required",
        "recurrence_count",
        "last_occurrence",
    ]
    search_fields = [
        "finding__clause",
        "finding__statement_of_nc",
        "finding__audit__organization__name",
        "resolution_notes",
    ]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Finding Reference", {"fields": ("finding",)}),
        (
            "Recurrence Data",
            {
                "fields": (
                    "recurrence_count",
                    "first_occurrence",
                    "last_occurrence",
                    "previous_audits",
                )
            },
        ),
        (
            "Resolution Tracking",
            {"fields": ("corrective_actions_effective", "resolution_notes", "escalation_required")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        """Optimize query with finding relationships."""
        qs = super().get_queryset(request)
        return qs.select_related("finding", "finding__audit", "finding__audit__organization")


@admin.register(AuditorCompetenceWarning)
class AuditorCompetenceWarningAdmin(admin.ModelAdmin):
    """Admin for AuditorCompetenceWarning model."""

    list_display = [
        "auditor",
        "audit",
        "warning_type",
        "severity",
        "issued_at",
        "resolved_at",
        "acknowledged_by_auditor",
    ]
    list_filter = [
        "warning_type",
        "severity",
        "issued_at",
        "resolved_at",
        "acknowledged_by_auditor",
    ]
    search_fields = [
        "auditor__username",
        "auditor__first_name",
        "auditor__last_name",
        "audit__organization__name",
        "description",
        "resolution_notes",
    ]
    readonly_fields = ["issued_at"]
    fieldsets = (
        ("Warning Details", {"fields": ("audit", "auditor", "warning_type", "severity")}),
        ("Description", {"fields": ("description",)}),
        ("Issuance", {"fields": ("issued_by", "issued_at")}),
        ("Resolution", {"fields": ("resolved_at", "resolution_notes", "acknowledged_by_auditor")}),
    )

    def get_queryset(self, request):
        """Optimize query with related objects."""
        qs = super().get_queryset(request)
        return qs.select_related("audit", "auditor", "issued_by", "audit__organization")

    def save_model(self, request, obj, form, change):
        """Auto-set issued_by to current user if creating new warning."""
        if not change:  # Only on creation
            obj.issued_by = request.user
        super().save_model(request, obj, form, change)
