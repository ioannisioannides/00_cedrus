"""
REST API Serializers for audit management models.

Provides JSON serialization for Audit, Finding, AuditProgram, and related models.
"""

from rest_framework import serializers

from audit_management.models import (
    Audit,
    AuditProgram,
    AuditTeamMember,
    EvidenceFile,
    Nonconformity,
    Observation,
    OpportunityForImprovement,
)


class AuditProgramSerializer(serializers.ModelSerializer):
    """Serializer for AuditProgram model."""

    organization_name = serializers.CharField(source="organization.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = AuditProgram
        fields = [
            "id",
            "organization",
            "organization_name",
            "title",
            "year",
            "status",
            "objectives",
            "risks_opportunities",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class AuditTeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for AuditTeamMember model."""

    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = AuditTeamMember
        fields = ["id", "audit", "user", "user_name", "name", "title", "role", "date_from", "date_to"]
        read_only_fields = ["id"]


class NonconformitySerializer(serializers.ModelSerializer):
    """Serializer for Nonconformity findings."""

    standard_code = serializers.CharField(source="standard.code", read_only=True)
    site_name = serializers.CharField(source="site.site_name", read_only=True, default=None)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    verified_by_name = serializers.CharField(source="verified_by.get_full_name", read_only=True, default=None)

    class Meta:
        model = Nonconformity
        fields = [
            "id",
            "audit",
            "standard",
            "standard_code",
            "clause",
            "site",
            "site_name",
            "category",
            "objective_evidence",
            "statement_of_nc",
            "auditor_explanation",
            "client_root_cause",
            "client_correction",
            "client_corrective_action",
            "due_date",
            "verification_status",
            "verified_by",
            "verified_by_name",
            "verified_at",
            "verification_notes",
            "created_by",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "verified_by", "verified_at", "created_at"]


class ObservationSerializer(serializers.ModelSerializer):
    """Serializer for Observation findings."""

    standard_code = serializers.CharField(source="standard.code", read_only=True)

    class Meta:
        model = Observation
        fields = [
            "id",
            "audit",
            "standard",
            "standard_code",
            "clause",
            "site",
            "statement",
            "explanation",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]


class OFISerializer(serializers.ModelSerializer):
    """Serializer for Opportunity for Improvement findings."""

    standard_code = serializers.CharField(source="standard.code", read_only=True)

    class Meta:
        model = OpportunityForImprovement
        fields = [
            "id",
            "audit",
            "standard",
            "standard_code",
            "clause",
            "site",
            "description",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]


class EvidenceFileSerializer(serializers.ModelSerializer):
    """Serializer for EvidenceFile model."""

    uploaded_by_name = serializers.CharField(source="uploaded_by.get_full_name", read_only=True)

    class Meta:
        model = EvidenceFile
        fields = [
            "id",
            "audit",
            "finding",
            "uploaded_by",
            "uploaded_by_name",
            "file",
            "evidence_type",
            "description",
            "uploaded_at",
            "retention_years",
            "purge_after",
        ]
        read_only_fields = ["id", "uploaded_by", "uploaded_at", "purge_after"]


class AuditListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Audit list views."""

    organization_name = serializers.CharField(source="organization.name", read_only=True)
    lead_auditor_name = serializers.CharField(source="lead_auditor.get_full_name", read_only=True, default=None)

    class Meta:
        model = Audit
        fields = [
            "id",
            "organization",
            "organization_name",
            "audit_type",
            "status",
            "total_audit_date_from",
            "total_audit_date_to",
            "lead_auditor",
            "lead_auditor_name",
            "created_at",
        ]


class AuditDetailSerializer(serializers.ModelSerializer):
    """Full serializer for Audit detail views."""

    organization_name = serializers.CharField(source="organization.name", read_only=True)
    lead_auditor_name = serializers.CharField(source="lead_auditor.get_full_name", read_only=True, default=None)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    team_members = AuditTeamMemberSerializer(many=True, read_only=True)
    nonconformities = NonconformitySerializer(source="nonconformity_set", many=True, read_only=True)
    observations = ObservationSerializer(source="observation_set", many=True, read_only=True)
    ofis = OFISerializer(source="opportunityforimprovement_set", many=True, read_only=True)
    nc_count = serializers.SerializerMethodField()
    open_nc_count = serializers.SerializerMethodField()

    class Meta:
        model = Audit
        fields = [
            "id",
            "program",
            "organization",
            "organization_name",
            "audit_type",
            "status",
            "total_audit_date_from",
            "total_audit_date_to",
            "planned_duration_hours",
            "actual_duration_hours",
            "duration_justification",
            "lead_auditor",
            "lead_auditor_name",
            "created_by",
            "created_by_name",
            "team_members",
            "nonconformities",
            "observations",
            "ofis",
            "nc_count",
            "open_nc_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_nc_count(self, obj):
        return obj.nonconformity_set.count()

    def get_open_nc_count(self, obj):
        return obj.nonconformity_set.exclude(verification_status="closed").count()


class AuditCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating audits."""

    class Meta:
        model = Audit
        fields = [
            "program",
            "organization",
            "audit_type",
            "total_audit_date_from",
            "total_audit_date_to",
            "planned_duration_hours",
            "duration_justification",
            "lead_auditor",
        ]
