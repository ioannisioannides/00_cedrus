"""
Django admin configuration for core app.
"""

from django.contrib import admin

from .models import Certification, Organization, Site, Standard


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin for Organization model."""

    list_display = ["name", "customer_id", "total_employee_count", "contact_email", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "customer_id", "registered_id"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "registered_id", "registered_address", "customer_id")},
        ),
        ("Employee Count", {"fields": ("total_employee_count",)}),
        (
            "Contact Information",
            {"fields": ("contact_telephone", "contact_fax", "contact_email", "contact_website")},
        ),
        ("Signatory", {"fields": ("signatory_name", "signatory_title")}),
        (
            "Management System Representative",
            {"fields": ("ms_representative_name", "ms_representative_title")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


class SiteInline(admin.TabularInline):
    """Inline admin for Site model."""

    model = Site
    extra = 1
    fields = ["site_name", "site_address", "site_employee_count", "active"]


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    """Admin for Site model."""

    list_display = ["site_name", "organization", "site_employee_count", "active", "created_at"]
    list_filter = ["active", "organization", "created_at"]
    search_fields = ["site_name", "site_address", "organization__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    """Admin for Standard model."""

    list_display = ["code", "title", "nace_code", "ea_code"]
    search_fields = ["code", "title"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    """Admin for Certification model."""

    list_display = [
        "organization",
        "standard",
        "certificate_status",
        "certificate_id",
        "issue_date",
        "expiry_date",
    ]
    list_filter = ["certificate_status", "standard", "created_at"]
    search_fields = ["organization__name", "standard__code", "certificate_id"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Basic Information", {"fields": ("organization", "standard", "certification_scope")}),
        (
            "Certificate Details",
            {"fields": ("certificate_id", "certificate_status", "issue_date", "expiry_date")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
