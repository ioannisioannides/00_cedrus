"""
REST API Serializers for core models.

Provides JSON serialization for Organization, Site, Standard, and Certification.
"""

from rest_framework import serializers

from core.models import Certification, Organization, Site, Standard


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""

    sites_count = serializers.SerializerMethodField()
    certifications_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "registered_id",
            "registered_address",
            "customer_id",
            "total_employee_count",
            "contact_telephone",
            "contact_fax",
            "contact_email",
            "contact_website",
            "signatory_name",
            "signatory_title",
            "ms_representative_name",
            "ms_representative_title",
            "sites_count",
            "certifications_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_sites_count(self, obj):
        return obj.sites.count()

    def get_certifications_count(self, obj):
        return obj.certifications.count()


class OrganizationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Organization list views."""

    class Meta:
        model = Organization
        fields = ["id", "name", "customer_id", "total_employee_count", "contact_email"]


class SiteSerializer(serializers.ModelSerializer):
    """Serializer for Site model."""

    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Site
        fields = [
            "id",
            "organization",
            "organization_name",
            "site_name",
            "site_address",
            "site_employee_count",
            "site_scope_override",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StandardSerializer(serializers.ModelSerializer):
    """Serializer for Standard model."""

    class Meta:
        model = Standard
        fields = ["id", "code", "title", "nace_code", "ea_code", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CertificationSerializer(serializers.ModelSerializer):
    """Serializer for Certification model."""

    organization_name = serializers.CharField(source="organization.name", read_only=True)
    standard_code = serializers.CharField(source="standard.code", read_only=True)

    class Meta:
        model = Certification
        fields = [
            "id",
            "organization",
            "organization_name",
            "standard",
            "standard_code",
            "certification_scope",
            "certificate_id",
            "certificate_status",
            "issue_date",
            "expiry_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
