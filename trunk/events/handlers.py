"""
Event handlers for the Cedrus event system.

Registers handlers for audit lifecycle events to enable event-driven notifications,
logging, and other derived actions.
"""

import logging

from django.apps import apps

from trunk.events import EventType, event_dispatcher

logger = logging.getLogger(__name__)


def on_audit_status_changed(payload):
    """
    Handler for audit status change events.

    Emits derived events based on status transitions.
    """
    audit_id = payload.get("audit_id")
    new_status = payload.get("new_status")
    changed_by_id = payload.get("changed_by_id")

    if not audit_id or not new_status:
        return

    Audit = apps.get_model("audit_management", "Audit")
    User = apps.get_model("auth", "User")

    try:
        audit = Audit.objects.get(id=audit_id)
        changed_by = User.objects.get(id=changed_by_id) if changed_by_id else None
    except (Audit.DoesNotExist, User.DoesNotExist):
        logger.error("Audit %s or User %s not found", audit_id, changed_by_id)
        return

    # Emit derived events based on status transitions
    if new_status == "client_review":
        event_dispatcher.emit(
            EventType.AUDIT_SUBMITTED_TO_CLIENT,
            {"audit_id": audit.id, "changed_by_id": changed_by.id if changed_by else None},
        )
        logger.info("Audit %s submitted to client for review", audit.id)

    elif new_status == "submitted":
        event_dispatcher.emit(
            EventType.AUDIT_SUBMITTED_TO_CB,
            {"audit_id": audit.id, "changed_by_id": changed_by.id if changed_by else None},
        )
        logger.info("Audit %s submitted to CB for decision", audit.id)

    elif new_status == "decided":
        event_dispatcher.emit(
            EventType.AUDIT_DECIDED,
            {"audit_id": audit.id, "changed_by_id": changed_by.id if changed_by else None},
        )
        logger.info("Audit %s decision made by %s", audit.id, changed_by)


def on_nc_verified(payload):
    """
    Handler for NC verification events.

    Logs verification actions and emits derived events.
    """
    nc_id = payload.get("nc_id")
    verification_status = payload.get("verification_status")

    if not nc_id or not verification_status:
        return

    Nonconformity = apps.get_model("audit_management", "Nonconformity")
    try:
        nc = Nonconformity.objects.get(id=nc_id)
    except Nonconformity.DoesNotExist:
        logger.error("Nonconformity %s not found", nc_id)
        return

    if verification_status == "accepted":
        event_dispatcher.emit(
            EventType.NC_VERIFIED_ACCEPTED,
            {"nc_id": nc.id},
        )
        logger.info("NC %s (Clause %s) verified and accepted", nc.id, nc.clause)

    elif verification_status == "rejected":
        event_dispatcher.emit(
            EventType.NC_VERIFIED_REJECTED,
            {"nc_id": nc.id},
        )
        logger.info("NC %s (Clause %s) verification rejected", nc.id, nc.clause)

    elif verification_status == "closed":
        event_dispatcher.emit(
            EventType.NC_CLOSED,
            {"nc_id": nc.id},
        )
        logger.info("NC %s (Clause %s) closed", nc.id, nc.clause)


def on_complaint_received(payload):
    """Handler for complaint received events."""
    complaint_id = payload.get("complaint_id")
    Complaint = apps.get_model("certification", "Complaint")
    try:
        complaint = Complaint.objects.get(id=complaint_id)
        logger.info("Complaint %s received from %s", complaint.complaint_number, complaint.complainant_name)
    except Complaint.DoesNotExist:
        logger.error("Complaint %s not found", complaint_id)


def on_appeal_received(payload):
    """Handler for appeal received events."""
    appeal_id = payload.get("appeal_id")
    Appeal = apps.get_model("certification", "Appeal")
    try:
        appeal = Appeal.objects.get(id=appeal_id)
        logger.info("Appeal %s received from %s", appeal.appeal_number, appeal.appellant_name)
    except Appeal.DoesNotExist:
        logger.error("Appeal %s not found", appeal_id)


def on_certificate_history_created(payload):
    """Handler for certificate history creation."""
    history_id = payload.get("history_id")
    CertificateHistory = apps.get_model("core", "CertificateHistory")
    try:
        history = CertificateHistory.objects.get(id=history_id)
        logger.info("Certificate history created: %s for %s", history.action, history.certification.certificate_id)
    except CertificateHistory.DoesNotExist:
        logger.error("CertificateHistory %s not found", history_id)


def register_event_handlers():
    """
    Register all event handlers.

    Called from core.apps.CoreConfig.ready()
    """
    event_dispatcher.register(EventType.AUDIT_STATUS_CHANGED, on_audit_status_changed)
    event_dispatcher.register(EventType.COMPLAINT_RECEIVED, on_complaint_received)
    event_dispatcher.register(EventType.APPEAL_RECEIVED, on_appeal_received)
    event_dispatcher.register(EventType.CERTIFICATE_HISTORY_CREATED, on_certificate_history_created)
    logger.info("Registered event handlers for audit lifecycle events")
