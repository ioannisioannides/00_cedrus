"""
Views for core app: organizations, sites, standards, certifications.

All views require CB Admin permissions (except read-only views for clients).
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .models import Certification, Organization, Site, Standard


class CBAdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require CB Admin role."""

    def test_func(self):
        return self.request.user.groups.filter(name="cb_admin").exists()


# Organization Views
class OrganizationListView(LoginRequiredMixin, CBAdminRequiredMixin, ListView):
    """List all organizations."""

    model = Organization
    template_name = "core/organization_list.html"
    context_object_name = "organizations"
    paginate_by = 20


class OrganizationDetailView(LoginRequiredMixin, CBAdminRequiredMixin, DetailView):
    """View organization details."""

    model = Organization
    template_name = "core/organization_detail.html"
    context_object_name = "organization"


class OrganizationCreateView(LoginRequiredMixin, CBAdminRequiredMixin, CreateView):
    """Create a new organization."""

    model = Organization
    template_name = "core/organization_form.html"
    fields = [
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
    ]
    success_url = reverse_lazy("core:organization_list")


class OrganizationUpdateView(LoginRequiredMixin, CBAdminRequiredMixin, UpdateView):
    """Update an organization."""

    model = Organization
    template_name = "core/organization_form.html"
    fields = [
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
    ]
    success_url = reverse_lazy("core:organization_list")


# Site Views
class SiteListView(LoginRequiredMixin, CBAdminRequiredMixin, ListView):
    """List all sites, optionally filtered by organization."""

    model = Site
    template_name = "core/site_list.html"
    context_object_name = "sites"
    paginate_by = 20

    def get_queryset(self):
        """
        Get queryset of sites, optionally filtered by organization.

        Query Parameters:
            organization: Filter by organization ID

        Returns:
            QuerySet of Site objects with organization pre-fetched
        """
        queryset = Site.objects.all()
        org_id = self.request.GET.get("organization")
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        return queryset.select_related("organization")

    def get_context_data(self, **kwargs):
        """Add all organizations to context for filter dropdown."""
        context = super().get_context_data(**kwargs)
        context["organizations"] = Organization.objects.all()
        return context


class SiteCreateView(LoginRequiredMixin, CBAdminRequiredMixin, CreateView):
    """Create a new site."""

    model = Site
    template_name = "core/site_form.html"
    fields = [
        "organization",
        "site_name",
        "site_address",
        "site_employee_count",
        "site_scope_override",
        "active",
    ]
    success_url = reverse_lazy("core:site_list")


class SiteUpdateView(LoginRequiredMixin, CBAdminRequiredMixin, UpdateView):
    """Update a site."""

    model = Site
    template_name = "core/site_form.html"
    fields = [
        "organization",
        "site_name",
        "site_address",
        "site_employee_count",
        "site_scope_override",
        "active",
    ]
    success_url = reverse_lazy("core:site_list")


# Standard Views
class StandardListView(LoginRequiredMixin, CBAdminRequiredMixin, ListView):
    """List all standards."""

    model = Standard
    template_name = "core/standard_list.html"
    context_object_name = "standards"
    paginate_by = 20


class StandardCreateView(LoginRequiredMixin, CBAdminRequiredMixin, CreateView):
    """Create a new standard."""

    model = Standard
    template_name = "core/standard_form.html"
    fields = ["code", "title", "nace_code", "ea_code"]
    success_url = reverse_lazy("core:standard_list")


class StandardUpdateView(LoginRequiredMixin, CBAdminRequiredMixin, UpdateView):
    """Update a standard."""

    model = Standard
    template_name = "core/standard_form.html"
    fields = ["code", "title", "nace_code", "ea_code"]
    success_url = reverse_lazy("core:standard_list")


# Certification Views
class CertificationListView(LoginRequiredMixin, CBAdminRequiredMixin, ListView):
    """List all certifications, optionally filtered by organization."""

    model = Certification
    template_name = "core/certification_list.html"
    context_object_name = "certifications"
    paginate_by = 20

    def get_queryset(self):
        """
        Get queryset of certifications, optionally filtered by organization.

        Query Parameters:
            organization: Filter by organization ID

        Returns:
            QuerySet of Certification objects with related data pre-fetched
        """
        queryset = Certification.objects.select_related("organization", "standard")
        org_id = self.request.GET.get("organization")
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        return queryset

    def get_context_data(self, **kwargs):
        """Add all organizations to context for filter dropdown."""
        context = super().get_context_data(**kwargs)
        context["organizations"] = Organization.objects.all()
        return context


class CertificationCreateView(LoginRequiredMixin, CBAdminRequiredMixin, CreateView):
    """Create a new certification."""

    model = Certification
    template_name = "core/certification_form.html"
    fields = [
        "organization",
        "standard",
        "certification_scope",
        "certificate_id",
        "certificate_status",
        "issue_date",
        "expiry_date",
    ]
    success_url = reverse_lazy("core:certification_list")


class CertificationUpdateView(LoginRequiredMixin, CBAdminRequiredMixin, UpdateView):
    """Update a certification."""

    model = Certification
    template_name = "core/certification_form.html"
    fields = [
        "organization",
        "standard",
        "certification_scope",
        "certificate_id",
        "certificate_status",
        "issue_date",
        "expiry_date",
    ]
    success_url = reverse_lazy("core:certification_list")
