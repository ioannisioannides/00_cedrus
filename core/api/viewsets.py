"""
REST API ViewSets for core models.

Provides CRUD API endpoints for Organization, Site, Standard, and Certification.
All endpoints require authentication. Write operations require CB Admin role.
"""

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Certification, Organization, Site, Standard

from .serializers import (
    CertificationSerializer,
    OrganizationListSerializer,
    OrganizationSerializer,
    SiteSerializer,
    StandardSerializer,
)


class IsCBAdmin(permissions.BasePermission):
    """Permission check for CB Admin role."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.groups.filter(name="cb_admin").exists()


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing organizations.

    list: List all organizations (authenticated users).
    retrieve: Get organization details.
    create/update/delete: CB Admin only.
    """

    queryset = Organization.objects.all().order_by("name")
    permission_classes = [permissions.IsAuthenticated, IsCBAdmin]

    def get_serializer_class(self):
        if self.action == "list":
            return OrganizationListSerializer
        return OrganizationSerializer

    @action(detail=True, methods=["get"])
    def sites(self, request, pk=None):
        """List all sites for an organization."""
        organization = self.get_object()
        sites = organization.sites.all()
        serializer = SiteSerializer(sites, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def certifications(self, request, pk=None):
        """List all certifications for an organization."""
        organization = self.get_object()
        certs = organization.certifications.select_related("standard").all()
        serializer = CertificationSerializer(certs, many=True)
        return Response(serializer.data)


class SiteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing sites.

    Supports filtering by organization via ?organization=<id>.
    """

    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated, IsCBAdmin]

    def get_queryset(self):
        queryset = Site.objects.select_related("organization").order_by("site_name")
        org_id = self.request.query_params.get("organization")
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        return queryset


class StandardViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing standards.

    Standards are reference data (e.g., ISO 9001:2015).
    """

    queryset = Standard.objects.all().order_by("code")
    serializer_class = StandardSerializer
    permission_classes = [permissions.IsAuthenticated, IsCBAdmin]


class CertificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing certifications.

    Supports filtering by organization and status.
    """

    serializer_class = CertificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsCBAdmin]

    def get_queryset(self):
        queryset = Certification.objects.select_related("organization", "standard").order_by("-created_at")
        org_id = self.request.query_params.get("organization")
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(certificate_status=status)
        return queryset
