"""
Event handlers for the Cedrus event system.

Registers handlers for audit lifecycle events to enable event-driven notifications,
logging, and other derived actions.
"""

import logging

from trunk.events import EventType, event_dispatcher

logger = logging.getLogger(__name__)


def on_audit_status_changed(payload):
    """
    Handler for audit status change events.

    Emits derived events based on status transitions.
    """
    audit = payload.get("audit")
    new_status = payload.get("new_status")
    changed_by = payload.get("changed_by")

    if not audit or not new_status:
        return

    # Emit derived events based on status transitions
    if new_status == "client_review":
        event_dispatcher.emit(
            EventType.AUDIT_SUBMITTED_TO_CLIENT,
            {"audit": audit, "changed_by": changed_by},
        )
        logger.info(f"Audit {audit.id} submitted to client for review")

    elif new_status == "submitted":
        event_dispatcher.emit(
            EventType.AUDIT_SUBMITTED_TO_CB,
            {"audit": audit, "changed_by": changed_by},
        )
        logger.info(f"Audit {audit.id} submitted to CB for decision")

    elif new_status == "decided":
        event_dispatcher.emit(
            EventType.AUDIT_DECIDED,
            {"audit": audit, "changed_by": changed_by},
        )
        logger.info(f"Audit {audit.id} decision made by {changed_by}")


def on_nc_verified(payload):
    """
    Handler for NC verification events.

    Logs verification actions and emits derived events.
    """
    nc = payload.get("nc")
    verification_status = payload.get("verification_status")

    if not nc or not verification_status:
        return

    if verification_status == "accepted":
        event_dispatcher.emit(
            EventType.NC_VERIFIED_ACCEPTED,
            {"nc": nc},
        )
        logger.info(f"NC {nc.id} (Clause {nc.clause}) verified and accepted")

    elif verification_status == "rejected":
        event_dispatcher.emit(
            EventType.NC_VERIFIED_REJECTED,
            {"nc": nc},
        )
        logger.info(f"NC {nc.id} (Clause {nc.clause}) verification rejected")

    elif verification_status == "closed":
        event_dispatcher.emit(
            EventType.NC_CLOSED,
            {"nc": nc},
        )
        logger.info(f"NC {nc.id} (Clause {nc.clause}) closed")


def register_event_handlers():
    """
    Register all event handlers.

    Called from core.apps.CoreConfig.ready()
    """
    event_dispatcher.register(EventType.AUDIT_STATUS_CHANGED, on_audit_status_changed)
    logger.info("Registered event handlers for audit lifecycle events")
