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
