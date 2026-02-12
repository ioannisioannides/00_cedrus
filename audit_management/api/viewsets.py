"""
REST API ViewSets for audit management models.

Provides CRUD API endpoints for Audit, AuditProgram, Findings, and Evidence.
All endpoints require authentication. Write operations require CB Admin or Auditor role.
"""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit_management.models import (
    Audit,
    AuditProgram,
    AuditTeamMember,
    EvidenceFile,
    Nonconformity,
    Observation,
    OpportunityForImprovement,
)

from .serializers import (
    AuditCreateSerializer,
    AuditDetailSerializer,
    AuditListSerializer,
    AuditProgramSerializer,
    AuditTeamMemberSerializer,
    EvidenceFileSerializer,
    NonconformitySerializer,
    ObservationSerializer,
    OFISerializer,
)


class IsAuditorOrAdmin(permissions.BasePermission):
    """Permission check for auditor or CB Admin role."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.groups.filter(name__in=["cb_admin", "lead_auditor", "auditor"]).exists()


class AuditProgramViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing audit programs.

    list: List all programs (filterable by organization, year).
    retrieve: Get program details including linked audits.
    create/update/delete: CB Admin or Auditor only.
    """

    serializer_class = AuditProgramSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuditorOrAdmin]

    def get_queryset(self):
        queryset = AuditProgram.objects.select_related("organization", "created_by").order_by("-year", "title")
        org_id = self.request.query_params.get("organization")
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        year = self.request.query_params.get("year")
        if year:
            queryset = queryset.filter(year=year)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AuditViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing audits.

    list: List audits (filterable by organization, status, audit_type).
    retrieve: Full detail view with findings and team members.
    create/update/delete: CB Admin or Auditor only.
    """

    permission_classes = [permissions.IsAuthenticated, IsAuditorOrAdmin]

    def get_serializer_class(self):
        if self.action == "list":
            return AuditListSerializer
        if self.action in ("create", "update", "partial_update"):
            return AuditCreateSerializer
        return AuditDetailSerializer

    def get_queryset(self):
        queryset = Audit.objects.select_related("organization", "lead_auditor", "created_by", "program").order_by(
            "-total_audit_date_from"
        )
        org_id = self.request.query_params.get("organization")
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        audit_status = self.request.query_params.get("status")
        if audit_status:
            queryset = queryset.filter(status=audit_status)
        audit_type = self.request.query_params.get("audit_type")
        if audit_type:
            queryset = queryset.filter(audit_type=audit_type)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["get"])
    def findings(self, request, pk=None):
        """List all findings (NCs, observations, OFIs) for this audit."""
        audit = self.get_object()
        data = {
            "nonconformities": NonconformitySerializer(audit.nonconformity_set.all(), many=True).data,
            "observations": ObservationSerializer(audit.observation_set.all(), many=True).data,
            "ofis": OFISerializer(audit.opportunityforimprovement_set.all(), many=True).data,
        }
        return Response(data)

    @action(detail=True, methods=["get"])
    def team(self, request, pk=None):
        """List team members for this audit."""
        audit = self.get_object()
        serializer = AuditTeamMemberSerializer(audit.team_members.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def evidence(self, request, pk=None):
        """List evidence files for this audit."""
        audit = self.get_object()
        serializer = EvidenceFileSerializer(audit.evidence_files.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        """Transition audit to a new status."""
        audit = self.get_object()
        new_status = request.data.get("status")
        if not new_status:
            return Response({"error": "status field is required"}, status=status.HTTP_400_BAD_REQUEST)

        valid_statuses = [s[0] for s in Audit.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {"error": f"Invalid status. Choose from: {valid_statuses}"}, status=status.HTTP_400_BAD_REQUEST
            )

        old_status = audit.status
        audit.status = new_status
        audit.save(update_fields=["status"])

        return Response({"previous_status": old_status, "new_status": new_status})


class NonconformityViewSet(viewsets.ModelViewSet):
    """API endpoint for nonconformity findings."""

    serializer_class = NonconformitySerializer
    permission_classes = [permissions.IsAuthenticated, IsAuditorOrAdmin]

    def get_queryset(self):
        queryset = Nonconformity.objects.select_related("audit", "standard", "site", "created_by", "verified_by")
        audit_id = self.request.query_params.get("audit")
        if audit_id:
            queryset = queryset.filter(audit_id=audit_id)
        verification_status = self.request.query_params.get("verification_status")
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ObservationViewSet(viewsets.ModelViewSet):
    """API endpoint for observation findings."""

    serializer_class = ObservationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuditorOrAdmin]

    def get_queryset(self):
        queryset = Observation.objects.select_related("audit", "standard", "site", "created_by")
        audit_id = self.request.query_params.get("audit")
        if audit_id:
            queryset = queryset.filter(audit_id=audit_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class OFIViewSet(viewsets.ModelViewSet):
    """API endpoint for opportunity for improvement findings."""

    serializer_class = OFISerializer
    permission_classes = [permissions.IsAuthenticated, IsAuditorOrAdmin]

    def get_queryset(self):
        queryset = OpportunityForImprovement.objects.select_related("audit", "standard", "site", "created_by")
        audit_id = self.request.query_params.get("audit")
        if audit_id:
            queryset = queryset.filter(audit_id=audit_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AuditTeamMemberViewSet(viewsets.ModelViewSet):
    """API endpoint for audit team members."""

    serializer_class = AuditTeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuditorOrAdmin]

    def get_queryset(self):
        queryset = AuditTeamMember.objects.select_related("audit", "user")
        audit_id = self.request.query_params.get("audit")
        if audit_id:
            queryset = queryset.filter(audit_id=audit_id)
        return queryset


class EvidenceFileViewSet(viewsets.ModelViewSet):
    """API endpoint for evidence file uploads."""

    serializer_class = EvidenceFileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuditorOrAdmin]

    def get_queryset(self):
        queryset = EvidenceFile.objects.select_related("audit", "finding", "uploaded_by")
        audit_id = self.request.query_params.get("audit")
        if audit_id:
            queryset = queryset.filter(audit_id=audit_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
