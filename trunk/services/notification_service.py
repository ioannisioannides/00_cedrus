"""
Email notification service for the Cedrus platform.

Sends transactional emails triggered by audit lifecycle events.
Uses Django's email subsystem (SMTP or console backend).
"""

import logging

from django.apps import apps
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending audit-lifecycle email notifications.

    All methods accept event payloads (dicts) and resolve the necessary
    model instances internally. Failures are logged but never propagated
    so they cannot break the main workflow.
    """

    # ------------------------------------------------------------------
    # Audit notifications
    # ------------------------------------------------------------------

    @staticmethod
    def notify_audit_assigned(payload: dict) -> None:
        """Notify the lead auditor that they have been assigned to an audit."""
        audit_id = payload.get("audit_id")
        if not audit_id:
            return

        Audit = apps.get_model("audit_management", "Audit")
        try:
            audit = Audit.objects.select_related("organization", "lead_auditor").get(id=audit_id)
        except Audit.DoesNotExist:
            logger.error("Audit %s not found for notification", audit_id)
            return

        if not audit.lead_auditor or not audit.lead_auditor.email:
            logger.info("Audit %s has no lead auditor email — skipping notification", audit_id)
            return

        context = {
            "audit": audit,
            "recipient": audit.lead_auditor,
            "site_url": getattr(settings, "SITE_URL", ""),
        }
        _send_notification(
            recipient_email=audit.lead_auditor.email,
            subject=f"Audit assigned: {audit.organization.name} – {audit.get_audit_type_display()}",
            template="notifications/audit_assigned.html",
            context=context,
        )

    @staticmethod
    def notify_audit_status_changed(payload: dict) -> None:
        """Notify relevant parties when an audit changes status."""
        audit_id = payload.get("audit_id")
        new_status = payload.get("new_status")
        if not audit_id or not new_status:
            return

        Audit = apps.get_model("audit_management", "Audit")
        try:
            audit = Audit.objects.select_related("organization", "lead_auditor", "created_by").get(id=audit_id)
        except Audit.DoesNotExist:
            logger.error("Audit %s not found for notification", audit_id)
            return

        # Collect all recipients (deduplicated)
        recipients = set()
        if audit.lead_auditor and audit.lead_auditor.email:
            recipients.add(audit.lead_auditor.email)
        if audit.created_by and audit.created_by.email:
            recipients.add(audit.created_by.email)

        if not recipients:
            return

        context = {
            "audit": audit,
            "new_status": audit.get_status_display(),
            "site_url": getattr(settings, "SITE_URL", ""),
        }
        for email in recipients:
            _send_notification(
                recipient_email=email,
                subject=f"Audit status update: {audit.organization.name} → {audit.get_status_display()}",
                template="notifications/audit_status_changed.html",
                context=context,
            )

    # ------------------------------------------------------------------
    # Finding notifications
    # ------------------------------------------------------------------

    @staticmethod
    def notify_nc_raised(payload: dict) -> None:
        """Notify the client when a nonconformity is raised against their audit."""
        nc_id = payload.get("nc_id") or payload.get("finding_id")
        if not nc_id:
            return

        Nonconformity = apps.get_model("audit_management", "Nonconformity")
        try:
            nc = Nonconformity.objects.select_related("audit__organization", "standard").get(id=nc_id)
        except Nonconformity.DoesNotExist:
            return

        # Find client contacts for the organization
        Profile = apps.get_model("identity", "Profile")
        client_emails = list(
            Profile.objects.filter(
                organization=nc.audit.organization,
                user__groups__name__in=["client_admin", "client_user"],
                user__email__gt="",
            )
            .values_list("user__email", flat=True)
            .distinct()
        )

        if not client_emails:
            return

        context = {
            "nc": nc,
            "audit": nc.audit,
            "site_url": getattr(settings, "SITE_URL", ""),
        }
        for email in client_emails:
            _send_notification(
                recipient_email=email,
                subject=f"Nonconformity raised: {nc.get_category_display()} NC – Clause {nc.clause}",
                template="notifications/nc_raised.html",
                context=context,
            )

    @staticmethod
    def notify_nc_response_required(payload: dict) -> None:
        """Remind the client that a corrective action response is overdue."""
        nc_id = payload.get("nc_id")
        if not nc_id:
            return

        Nonconformity = apps.get_model("audit_management", "Nonconformity")
        try:
            nc = Nonconformity.objects.select_related("audit__organization").get(id=nc_id)
        except Nonconformity.DoesNotExist:
            return

        Profile = apps.get_model("identity", "Profile")
        client_emails = list(
            Profile.objects.filter(
                organization=nc.audit.organization,
                user__groups__name__in=["client_admin", "client_user"],
                user__email__gt="",
            )
            .values_list("user__email", flat=True)
            .distinct()
        )

        if not client_emails:
            return

        context = {
            "nc": nc,
            "audit": nc.audit,
            "site_url": getattr(settings, "SITE_URL", ""),
        }
        for email in client_emails:
            _send_notification(
                recipient_email=email,
                subject=f"Response required: {nc.get_category_display()} NC – Clause {nc.clause}",
                template="notifications/nc_response_required.html",
                context=context,
            )

    # ------------------------------------------------------------------
    # Certification notifications
    # ------------------------------------------------------------------

    @staticmethod
    def notify_certification_expiring(payload: dict) -> None:
        """Notify the client that a certification is approaching expiry."""
        certification_id = payload.get("certification_id")
        if not certification_id:
            return

        Certification = apps.get_model("core", "Certification")
        try:
            cert = Certification.objects.select_related("organization", "standard").get(id=certification_id)
        except Certification.DoesNotExist:
            return

        Profile = apps.get_model("identity", "Profile")
        client_emails = list(
            Profile.objects.filter(
                organization=cert.organization,
                user__groups__name__in=["client_admin", "client_user"],
                user__email__gt="",
            )
            .values_list("user__email", flat=True)
            .distinct()
        )

        if not client_emails:
            return

        context = {
            "certification": cert,
            "site_url": getattr(settings, "SITE_URL", ""),
        }
        for email in client_emails:
            _send_notification(
                recipient_email=email,
                subject=f"Certification expiring: {cert.standard.code} – {cert.organization.name}",
                template="notifications/certification_expiring.html",
                context=context,
            )

    # ------------------------------------------------------------------
    # Complaint / Appeal notifications
    # ------------------------------------------------------------------

    @staticmethod
    def notify_complaint_received(payload: dict) -> None:
        """Notify CB admin that a new complaint has been received."""
        complaint_id = payload.get("complaint_id")
        if not complaint_id:
            return

        Complaint = apps.get_model("certification", "Complaint")
        try:
            complaint = Complaint.objects.get(id=complaint_id)
        except Complaint.DoesNotExist:
            return

        # Notify all CB admins
        User = apps.get_model("auth", "User")
        admin_emails = list(
            User.objects.filter(groups__name="cb_admin", email__gt="").values_list("email", flat=True).distinct()
        )

        if not admin_emails:
            return

        context = {
            "complaint": complaint,
            "site_url": getattr(settings, "SITE_URL", ""),
        }
        for email in admin_emails:
            _send_notification(
                recipient_email=email,
                subject=f"New complaint received: {complaint.complaint_number}",
                template="notifications/complaint_received.html",
                context=context,
            )

    @staticmethod
    def notify_decision_made(payload: dict) -> None:
        """Notify relevant parties when a certification decision is made."""
        audit_id = payload.get("audit_id")
        if not audit_id:
            return

        CertificationDecision = apps.get_model("certification", "CertificationDecision")
        try:
            decision = CertificationDecision.objects.select_related("audit__organization", "decision_maker").get(
                audit_id=audit_id
            )
        except CertificationDecision.DoesNotExist:
            return

        Audit = apps.get_model("audit_management", "Audit")
        audit = decision.audit

        recipients = set()
        if audit.lead_auditor and audit.lead_auditor.email:
            recipients.add(audit.lead_auditor.email)

        # Also notify client contacts
        Profile = apps.get_model("identity", "Profile")
        client_emails = (
            Profile.objects.filter(
                organization=audit.organization,
                user__groups__name__in=["client_admin"],
                user__email__gt="",
            )
            .values_list("user__email", flat=True)
            .distinct()
        )
        recipients.update(client_emails)

        if not recipients:
            return

        context = {
            "decision": decision,
            "audit": audit,
            "site_url": getattr(settings, "SITE_URL", ""),
        }
        for email in recipients:
            _send_notification(
                recipient_email=email,
                subject=f"Certification decision: {decision.get_decision_display()} – {audit.organization.name}",
                template="notifications/decision_made.html",
                context=context,
            )


# --------------------------------------------------------------------------
# Private helpers
# --------------------------------------------------------------------------


def _send_notification(
    recipient_email: str,
    subject: str,
    template: str,
    context: dict,
) -> None:
    """
    Render an HTML template and send a notification email.

    Failures are logged but never raised.
    """
    try:
        html_body = render_to_string(template, context)
        send_mail(
            subject=subject,
            message="",  # plain-text fallback (HTML only for now)
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_body,
            fail_silently=False,
        )
        logger.info("Notification sent to %s: %s", recipient_email, subject)
    except Exception:
        logger.exception("Failed to send notification to %s: %s", recipient_email, subject)
