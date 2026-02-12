"""
REST API ViewSets for certification models.

Provides CRUD API endpoints for Complaints, Appeals, CertificationDecisions,
TechnicalReviews, and TransferCertifications.
"""

from rest_framework import permissions, viewsets

from certification.models import Appeal, CertificationDecision, Complaint, TechnicalReview, TransferCertification

from .serializers import (
    AppealSerializer,
    CertificationDecisionSerializer,
    ComplaintListSerializer,
    ComplaintSerializer,
    TechnicalReviewSerializer,
    TransferCertificationSerializer,
)


class IsCBStaff(permissions.BasePermission):
    """Permission check for CB staff roles (admin, auditor, reviewer)."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.groups.filter(name__in=["cb_admin", "lead_auditor", "auditor"]).exists()


class ComplaintViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing complaints.

    Filterable by status and organization.
    """

    permission_classes = [permissions.IsAuthenticated, IsCBStaff]

    def get_serializer_class(self):
        if self.action == "list":
            return ComplaintListSerializer
        return ComplaintSerializer

    def get_queryset(self):
        queryset = Complaint.objects.select_related(
            "organization", "submitted_by", "assigned_investigator"
        ).order_by("-submitted_at")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        org_id = self.request.query_params.get("organization")
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)


class AppealViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing appeals.

    Filterable by status.
    """

    serializer_class = AppealSerializer
    permission_classes = [permissions.IsAuthenticated, IsCBStaff]

    def get_queryset(self):
        queryset = Appeal.objects.select_related(
            "submitted_by", "related_complaint", "related_decision"
        ).order_by("-submitted_at")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)


class CertificationDecisionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for certification decisions.

    Filterable by decision type.
    """

    serializer_class = CertificationDecisionSerializer
    permission_classes = [permissions.IsAuthenticated, IsCBStaff]

    def get_queryset(self):
        queryset = CertificationDecision.objects.select_related("audit", "decision_maker").order_by("-decided_at")
        decision = self.request.query_params.get("decision")
        if decision:
            queryset = queryset.filter(decision=decision)
        return queryset


class TechnicalReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for technical reviews.

    Filterable by status.
    """

    serializer_class = TechnicalReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsCBStaff]

    def get_queryset(self):
        queryset = TechnicalReview.objects.select_related("audit", "reviewer").order_by("-reviewed_at")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class TransferCertificationViewSet(viewsets.ModelViewSet):
    """API endpoint for transfer certifications (IAF MD17)."""

    serializer_class = TransferCertificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsCBStaff]

    def get_queryset(self):
        return TransferCertification.objects.select_related("transfer_audit").order_by(
            "-previous_certificate_expiry_date"
        )
