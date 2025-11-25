"""
Audits app models for audit management, findings, and recommendations.

This app contains the core audit workflow models:
- Audit: The main audit record
- AuditTeamMember: Team members assigned to an audit
- AuditChanges, AuditPlanReview, AuditSummary: Audit metadata sections
- Finding (abstract): Base class for findings
- Nonconformity, Observation, OpportunityForImprovement: Finding types
- AuditRecommendation: Final recommendations
- EvidenceFile: File attachments
"""

# pylint: disable=too-many-lines

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class AuditProgram(models.Model):
    """
    Annual audit program (ISO 19011 Clause 5).

    Defines the schedule, objectives, and risks for a set of audits
    (internal or external) over a specific period (usually a year).
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    organization = models.ForeignKey("core.Organization", on_delete=models.CASCADE, related_name="audit_programs")
    title = models.CharField(max_length=255, help_text="Program title (e.g., '2025 Internal Audit Program')")
    year = models.PositiveIntegerField(help_text="Program year")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    objectives = models.TextField(help_text="Audit program objectives (ISO 19011 5.2)")
    risks_opportunities = models.TextField(
        help_text="Risks and opportunities associated with the audit program (ISO 19011 5.3)"
    )

    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="audit_programs_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Audit Program"
        verbose_name_plural = "Audit Programs"
        ordering = ["-year", "title"]
        unique_together = ["organization", "year", "title"]

    def __str__(self):
        return f"{self.title} ({self.organization.name})"


class Audit(models.Model):
    """
    Main audit record.

    An audit is performed on an organization, covers specific certifications
    and sites, and is managed by a lead auditor.
    """

    AUDIT_TYPE_CHOICES = [
        ("stage1", "Stage 1"),
        ("stage2", "Stage 2"),
        ("surveillance", "Surveillance"),
        ("recertification", "Recertification"),
        ("transfer", "Transfer"),
        ("special", "Special"),
        ("internal", "Internal Audit"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("report_draft", "Report Draft"),
        ("client_review", "Client Review"),
        ("submitted", "Submitted"),
        ("technical_review", "Technical Review"),
        ("decision_pending", "Decision Pending"),
        ("decided", "Decided"),
        ("closed", "Closed"),
        ("cancelled", "Cancelled"),
    ]

    program = models.ForeignKey(
        AuditProgram,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audits",
        help_text="Audit program this audit belongs to",
    )
    organization = models.ForeignKey("core.Organization", on_delete=models.CASCADE, related_name="audits")
    certifications = models.ManyToManyField(
        "core.Certification",
        related_name="audits",
        help_text="Certifications covered by this audit",
    )
    sites = models.ManyToManyField("core.Site", related_name="audits", help_text="Sites covered by this audit")
    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPE_CHOICES, help_text="Type of audit")
    total_audit_date_from = models.DateField(help_text="Audit start date")
    total_audit_date_to = models.DateField(help_text="Audit end date")

    # IAF MD5 Duration Management
    planned_duration_hours = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0)],
        help_text="Planned audit duration (IAF MD5 calculation)",
    )
    actual_duration_hours = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0)],
        help_text="Actual audit duration in hours",
    )
    duration_justification = models.TextField(
        blank=True, help_text="Justification for deviation from planned duration (IAF MD5)"
    )

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="draft")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="audits_created")
    lead_auditor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="audits_led",
        help_text="Lead auditor responsible for this audit",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Audit"
        verbose_name_plural = "Audits"
        ordering = ["-total_audit_date_from", "-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["lead_auditor"]),
        ]

    def __str__(self):
        """Return string representation of the model instance."""
        return f"{self.organization.name} - {self.get_audit_type_display()} ({self.get_status_display()})"

    def clean(self):
        """Validate audit data."""
        from django.core.exceptions import ValidationError

        errors = {}
        self._validate_dates(errors)
        self._validate_audit_type(errors)

        if errors:
            raise ValidationError(errors)

        self._validate_organization_consistency()
        self._validate_roles()

    def _validate_dates(self, errors):
        """Validate audit dates."""
        from datetime import timedelta

        from django.utils import timezone

        # Validate that end date is not before start date
        if self.total_audit_date_from and self.total_audit_date_to:
            if self.total_audit_date_to < self.total_audit_date_from:
                errors["total_audit_date_to"] = "Audit end date must be on or after start date."

        # Validate future dates - audits shouldn't be > 1 year in future
        if self.total_audit_date_from:
            one_year_ahead = timezone.now().date() + timedelta(days=365)
            if self.total_audit_date_from > one_year_ahead:
                errors["total_audit_date_from"] = "Audit start date cannot be more than 1 year in the future."

    def _validate_audit_type(self, errors):
        """Validate audit type specific rules."""
        # Validate audit sequence - Stage 2 must follow Stage 1
        if self.audit_type == "stage2" and self.organization:
            # Check if there's a completed Stage 1 audit for this organization
            previous_stage1 = Audit.objects.filter(
                organization=self.organization, audit_type="stage1", status="closed"
            ).exists()

            if not previous_stage1:
                errors["audit_type"] = "Stage 2 audit requires a completed Stage 1 audit for this organization."

        # Validate surveillance audits - require previous certification
        if self.audit_type == "surveillance" and self.organization and self.pk:
            # Check if organization has active certifications (only after save)
            has_active_cert = self.certifications.filter(certificate_status="active").exists()

            if not has_active_cert:
                errors["audit_type"] = "Surveillance audit requires at least one active certification."

    def _validate_organization_consistency(self):
        """Validate that related objects belong to the same organization."""
        from django.core.exceptions import ValidationError

        # Validate that certifications belong to the organization
        if self.pk and self.organization:
            # Check certifications (only after save since it's M2M)
            invalid_certs = self.certifications.exclude(organization=self.organization)
            if invalid_certs.exists():
                raise ValidationError(
                    {"certifications": f"All certifications must belong to {self.organization.name}."}
                )

            # Check sites (only after save since it's M2M)
            invalid_sites = self.sites.exclude(organization=self.organization)
            if invalid_sites.exists():
                raise ValidationError({"sites": f"All sites must belong to {self.organization.name}."})

    def _validate_roles(self):
        """Validate user roles."""
        from django.core.exceptions import ValidationError

        # Validate that lead_auditor has proper role
        if self.lead_auditor:
            has_auditor_role = self.lead_auditor.groups.filter(
                name__in=["lead_auditor", "auditor", "cb_admin"]
            ).exists()
            if not has_auditor_role:
                raise ValidationError(
                    {
                        "lead_auditor": (
                            f"{self.lead_auditor.username} does not have lead_auditor, " "auditor, or cb_admin role."
                        )
                    }
                )


class AuditTeamMember(models.Model):
    """
    Team member assigned to an audit.

    Can be a User (internal auditor) or external (name/title only).
    """

    ROLE_CHOICES = [
        ("lead_auditor", "Lead Auditor"),
        ("auditor", "Auditor"),
        ("technical_expert", "Technical Expert"),
        ("trainee", "Trainee"),
        ("observer", "Observer"),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="team_members")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_assignments",
        help_text="User account (null for external experts)",
    )
    name = models.CharField(max_length=255, help_text="Full name (required if user is null)")
    title = models.CharField(max_length=255, blank=True, help_text="Job title or role")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, help_text="Role in the audit team")
    date_from = models.DateField(help_text="Start date for this team member")
    date_to = models.DateField(help_text="End date for this team member")

    class Meta:
        verbose_name = "Audit Team Member"
        verbose_name_plural = "Audit Team Members"
        ordering = ["audit", "role", "name"]

    def __str__(self):
        """Return string representation of the model instance."""
        return f"{self.name} - {self.get_role_display()} ({self.audit})"

    def clean(self):
        """Validate team member data."""
        from django.core.exceptions import ValidationError

        # Validate that name is provided if user is null
        if not self.user and not self.name:
            raise ValidationError("Either user or name must be provided.")

        # Validate that team member dates are within audit dates
        if self.date_from and self.date_to and self.audit:
            if self.date_from > self.date_to:
                raise ValidationError({"date_to": "End date must be on or after start date."})

            if self.date_from < self.audit.total_audit_date_from:
                raise ValidationError(
                    {
                        "date_from": (
                            f"Team member start date cannot be before audit start date "
                            f"({self.audit.total_audit_date_from})."
                        )
                    }
                )

            if self.date_to > self.audit.total_audit_date_to:
                raise ValidationError(
                    {
                        "date_to": (
                            f"Team member end date cannot be after audit end date "
                            f"({self.audit.total_audit_date_to})."
                        )
                    }
                )

        # Validate that user has appropriate role for team assignment
        if self.user and self.role:
            # Check if user has auditor-related role
            is_auditor = self.user.groups.filter(
                name__in=["lead_auditor", "auditor", "technical_expert", "cb_admin"]
            ).exists()

            if not is_auditor and self.role in ["lead_auditor", "auditor", "technical_expert"]:
                raise ValidationError(
                    {
                        "user": (
                            f"{self.user.username} does not have an auditor role and cannot be "
                            f"assigned as {self.get_role_display()}."
                        )
                    }
                )


class AuditChanges(models.Model):
    """
    Track changes to organization details during the audit.

    OneToOne with Audit - each audit has one changes record.
    """

    audit = models.OneToOneField(Audit, on_delete=models.CASCADE, related_name="changes")
    change_of_name = models.BooleanField(default=False)
    change_of_scope = models.BooleanField(default=False)
    change_of_sites = models.BooleanField(default=False)
    change_of_ms_rep = models.BooleanField(default=False, help_text="Change of Management System Representative")
    change_of_signatory = models.BooleanField(default=False)
    change_of_employee_count = models.BooleanField(default=False)
    change_of_contact_info = models.BooleanField(default=False)
    other_has_change = models.BooleanField(default=False)
    other_description = models.TextField(blank=True, help_text="Description of other changes")

    class Meta:
        verbose_name = "Audit Changes"
        verbose_name_plural = "Audit Changes"

    def __str__(self):
        """Return string representation of the model instance."""
        return f"Changes for {self.audit}"


class AuditPlanReview(models.Model):
    """
    Review of the audit plan and any deviations.

    OneToOne with Audit - each audit has one plan review.
    """

    audit = models.OneToOneField(Audit, on_delete=models.CASCADE, related_name="plan_review")
    deviations_yes_no = models.BooleanField(default=False, help_text="Were there deviations from the audit plan?")
    deviations_details = models.TextField(blank=True, help_text="Details of deviations")
    issues_affecting_yes_no = models.BooleanField(default=False, help_text="Were there issues affecting the audit?")
    issues_affecting_details = models.TextField(blank=True, help_text="Details of issues affecting the audit")
    next_audit_date_from = models.DateField(null=True, blank=True, help_text="Proposed next audit start date")
    next_audit_date_to = models.DateField(null=True, blank=True, help_text="Proposed next audit end date")

    class Meta:
        verbose_name = "Audit Plan Review"
        verbose_name_plural = "Audit Plan Reviews"

    def __str__(self):
        """Return string representation of the model instance."""
        return f"Plan Review for {self.audit}"


class AuditSummary(models.Model):
    """
    Summary and evaluation of the audit.

    OneToOne with Audit - each audit has one summary.
    Contains various yes/no questions with comment fields.
    """

    audit = models.OneToOneField(Audit, on_delete=models.CASCADE, related_name="summary")

    # Evaluation questions
    objectives_met = models.BooleanField(default=False)
    objectives_comments = models.TextField(blank=True)

    scope_appropriate = models.BooleanField(default=False)
    scope_comments = models.TextField(blank=True)

    ms_meets_requirements = models.BooleanField(default=False, help_text="Management system meets requirements")
    ms_comments = models.TextField(blank=True)

    management_review_effective = models.BooleanField(default=False)
    management_review_comments = models.TextField(blank=True)

    internal_audit_effective = models.BooleanField(default=False)
    internal_audit_comments = models.TextField(blank=True)

    ms_effective = models.BooleanField(default=False, help_text="Management system is effective")
    ms_effective_comments = models.TextField(blank=True)

    correct_use_of_logos = models.BooleanField(default=False)
    logos_comments = models.TextField(blank=True)

    promoted_to_committee = models.BooleanField(default=False)
    committee_comments = models.TextField(blank=True)

    general_commentary = models.TextField(blank=True, help_text="General commentary (A.4)")

    class Meta:
        verbose_name = "Audit Summary"
        verbose_name_plural = "Audit Summaries"

    def __str__(self):
        """Return string representation of the model instance."""
        return f"Summary for {self.audit}"


class Finding(models.Model):
    """
    Abstract base model for audit findings.

    All finding types (NC, Observation, OFI) inherit from this.
    """

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="%(class)s_set")
    standard = models.ForeignKey(
        "core.Standard",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Standard clause this finding relates to",
    )
    clause = models.CharField(max_length=100, help_text="Clause reference (e.g., '4.1', '7.5.1')")
    site = models.ForeignKey(
        "core.Site",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_findings",
        help_text="Specific site where finding was raised (for multi-site audits)",
    )
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="%(class)s_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["clause", "created_at"]
        indexes = [
            models.Index(fields=["site"]),
        ]

    def __str__(self):
        """Return string representation of the model instance."""
        return f"{self.__class__.__name__} - {self.clause} ({self.audit})"

    def clean(self):
        """Validate finding data."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Validate that standard belongs to one of the audit's certifications
        # Only validate if audit is available (not excluded from validation)
        if self.standard and hasattr(self, "audit") and self.audit:
            # Get standards from audit's certifications
            audit_standards = self.audit.certifications.values_list("standard", flat=True)

            if self.standard.pk not in audit_standards:
                errors["standard"] = (
                    f"Standard {self.standard.code} is not part of this audit's certifications. "
                    f"This audit covers: {', '.join([cert.standard.code for cert in self.audit.certifications.all()])}"
                )

        # Validate that site belongs to the audit's organization
        # Only validate if audit is available
        if self.site and hasattr(self, "audit") and self.audit:
            if self.site.organization != self.audit.organization:
                errors["site"] = f"Site {self.site.site_name} does not belong to {self.audit.organization.name}."

        if errors:
            raise ValidationError(errors)


class Nonconformity(Finding):
    """
    Nonconformity finding - requires corrective action.

    Can be major or minor. Client can respond with root cause, correction,
    and corrective action. Auditor verifies the response.
    """

    CATEGORY_CHOICES = [
        ("major", "Major"),
        ("minor", "Minor"),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ("open", "Open"),
        ("client_responded", "Client Responded"),
        ("accepted", "Accepted"),
        ("closed", "Closed"),
    ]

    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, help_text="Major or minor nonconformity")
    objective_evidence = models.TextField(help_text="Objective evidence of the nonconformity")
    statement_of_nc = models.TextField(help_text="Statement of the nonconformity")
    auditor_explanation = models.TextField(help_text="Auditor's explanation")

    # Client response fields (editable by client)
    client_root_cause = models.TextField(blank=True, help_text="Client's root cause analysis")
    client_correction = models.TextField(blank=True, help_text="Client's immediate correction")
    client_corrective_action = models.TextField(blank=True, help_text="Client's corrective action plan")
    due_date = models.DateField(null=True, blank=True, help_text="Due date for corrective action")

    # Verification fields
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default="open")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ncs_verified")
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True, help_text="Notes from the auditor during verification")

    # Phase 2: Root cause categorization
    root_cause_categories = models.ManyToManyField(
        "RootCauseCategory",
        blank=True,
        related_name="nonconformities",
        help_text="Root cause categories for systematic analysis",
    )  # type: ignore

    class Meta:
        verbose_name = "Nonconformity"
        verbose_name_plural = "Nonconformities"
        ordering = ["category", "clause", "created_at"]
        indexes = [
            models.Index(fields=["verification_status"]),
            models.Index(fields=["audit", "verification_status"]),
            models.Index(fields=["category", "verification_status"]),
        ]

    def __str__(self):
        """Return string representation of the model instance."""
        return f"{self.get_category_display()} NC - {self.clause} ({self.audit})"


class Observation(Finding):
    """
    Observation finding - informational, no action required.
    """

    statement = models.TextField(help_text="Observation statement")
    explanation = models.TextField(blank=True, help_text="Additional explanation")

    class Meta:
        verbose_name = "Observation"
        verbose_name_plural = "Observations"

    def __str__(self):
        """Return string representation of the model instance."""
        return f"Observation - {self.clause} ({self.audit})"


class OpportunityForImprovement(Finding):
    """
    Opportunity for Improvement finding - suggestion for enhancement.
    """

    description = models.TextField(help_text="Description of the opportunity")

    class Meta:
        verbose_name = "Opportunity for Improvement"
        verbose_name_plural = "Opportunities for Improvement"

    def __str__(self):
        """Return string representation of the model instance."""
        return f"OFI - {self.clause} ({self.audit})"


class AuditRecommendation(models.Model):
    """
    Final recommendations from the audit.

    OneToOne with Audit - each audit has one recommendation record.
    Used by CB Admin to make final decisions.
    """

    audit = models.OneToOneField(Audit, on_delete=models.CASCADE, related_name="recommendation")
    special_audit_required = models.BooleanField(default=False)
    special_audit_details = models.TextField(blank=True, help_text="Details of special audit requirements")
    suspension_recommended = models.BooleanField(default=False)
    suspension_certificates = models.TextField(
        blank=True, help_text="List of certificates to suspend (simple text for now)"
    )
    revocation_recommended = models.BooleanField(default=False)
    revocation_certificates = models.TextField(
        blank=True, help_text="List of certificates to revoke (simple text for now)"
    )
    stage2_required = models.BooleanField(default=False, help_text="Stage 2 audit required")
    decision_notes = models.TextField(blank=True, help_text="Additional decision notes")

    class Meta:
        verbose_name = "Audit Recommendation"
        verbose_name_plural = "Audit Recommendations"

    def __str__(self):
        """Return string representation of the model instance."""
        return f"Recommendation for {self.audit}"


class AuditStatusLog(models.Model):
    """
    Immutable audit trail of status transitions.

    Records every status change for compliance and auditing purposes.
    """

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField(max_length=30, help_text="Previous status")
    to_status = models.CharField(max_length=30, help_text="New status")
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="audit_status_changes")
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Notes about this transition")

    class Meta:
        verbose_name = "Audit Status Log"
        verbose_name_plural = "Audit Status Logs"
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["audit", "-changed_at"]),
        ]

    def __str__(self):
        """Return string representation of the model instance."""
        return f"{self.audit} - {self.from_status} → {self.to_status} ({self.changed_at})"


# ---------------------------------------------------------------------------
# Phase 2A: Complaints & Appeals (ISO 17021-1 Clause 9.8)
# ---------------------------------------------------------------------------


class Complaint(models.Model):
    """Formal complaint management record (ISO 17021-1 Clause 9.8)."""

    COMPLAINT_TYPE_CHOICES = [
        ("audit_conduct", "Audit Conduct"),
        ("auditor_behavior", "Auditor Behavior"),
        ("certification_decision", "Certification Decision"),
        ("certificate_misuse", "Certificate Misuse"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("received", "Received"),
        ("under_investigation", "Under Investigation"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
        ("escalated", "Escalated to Appeal"),
    ]

    complaint_number = models.CharField(max_length=50, unique=True)
    organization = models.ForeignKey(
        "core.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="complaints"
    )
    related_audit = models.ForeignKey(
        Audit, on_delete=models.SET_NULL, null=True, blank=True, related_name="complaints"
    )
    complainant_name = models.CharField(max_length=255)
    complainant_email = models.EmailField(blank=True)
    complaint_type = models.CharField(max_length=40, choices=COMPLAINT_TYPE_CHOICES)
    description = models.TextField(help_text="Detailed description of the complaint")
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="complaints_submitted")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="received")
    assigned_investigator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="complaints_investigating"
    )
    investigation_started_at = models.DateTimeField(null=True, blank=True)
    investigation_notes = models.TextField(blank=True)
    investigation_completed_at = models.DateTimeField(null=True, blank=True)
    resolution_details = models.TextField(blank=True)
    corrective_actions = models.TextField(blank=True)

    class Meta:
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["complaint_number"]),
        ]

    def __str__(self):
        return f"Complaint {self.complaint_number} ({self.get_status_display()})"


class Appeal(models.Model):
    """Appeal against a certification decision or complaint resolution."""

    APPEAL_STATUS_CHOICES = [
        ("received", "Received"),
        ("panel_review", "Panel Review"),
        ("decided", "Decided"),
        ("closed", "Closed"),
    ]

    appeal_number = models.CharField(max_length=50, unique=True)
    related_complaint = models.ForeignKey(
        Complaint, on_delete=models.SET_NULL, null=True, blank=True, related_name="appeals"
    )
    related_decision = models.ForeignKey(
        "CertificationDecision", on_delete=models.SET_NULL, null=True, blank=True, related_name="appeals"
    )
    appellant_name = models.CharField(max_length=255)
    appellant_email = models.EmailField(blank=True)
    grounds = models.TextField(help_text="Grounds for appeal")
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="appeals_submitted")
    status = models.CharField(max_length=30, choices=APPEAL_STATUS_CHOICES, default="received")
    panel_members = models.ManyToManyField(User, related_name="appeal_panels", blank=True)
    panel_decision = models.CharField(
        max_length=30,
        choices=[("upheld", "Upheld"), ("rejected", "Rejected"), ("partially_upheld", "Partially Upheld")],
        blank=True,
    )
    panel_decision_date = models.DateTimeField(null=True, blank=True)
    panel_justification = models.TextField(blank=True)

    class Meta:
        verbose_name = "Appeal"
        verbose_name_plural = "Appeals"
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["appeal_number"]),
        ]

    def __str__(self):
        return f"Appeal {self.appeal_number} ({self.get_status_display()})"


class TechnicalReview(models.Model):
    """
    Technical review before certification decision (ISO 17021-1 Clause 9.5).

    Mandatory gate before certification decision. Ensures audit report meets
    requirements defined in ISO 17021-1 Clause 9.4.8.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("requires_clarification", "Requires Clarification"),
        ("rejected", "Rejected"),
    ]

    audit = models.OneToOneField(Audit, on_delete=models.CASCADE, related_name="technical_review")
    reviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="technical_reviews_conducted",
        help_text="CB staff member conducting technical review",
    )
    reviewed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")

    # ISO 17021-1 Clause 9.4.8 requirements checklist
    scope_verified = models.BooleanField(default=False, help_text="Audit scope clearly defined and verified")
    objectives_verified = models.BooleanField(default=False, help_text="Audit objectives met")
    findings_reviewed = models.BooleanField(default=False, help_text="All findings reviewed and properly documented")
    conclusion_clear = models.BooleanField(default=False, help_text="Audit conclusion is clear and justified")

    reviewer_notes = models.TextField(blank=True, help_text="Technical reviewer's notes")
    clarification_requested = models.TextField(blank=True, help_text="Clarifications requested from audit team")

    class Meta:
        verbose_name = "Technical Review"
        verbose_name_plural = "Technical Reviews"

    def __str__(self):
        """Return string representation of the model instance."""
        return f"Technical Review for {self.audit} - {self.get_status_display()}"


class CertificationDecision(models.Model):
    """
    Final certification decision (ISO 17021-1 separation of duties).

    Decision maker must be independent from the audit team.
    """

    DECISION_CHOICES = [
        ("grant", "Grant Certification"),
        ("refuse", "Refuse Certification"),
        ("suspend", "Suspend Certification"),
        ("withdraw", "Withdraw Certification"),
        ("special_audit", "Require Special Audit"),
    ]

    audit = models.OneToOneField(Audit, on_delete=models.CASCADE, related_name="certification_decision")
    decision_maker = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="certification_decisions_made",
        help_text="Person making final certification decision",
    )
    decided_at = models.DateTimeField(auto_now_add=True)
    decision = models.CharField(max_length=30, choices=DECISION_CHOICES, help_text="Final certification decision")
    decision_notes = models.TextField(help_text="Justification for the decision")

    # Link to affected certifications
    certifications_affected = models.ManyToManyField(
        "core.Certification",
        related_name="certification_decisions",
        help_text="Certifications affected by this decision",
    )

    class Meta:
        verbose_name = "Certification Decision"
        verbose_name_plural = "Certification Decisions"

    def __str__(self):
        """Return string representation of the model instance."""
        return f"Decision for {self.audit} - {self.get_decision_display()}"


# ---------------------------------------------------------------------------
# Phase 2B: Remote Audit & Transfer Certification & Pre-Audit Docs
# ---------------------------------------------------------------------------


class RemoteAuditLog(models.Model):
    """IAF MD4: Track remote audit ICT-enabled activities."""

    ACTIVITY_TYPE_CHOICES = [
        ("video_conference", "Video Conference"),
        ("document_review_remote", "Remote Document Review"),
        ("screen_sharing", "Screen Sharing"),
        ("remote_access", "Remote System Access"),
        ("electronic_signature", "Electronic Signature"),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="remote_logs")
    activity_type = models.CharField(max_length=40, choices=ACTIVITY_TYPE_CHOICES)
    auditor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="remote_audit_activities")
    client_participants = models.TextField(blank=True, help_text="Names/roles of client participants")
    platform_used = models.CharField(max_length=100, help_text="Technology platform (Zoom/Teams/WebEx/etc.)")
    session_start = models.DateTimeField()
    session_end = models.DateTimeField()
    technology_validated = models.BooleanField(default=False)
    security_controls_verified = models.BooleanField(default=False)
    data_protection_confirmed = models.BooleanField(default=False)
    session_notes = models.TextField(blank=True)
    technical_issues = models.TextField(blank=True)
    recording_file = models.FileField(upload_to="remote_audit_recordings/", blank=True)
    site_visit_complement = models.BooleanField(
        default=False, help_text="Was an on-site component also performed as complement?"
    )

    class Meta:
        verbose_name = "Remote Audit Log"
        verbose_name_plural = "Remote Audit Logs"
        ordering = ["-session_start"]
        indexes = [
            models.Index(fields=["audit", "session_start"]),
        ]

    def __str__(self):
        return f"Remote session {self.session_start} ({self.audit})"


class TransferCertification(models.Model):
    """IAF MD17: Transfer certification from previous CB."""

    transfer_audit = models.OneToOneField(
        Audit,
        on_delete=models.CASCADE,
        related_name="transfer_certification",
        limit_choices_to={"audit_type": "transfer"},
    )
    previous_cb_name = models.CharField(max_length=255)
    previous_cb_accreditation_body = models.CharField(max_length=255, blank=True)
    previous_certificate_number = models.CharField(max_length=100, blank=True)
    previous_certificate_issue_date = models.DateField(null=True, blank=True)
    previous_certificate_expiry_date = models.DateField(null=True, blank=True)
    reason_for_transfer = models.TextField(blank=True)
    previous_audit_reports_received = models.BooleanField(default=False)
    previous_nc_records_received = models.BooleanField(default=False)
    previous_surveillance_history_received = models.BooleanField(default=False)
    previous_certificate_file = models.FileField(upload_to="transfer_certificates/", blank=True)
    previous_audit_reports = models.FileField(upload_to="transfer_previous_reports/", blank=True)
    transfer_date_before_expiry = models.BooleanField(default=False)
    no_expiry_extension_applied = models.BooleanField(default=False)
    transfer_approved = models.BooleanField(null=True)
    transfer_approval_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Transfer Certification"
        verbose_name_plural = "Transfer Certifications"
        ordering = ["-previous_certificate_expiry_date"]

    def __str__(self):
        return f"Transfer for audit {self.transfer_audit_id} from {self.previous_cb_name}"


class PreAuditDocumentSubmission(models.Model):
    """Client provided documents prior to audit execution."""

    DOCUMENT_TYPE_CHOICES = [
        ("quality_manual", "Quality Manual"),
        ("procedure", "Procedure"),
        ("work_instruction", "Work Instruction"),
        ("record", "Record/Form"),
        ("org_chart", "Organization Chart"),
        ("scope_statement", "Scope Statement"),
        ("other", "Other"),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="pre_audit_documents")
    document_type = models.CharField(max_length=40, choices=DOCUMENT_TYPE_CHOICES)
    document_file = models.FileField(upload_to="pre_audit_docs/")
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="pre_audit_docs_uploaded")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_by_auditor = models.BooleanField(default=False)
    reviewer_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Pre-Audit Document Submission"
        verbose_name_plural = "Pre-Audit Document Submissions"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["audit", "uploaded_at"]),
        ]

    def __str__(self):
        return f"Pre-audit doc {self.get_document_type_display()} ({self.audit})"


class EvidenceFile(models.Model):
    """
    File attachment for audits or findings.

    Can be attached to an audit (general evidence) or to a specific
    nonconformity (evidence of the NC or of corrective action).
    """

    EVIDENCE_TYPE_CHOICES = [
        ("document", "Document Review"),
        ("interview", "Interview Notes"),
        ("observation", "Direct Observation"),
        ("record", "Record Examination"),
        ("photo", "Photographic Evidence"),
        ("other", "Other"),
    ]

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="evidence_files")
    finding = models.ForeignKey(
        Nonconformity,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="evidence_files",
        help_text="Optional: link to a specific nonconformity",
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="files_uploaded")
    file = models.FileField(upload_to="evidence/%Y/%m/%d/", help_text="Upload evidence file")
    evidence_type = models.CharField(
        max_length=20,
        choices=EVIDENCE_TYPE_CHOICES,
        default="document",
        help_text="Type of audit evidence",
    )
    description = models.TextField(blank=True, help_text="Description of the evidence")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # GDPR/Retention policy (Board approved 7 years default)
    retention_years = models.PositiveIntegerField(default=7, help_text="Number of years to retain this evidence")
    purge_after = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this evidence should be purged (auto-calculated)",
    )

    class Meta:
        verbose_name = "Evidence File"
        verbose_name_plural = "Evidence Files"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["purge_after"]),
        ]

    def __str__(self):
        """Return string representation of the model instance."""
        if self.finding:
            return f"Evidence for NC {self.finding.clause} ({self.audit})"
        return f"Evidence for {self.audit}"

    def clean(self):
        """Validate file uploads."""
        import os

        from django.core.exceptions import ValidationError

        if self.file:
            # Validate file size (10MB max)
            max_size = 10 * 1024 * 1024  # 10MB in bytes
            if self.file.size > max_size:
                raise ValidationError(
                    {"file": f"File size must not exceed 10MB. Current size: {self.file.size / (1024 * 1024):.2f}MB"}
                )

            # Validate file type
            allowed_extensions = [
                ".pdf",
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
                ".txt",
                ".csv",
            ]
            file_ext = os.path.splitext(self.file.name)[1].lower()
            if file_ext not in allowed_extensions:
                raise ValidationError(
                    {
                        "file": (
                            f'File type "{file_ext}" not allowed. Allowed types: PDF, images '
                            "(jpg/png/gif), Office documents (docx/xlsx/pptx), text files."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        """Auto-calculate purge_after date based on retention policy."""
        if not self.purge_after and self.uploaded_at:
            from datetime import timedelta

            from django.utils import timezone

            upload_date = self.uploaded_at if self.uploaded_at else timezone.now()
            self.purge_after = upload_date.date() + timedelta(days=365 * self.retention_years)

        super().save(*args, **kwargs)


# ============================================================================
# PHASE 2 MODELS: Root Cause Analysis & Competence Tracking
# ============================================================================


class RootCauseCategory(models.Model):
    """
    Hierarchical categorization of root causes for systematic analysis.

    Enables trending and pattern recognition across audits.
    Examples: "Resource inadequacy", "Training deficiency", "Process design flaw"
    """

    name = models.CharField(max_length=255, help_text="Category name (e.g., 'Resource inadequacy')")
    code = models.CharField(max_length=50, unique=True, help_text="Unique code for this category (e.g., 'RC-001')")
    description = models.TextField(blank=True, help_text="Detailed description of this root cause category")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
        help_text="Parent category for hierarchical organization",
    )
    is_active = models.BooleanField(default=True, help_text="Whether this category is currently in use")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Root Cause Category"
        verbose_name_plural = "Root Cause Categories"
        ordering = ["code", "name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        """Return string representation of the model instance."""
        if self.parent:
            return f"{self.parent.code} > {self.code}: {self.name}"
        return f"{self.code}: {self.name}"


class FindingRecurrence(models.Model):
    """
    Track recurring findings across multiple audits.

    Helps identify systemic issues and evaluate effectiveness of corrective actions.
    Linked to Nonconformity findings to track resolution patterns.
    """

    finding = models.OneToOneField(
        Nonconformity,
        on_delete=models.CASCADE,
        related_name="recurrence_data",
        help_text="The finding this recurrence data relates to",
    )
    recurrence_count = models.PositiveIntegerField(default=1, help_text="Number of times this issue has recurred")
    first_occurrence = models.DateField(help_text="Date of first occurrence of this finding")
    last_occurrence = models.DateField(help_text="Date of most recent occurrence")
    previous_audits = models.TextField(blank=True, help_text="References to previous audits where this issue was found")
    corrective_actions_effective = models.BooleanField(
        default=False, help_text="Whether previous corrective actions were effective"
    )
    resolution_notes = models.TextField(blank=True, help_text="Notes on resolution attempts and outcomes")
    escalation_required = models.BooleanField(
        default=False, help_text="Flag for findings requiring management attention"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Finding Recurrence"
        verbose_name_plural = "Finding Recurrences"
        ordering = ["-recurrence_count", "-last_occurrence"]
        indexes = [
            models.Index(fields=["recurrence_count"]),
            models.Index(fields=["escalation_required"]),
        ]

    def __str__(self):
        """Return string representation of the model instance."""
        return f"Recurrence data for {self.finding} ({self.recurrence_count}x)"


class AuditorCompetenceWarning(models.Model):
    """
    Track competence-related warnings for auditors during audit planning.

    Implements IAF MD1 requirements for auditor competence verification.
    Helps prevent assignment of auditors without required qualifications.
    """

    WARNING_TYPE_CHOICES = [
        ("scope_mismatch", "Scope Mismatch"),
        ("insufficient_experience", "Insufficient Experience"),
        ("expired_qualification", "Expired Qualification"),
        ("language_barrier", "Language Barrier"),
        ("conflict_of_interest", "Conflict of Interest"),
        ("other", "Other"),
    ]

    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    audit = models.ForeignKey(
        Audit,
        on_delete=models.CASCADE,
        related_name="competence_warnings",
        help_text="Audit this warning relates to",
    )
    auditor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="competence_warnings_received",
        help_text="Auditor this warning is about",
    )
    warning_type = models.CharField(max_length=30, choices=WARNING_TYPE_CHOICES, help_text="Type of competence warning")
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default="medium",
        help_text="Severity level of the warning",
    )
    description = models.TextField(help_text="Detailed description of the competence issue")
    issued_at = models.DateTimeField(auto_now_add=True, help_text="When this warning was issued")
    issued_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="competence_warnings_issued",
        help_text="CB staff member who issued this warning",
    )
    resolved_at = models.DateTimeField(null=True, blank=True, help_text="When this warning was resolved")
    resolution_notes = models.TextField(blank=True, help_text="How this warning was resolved")
    acknowledged_by_auditor = models.BooleanField(
        default=False, help_text="Whether the auditor has acknowledged this warning"
    )

    class Meta:
        verbose_name = "Auditor Competence Warning"
        verbose_name_plural = "Auditor Competence Warnings"
        ordering = ["-issued_at", "-severity"]
        indexes = [
            models.Index(fields=["audit", "auditor"]),
            models.Index(fields=["severity"]),
            models.Index(fields=["resolved_at"]),
        ]

    def __str__(self):
        """Return string representation of the model instance."""
        return f"{self.get_warning_type_display()} - {self.auditor} ({self.audit})"

    def is_resolved(self):
        """Check if this warning has been resolved."""
        return self.resolved_at is not None
