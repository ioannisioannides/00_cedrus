"""
Event type constants for the Cedrus event system.

These constants define all the events that can be emitted throughout
the application lifecycle.
"""


class EventType:
    """Event type constants."""

    # Audit lifecycle events
    AUDIT_CREATED = "audit.created"
    AUDIT_UPDATED = "audit.updated"
    AUDIT_STATUS_CHANGED = "audit.status_changed"
    AUDIT_SUBMITTED_TO_CLIENT = "audit.submitted_to_client"
    AUDIT_SUBMITTED_TO_CB = "audit.submitted_to_cb"
    AUDIT_DECIDED = "audit.decided"

    # Complaints & Appeals
    COMPLAINT_RECEIVED = "complaint.received"
    COMPLAINT_STATUS_CHANGED = "complaint.status_changed"
    APPEAL_RECEIVED = "appeal.received"
    APPEAL_DECIDED = "appeal.decided"

    # Certificate lifecycle
    CERTIFICATE_HISTORY_CREATED = "certificate.history_created"
    SURVEILLANCE_SCHEDULE_CREATED = "surveillance.schedule_created"

    # Finding lifecycle events
    FINDING_CREATED = "finding.created"
    FINDING_UPDATED = "finding.updated"
    FINDING_DELETED = "finding.deleted"

    # Nonconformity specific events
    NC_CLIENT_RESPONDED = "nc.client_responded"
    NC_VERIFIED_ACCEPTED = "nc.verified_accepted"
    NC_VERIFIED_REJECTED = "nc.verified_rejected"
    NC_CLOSED = "nc.closed"

    # Certification events
    CERTIFICATION_ISSUED = "certification.issued"
    CERTIFICATION_SUSPENDED = "certification.suspended"
    CERTIFICATION_REVOKED = "certification.revoked"
    CERTIFICATION_RENEWED = "certification.renewed"

    # Organization events
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_CREATED = "organization.created"
