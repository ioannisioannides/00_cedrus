from django.contrib.auth.models import User
from django.db import models


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
        "audit_management.Audit", on_delete=models.SET_NULL, null=True, blank=True, related_name="complaints"
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
        db_table = "audits_complaint"

    def __str__(self):
        return f"Complaint {self.complaint_number} ({self.get_status_display()})"


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

    audit = models.OneToOneField(
        "audit_management.Audit", on_delete=models.CASCADE, related_name="certification_decision"
    )
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
        db_table = "audits_certificationdecision"

    def __str__(self):
        """Return string representation of the model instance."""
        return f"Decision for {self.audit} - {self.get_decision_display()}"


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
        CertificationDecision, on_delete=models.SET_NULL, null=True, blank=True, related_name="appeals"
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
        db_table = "audits_appeal"

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

    audit = models.OneToOneField("audit_management.Audit", on_delete=models.CASCADE, related_name="technical_review")
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
        db_table = "audits_technicalreview"

    def __str__(self):
        """Return string representation of the model instance."""
        return f"Technical Review for {self.audit} - {self.get_status_display()}"


class TransferCertification(models.Model):
    """IAF MD17: Transfer certification from previous CB."""

    transfer_audit = models.OneToOneField(
        "audit_management.Audit",
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
        db_table = "audits_transfercertification"

    def __str__(self):
        return f"Transfer for audit {self.transfer_audit_id} from {self.previous_cb_name}"
