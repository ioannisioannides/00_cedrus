"""
Accounts app models for user profiles and role management.

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

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    organization = models.ForeignKey(
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

    def __str__(self):
        return (
            f"{self.user.get_full_name() or self.user.username} ({self.organization or 'No Org'})"
        )

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

    def get_role_display(self):
        """Get a human-readable role name."""
        if self.is_cb_admin():
            return "CB Admin"
        elif self.is_lead_auditor():
            return "Lead Auditor"
        elif self.user.groups.filter(name="auditor").exists():
            return "Auditor"
        elif self.is_client_admin():
            return "Client Admin"
        elif self.user.groups.filter(name="client_user").exists():
            return "Client User"
        return "No Role"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a profile when a user is created."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the profile when the user is saved."""
    if hasattr(instance, "profile"):
        instance.profile.save()
