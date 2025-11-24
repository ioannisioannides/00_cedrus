"""
Core app models for organizations, sites, standards, and certifications.

These models form the foundation of the platform - the entities that audits
are performed on and the standards/certifications they hold.
"""

from django.core.validators import MinValueValidator
from django.db import models


class Organization(models.Model):
    """
    Client organization (company) that can be certified.

    This is the main entity - all sites, certifications, and audits belong to
    an organization.
    """

    name = models.CharField(max_length=255, help_text="Official company name")
    registered_id = models.CharField(
        max_length=100, blank=True, help_text="Company registration number"
    )
    registered_address = models.TextField(help_text="Registered business address")
    customer_id = models.CharField(
        max_length=50, unique=True, help_text="Internal customer reference number"
    )
    total_employee_count = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], help_text="Total number of employees across all sites"
    )

    # Contact information
    contact_telephone = models.CharField(max_length=50, blank=True)
    contact_fax = models.CharField(max_length=50, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_website = models.URLField(blank=True)

    # Signatory (person authorized to sign contracts/certificates)
    signatory_name = models.CharField(max_length=255, blank=True)
    signatory_title = models.CharField(max_length=255, blank=True)

    # Management System Representative
    ms_representative_name = models.CharField(
        max_length=255, blank=True, help_text="Management System Representative name"
    )
    ms_representative_title = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.customer_id})"


class Site(models.Model):
    """
    Physical location or site belonging to an organization.

    Organizations can have multiple sites, each potentially with different
    scopes or employee counts. Sites are linked to audits.
    """

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="sites")
    site_name = models.CharField(max_length=255, help_text="Name of the site/location")
    site_address = models.TextField(help_text="Physical address of the site")
    site_employee_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Number of employees at this site (optional)",
    )
    site_scope_override = models.TextField(
        blank=True, help_text="Optional scope description specific to this site"
    )
    active = models.BooleanField(default=True, help_text="Whether this site is currently active")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        ordering = ["organization", "site_name"]

    def __str__(self):
        return f"{self.site_name} ({self.organization.name})"


class Standard(models.Model):
    """
    Management system standard (e.g., ISO 9001:2015, ISO 14001:2015).

    Standards are reference data - they define what certifications are based on.
    """

    code = models.CharField(
        max_length=100, unique=True, help_text="Standard code (e.g., 'ISO 9001:2015')"
    )
    title = models.CharField(max_length=255, help_text="Full title of the standard")
    nace_code = models.CharField(max_length=50, blank=True, help_text="NACE classification code")
    ea_code = models.CharField(
        max_length=50, blank=True, help_text="EA (European Accreditation) code"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Standard"
        verbose_name_plural = "Standards"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.title}"


class Certification(models.Model):
    """
    Certification held by an organization for a specific standard.

    An organization can have multiple certifications (e.g., ISO 9001, ISO 14001).
    Certifications are linked to audits.
    """

    CERTIFICATE_STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("suspended", "Suspended"),
        ("withdrawn", "Withdrawn"),
        ("expired", "Expired"),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="certifications"
    )
    standard = models.ForeignKey(Standard, on_delete=models.PROTECT, related_name="certifications")
    certification_scope = models.TextField(help_text="Scope of the certification")
    certificate_id = models.CharField(
        max_length=100, blank=True, help_text="Certificate number/reference"
    )
    certificate_status = models.CharField(
        max_length=20, choices=CERTIFICATE_STATUS_CHOICES, default="draft"
    )
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Certification"
        verbose_name_plural = "Certifications"
        ordering = ["organization", "standard"]
        unique_together = [["organization", "standard"]]

    def __str__(self):
        return f"{self.organization.name} - {self.standard.code} ({self.certificate_status})"


# ---------------------------------------------------------------------------
# Phase 2A: Certificate Lifecycle Tracking (History & Surveillance Schedule)
# ---------------------------------------------------------------------------

class CertificateHistory(models.Model):
    """Immutable record of certificate lifecycle actions (issue, renew, suspend, etc.)."""

    ACTION_CHOICES = [
        ("issued", "Certificate Issued"),
        ("renewed", "Certificate Renewed"),
        ("surveillance_passed", "Surveillance Audit Passed"),
        ("suspended", "Certificate Suspended"),
        ("suspension_lifted", "Suspension Lifted"),
        ("withdrawn", "Certificate Withdrawn"),
        ("expired", "Certificate Expired"),
        ("scope_extended", "Scope Extended"),
        ("scope_reduced", "Scope Reduced"),
        ("transfer_in", "Transferred In"),
        ("transfer_out", "Transferred Out"),
    ]

    certification = models.ForeignKey(
        Certification, on_delete=models.CASCADE, related_name="history"
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    action_date = models.DateField()
    related_audit = models.ForeignKey(
        "audits.Audit", on_delete=models.SET_NULL, null=True, blank=True, related_name="certificate_history_entries"
    )
    related_decision = models.ForeignKey(
        "audits.CertificationDecision", on_delete=models.SET_NULL, null=True, blank=True, related_name="certificate_history_entries"
    )
    certificate_number_snapshot = models.CharField(max_length=100, blank=True)
    certification_scope_snapshot = models.TextField(blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    action_by = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, related_name="certificate_history_actions"
    )
    action_reason = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Certificate History"
        verbose_name_plural = "Certificate History Entries"
        ordering = ["-action_date", "-created_at"]
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["action_date"]),
        ]

    def __str__(self):
        return f"{self.certification} {self.action} ({self.action_date})"


class SurveillanceSchedule(models.Model):
    """Track 3-year certification cycle surveillance and recertification milestones."""

    certification = models.OneToOneField(
        Certification, on_delete=models.CASCADE, related_name="surveillance_schedule"
    )
    cycle_start = models.DateField(help_text="Certification cycle start (Stage 2 decision date)")
    cycle_end = models.DateField(help_text="Certification cycle end (3 years from start)")
    surveillance_1_due_date = models.DateField()
    surveillance_2_due_date = models.DateField()
    recertification_due_date = models.DateField()
    surveillance_1_audit = models.ForeignKey(
        "audits.Audit", on_delete=models.SET_NULL, null=True, blank=True, related_name="surveillance_1_for"
    )
    surveillance_2_audit = models.ForeignKey(
        "audits.Audit", on_delete=models.SET_NULL, null=True, blank=True, related_name="surveillance_2_for"
    )
    recertification_audit = models.ForeignKey(
        "audits.Audit", on_delete=models.SET_NULL, null=True, blank=True, related_name="recertification_for"
    )
    surveillance_1_completed = models.BooleanField(default=False)
    surveillance_2_completed = models.BooleanField(default=False)
    recertification_completed = models.BooleanField(default=False)
    overdue_alert_sent = models.BooleanField(default=False)
    expiry_warning_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Surveillance Schedule"
        verbose_name_plural = "Surveillance Schedules"
        ordering = ["-cycle_start"]

    def __str__(self):
        return f"Surveillance schedule for {self.certification}" 
