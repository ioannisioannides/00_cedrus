"""
REST API Serializers for certification models.

Provides JSON serialization for Complaint, Appeal, CertificationDecision,
TechnicalReview, and TransferCertification.
"""

from rest_framework import serializers

from certification.models import Appeal, CertificationDecision, Complaint, TechnicalReview, TransferCertification


class ComplaintSerializer(serializers.ModelSerializer):
    """Serializer for Complaint model."""

    organization_name = serializers.CharField(source="organization.name", read_only=True, default=None)
    submitted_by_name = serializers.CharField(source="submitted_by.get_full_name", read_only=True, default=None)
    assigned_investigator_name = serializers.CharField(
        source="assigned_investigator.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = Complaint
        fields = [
            "id",
            "complaint_number",
            "organization",
            "organization_name",
            "related_audit",
            "complainant_name",
            "complainant_email",
            "complaint_type",
            "description",
            "submitted_at",
            "submitted_by",
            "submitted_by_name",
            "status",
            "assigned_investigator",
            "assigned_investigator_name",
            "investigation_started_at",
            "investigation_notes",
            "investigation_completed_at",
            "resolution_details",
            "corrective_actions",
        ]
        read_only_fields = ["id", "complaint_number", "submitted_at", "submitted_by"]


class ComplaintListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Complaint list views."""

    organization_name = serializers.CharField(source="organization.name", read_only=True, default=None)

    class Meta:
        model = Complaint
        fields = [
            "id",
            "complaint_number",
            "organization_name",
            "complaint_type",
            "status",
            "submitted_at",
            "complainant_name",
        ]


class AppealSerializer(serializers.ModelSerializer):
    """Serializer for Appeal model."""

    submitted_by_name = serializers.CharField(source="submitted_by.get_full_name", read_only=True, default=None)

    class Meta:
        model = Appeal
        fields = [
            "id",
            "appeal_number",
            "related_complaint",
            "related_decision",
            "appellant_name",
            "appellant_email",
            "grounds",
            "submitted_at",
            "submitted_by",
            "submitted_by_name",
            "status",
            "panel_decision",
            "panel_decision_date",
            "panel_justification",
        ]
        read_only_fields = ["id", "appeal_number", "submitted_at", "submitted_by"]


class CertificationDecisionSerializer(serializers.ModelSerializer):
    """Serializer for CertificationDecision model."""

    decision_maker_name = serializers.CharField(source="decision_maker.get_full_name", read_only=True)
    audit_display = serializers.CharField(source="audit.__str__", read_only=True)

    class Meta:
        model = CertificationDecision
        fields = [
            "id",
            "audit",
            "audit_display",
            "decision_maker",
            "decision_maker_name",
            "decided_at",
            "decision",
            "decision_notes",
        ]
        read_only_fields = ["id", "decided_at"]


class TechnicalReviewSerializer(serializers.ModelSerializer):
    """Serializer for TechnicalReview model."""

    reviewer_name = serializers.CharField(source="reviewer.get_full_name", read_only=True)
    audit_display = serializers.CharField(source="audit.__str__", read_only=True)

    class Meta:
        model = TechnicalReview
        fields = [
            "id",
            "audit",
            "audit_display",
            "reviewer",
            "reviewer_name",
            "reviewed_at",
            "status",
            "scope_verified",
            "objectives_verified",
            "findings_reviewed",
            "conclusion_clear",
            "reviewer_notes",
            "clarification_requested",
        ]
        read_only_fields = ["id", "reviewed_at"]


class TransferCertificationSerializer(serializers.ModelSerializer):
    """Serializer for TransferCertification model."""

    class Meta:
        model = TransferCertification
        fields = [
            "id",
            "transfer_audit",
            "previous_cb_name",
            "previous_cb_accreditation_body",
            "previous_certificate_number",
            "previous_certificate_issue_date",
            "previous_certificate_expiry_date",
            "reason_for_transfer",
            "previous_audit_reports_received",
            "previous_nc_records_received",
            "previous_surveillance_history_received",
            "transfer_date_before_expiry",
            "no_expiry_extension_applied",
            "transfer_approved",
            "transfer_approval_notes",
        ]
        read_only_fields = ["id"]
