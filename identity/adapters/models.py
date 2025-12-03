"""
Identity domain models (formerly accounts).

We use Django's built-in Group system for roles:
- cb_admin: Certification Body administrators
- lead_auditor: Lead auditors who can manage audits
- auditor: Regular auditors
- client_admin: Client organization administrators
- client_user: Regular client users

The Profile model extends User with organization membership and convenience
methods to check role membership.
"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """
    Extended user profile with organization membership.

    For CB admins, organization can be None as they manage multiple organizations.
    For auditors, organization is typically None (they work for the CB).
    For client users, organization links them to their company.
    """

    user: models.OneToOneField = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    organization: models.ForeignKey = models.ForeignKey(
        "core.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
        help_text="Organization this user belongs to. Null for CB admins and auditors.",
    )

    # Convenience flags (can be used alongside Groups for quick checks)
    # These are computed properties, not stored fields, to avoid duplication
    # We'll use Groups as the source of truth

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ["user__last_name", "user__first_name"]
        db_table = "accounts_profile"  # Preserve existing table name

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.organization or 'No Org'})"

    def is_cb_admin(self):
        """Check if user is in the cb_admin group."""
        return self.user.groups.filter(name="cb_admin").exists()

    def is_lead_auditor(self):
        """Check if user is in the lead_auditor group."""
        return self.user.groups.filter(name="lead_auditor").exists()

    def is_auditor(self):
        """Check if user is an auditor (lead_auditor or auditor group)."""
        return self.user.groups.filter(name__in=["lead_auditor", "auditor"]).exists()

    def is_client_admin(self):
        """Check if user is in the client_admin group."""
        return self.user.groups.filter(name="client_admin").exists()

    def is_client_user(self):
        """Check if user is a client user (client_admin or client_user group)."""
        return self.user.groups.filter(name__in=["client_admin", "client_user"]).exists()

    def is_technical_reviewer(self):
        """Check if user is in the technical_reviewer group."""
        return self.user.groups.filter(name="technical_reviewer").exists()

    def is_decision_maker(self):
        """Check if user is in the decision_maker group."""
        return self.user.groups.filter(name="decision_maker").exists()

    def get_role_display(self):
        """Get a human-readable role name."""
        if self.is_cb_admin():
            return "CB Admin"
        if self.is_lead_auditor():
            return "Lead Auditor"
        if self.user.groups.filter(name="auditor").exists():
            return "Auditor"
        if self.is_technical_reviewer():
            return "Technical Reviewer"
        if self.is_decision_maker():
            return "Decision Maker"
        if self.is_client_admin():
            return "Client Admin"
        if self.user.groups.filter(name="client_user").exists():
            return "Client User"
        return "No Role"


# ---------------------------------------------------------------------------
# Phase 2A: Auditor Competence & Impartiality (ISO 17021-1 Clause 7 & 5.2)
# ---------------------------------------------------------------------------


class AuditorQualification(models.Model):
    """Formal auditor qualification / certification record."""

    QUALIFICATION_TYPE_CHOICES = [
        ("lead_auditor_cert", "Lead Auditor Certificate"),
        ("auditor_cert", "Auditor Certificate"),
        ("technical_expert_cert", "Technical Expert Certificate"),
        ("sector_qualification", "Sector-Specific Qualification"),
        ("language_cert", "Language Certification"),
    ]

    auditor: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE, related_name="qualifications")
    qualification_type: models.CharField = models.CharField(max_length=40, choices=QUALIFICATION_TYPE_CHOICES)
    issuing_body: models.CharField = models.CharField(max_length=255)
    certificate_number: models.CharField = models.CharField(max_length=100)
    issue_date: models.DateField = models.DateField()
    expiry_date: models.DateField = models.DateField(null=True, blank=True)
    standards: models.ManyToManyField = models.ManyToManyField(
        "core.Standard", blank=True, related_name="auditor_qualifications"
    )
    nace_codes: models.CharField = models.CharField(
        max_length=255, blank=True, help_text="Comma-separated NACE codes for sector competence"
    )
    ea_codes: models.CharField = models.CharField(
        max_length=255, blank=True, help_text="Comma-separated EA codes for sector competence"
    )
    certificate_file: models.FileField = models.FileField(upload_to="auditor_qualifications/", blank=True)
    status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("expired", "Expired"),
            ("suspended", "Suspended"),
            ("withdrawn", "Withdrawn"),
        ],
        default="active",
    )
    notes: models.TextField = models.TextField(blank=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Auditor Qualification"
        verbose_name_plural = "Auditor Qualifications"
        ordering = ["auditor", "-issue_date"]
        indexes = [models.Index(fields=["status"])]
        db_table = "accounts_auditorqualification"

    def __str__(self):
        return f"{self.auditor.username} - {self.get_qualification_type_display()}"


class AuditorTrainingRecord(models.Model):
    """Continuing professional development and training records."""

    auditor: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE, related_name="training_records")
    course_title: models.CharField = models.CharField(max_length=255)
    training_provider: models.CharField = models.CharField(max_length=255)
    course_date: models.DateField = models.DateField()
    duration_hours: models.FloatField = models.FloatField(null=True, blank=True)
    standards_covered: models.ManyToManyField = models.ManyToManyField(
        "core.Standard", blank=True, related_name="training_records"
    )
    cpd_points: models.FloatField = models.FloatField(
        default=0.0, help_text="Continuing Professional Development points"
    )
    certificate_file: models.FileField = models.FileField(upload_to="training_certificates/", blank=True)
    notes: models.TextField = models.TextField(blank=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Auditor Training Record"
        verbose_name_plural = "Auditor Training Records"
        ordering = ["-course_date"]
        db_table = "accounts_auditortrainingrecord"

    def __str__(self):
        return f"Training: {self.course_title} ({self.auditor.username})"


class AuditorCompetenceEvaluation(models.Model):
    """Annual competence evaluation (witness audits, scoring)."""

    auditor: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="competence_evaluations"
    )
    evaluation_date: models.DateField = models.DateField()
    evaluator: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="evaluations_conducted"
    )
    technical_knowledge_score: models.PositiveIntegerField = models.PositiveIntegerField()
    audit_skills_score: models.PositiveIntegerField = models.PositiveIntegerField()
    communication_skills_score: models.PositiveIntegerField = models.PositiveIntegerField()
    report_writing_score: models.PositiveIntegerField = models.PositiveIntegerField()
    witness_audit_date: models.DateField = models.DateField(null=True, blank=True)
    witness_audit_observer: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="witness_audits_observed"
    )
    witness_audit_notes: models.TextField = models.TextField(blank=True)
    overall_assessment: models.CharField = models.CharField(
        max_length=30,
        choices=[
            ("exceeds", "Exceeds Requirements"),
            ("meets", "Meets Requirements"),
            ("development_needed", "Development Needed"),
            ("unsatisfactory", "Unsatisfactory"),
        ],
    )
    development_plan: models.TextField = models.TextField(blank=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Auditor Competence Evaluation"
        verbose_name_plural = "Auditor Competence Evaluations"
        ordering = ["-evaluation_date"]
        db_table = "accounts_auditorcompetenceevaluation"

    def __str__(self):
        return f"Competence Eval {self.auditor.username} {self.evaluation_date}"


class ConflictOfInterest(models.Model):
    """Declared relationships that may pose impartiality risks."""

    RELATIONSHIP_TYPE_CHOICES = [
        ("former_employee", "Former Employee"),
        ("consultant", "Consultant / Advisory"),
        ("family_member", "Family Member Employed"),
        ("financial_interest", "Financial Interest"),
        ("competing_business", "Competing Business"),
        ("other", "Other"),
    ]

    auditor: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conflicts_of_interest")
    organization: models.ForeignKey = models.ForeignKey(
        "core.Organization", on_delete=models.CASCADE, related_name="conflicts_declared"
    )
    relationship_type: models.CharField = models.CharField(max_length=40, choices=RELATIONSHIP_TYPE_CHOICES)
    description: models.TextField = models.TextField()
    declared_date: models.DateField = models.DateField(auto_now_add=True)
    relationship_start_date: models.DateField = models.DateField(null=True, blank=True)
    relationship_end_date: models.DateField = models.DateField(null=True, blank=True)
    impartiality_risk: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High - Assignment Prohibited"),
        ],
        default="low",
    )
    mitigation_measures: models.TextField = models.TextField(blank=True)
    approved_by: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="coi_approvals"
    )
    is_active: models.BooleanField = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Conflict of Interest"
        verbose_name_plural = "Conflicts of Interest"
        ordering = ["-declared_date"]
        indexes = [models.Index(fields=["impartiality_risk"])]
        db_table = "accounts_conflictofinterest"

    def __str__(self):
        return f"COI {self.auditor.username} → {self.organization.name} ({self.get_impartiality_risk_display()})"


class ImpartialityDeclaration(models.Model):
    """Annual impartiality declaration by personnel (ISO 17021-1 Clause 5)."""

    user: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="impartiality_declarations"
    )
    declaration_period_year: models.PositiveIntegerField = models.PositiveIntegerField()
    declaration_date: models.DateField = models.DateField(auto_now_add=True)
    no_conflicts_declared: models.BooleanField = models.BooleanField(default=False)
    conflicts_detailed: models.TextField = models.TextField(blank=True)
    declaration_accepted: models.BooleanField = models.BooleanField(default=False)
    reviewed_by: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="impartiality_reviews"
    )

    class Meta:
        verbose_name = "Impartiality Declaration"
        verbose_name_plural = "Impartiality Declarations"
        ordering = ["-declaration_date"]
        unique_together = ["user", "declaration_period_year"]
        db_table = "accounts_impartialitydeclaration"

    def __str__(self):
        return f"Impartiality {self.user.username} {self.declaration_period_year}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """Automatically create a profile when a user is created."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Save the profile when the user is saved."""
    if hasattr(instance, "profile"):
        instance.profile.save()
