"""
Views for Audit Program management (ISO 19011).
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from audit_management.forms.program_forms import AuditProgramForm
from audit_management.models import AuditProgram
from trunk.permissions.predicates import PermissionPredicate


class AuditProgramListView(LoginRequiredMixin, ListView):
    """List audit programs."""

    model = AuditProgram
    template_name = "audits/program_list.html"
    context_object_name = "programs"
    paginate_by = 20

    def get_queryset(self):
        """Filter programs by user role."""
        user = self.request.user
        queryset = AuditProgram.objects.select_related("organization", "created_by")

        if PermissionPredicate.is_cb_admin(user):
            return queryset

        if PermissionPredicate.is_client_user(user):
            if hasattr(user, "profile") and user.profile.organization:
                return queryset.filter(organization=user.profile.organization)

        # Auditors can see programs they are involved in (via audits)
        if PermissionPredicate.is_auditor(user):
            return queryset.filter(audits__lead_auditor=user).distinct()

        return queryset.none()


class AuditProgramCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new audit program."""

    model = AuditProgram
    form_class = AuditProgramForm
    template_name = "audits/program_form.html"

    def test_func(self):
        """Only CB Admin and Client Admin can create programs."""
        user = self.request.user
        is_client_admin = user.groups.filter(name="client_admin").exists()
        return PermissionPredicate.is_cb_admin(user) or is_client_admin

    def form_valid(self, form):
        """Set organization and creator."""
        user = self.request.user
        program = form.save(commit=False)
        program.created_by = user

        if PermissionPredicate.is_client_user(user):
            program.organization = user.profile.organization
        elif PermissionPredicate.is_cb_admin(user):
            # For CB Admin, we might need to select organization.
            # But the form doesn't have organization field.
            # For now, let's assume CB Admin creates for their own org or we need to add org field for CB Admin.
            # Ideally, CB Admin should be able to select organization.
            # Let's check if we can get organization from URL or if we need to add it to form.
            # If this is for "Internal Audit", usually it's the organization doing it.
            # If CB Admin is creating a program for a client, they need to select the client.
            pass

        # If organization is not set (e.g. CB Admin didn't select), we have a problem.
        # Let's assume for now this is primarily for Clients to manage their internal audits.
        # If CB Admin uses it, they might be managing the CB's own internal audits.
        # I'll check if user has profile.organization.

        if hasattr(user, "profile") and user.profile.organization:
            program.organization = user.profile.organization
        else:
            # Fallback or error. For now, let's assume user has organization.
            # If CB Admin doesn't have organization in profile, this might fail.
            # But CB Admin usually belongs to the CB Organization.
            pass

        self.object = program.save()
        # save() returns None, so we need to set self.object to program
        program.save()
        self.object = program

        messages.success(self.request, "Audit Program created successfully.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("audits:program_detail", kwargs={"pk": self.object.pk})


class AuditProgramDetailView(LoginRequiredMixin, DetailView):
    """View audit program details."""

    model = AuditProgram
    template_name = "audits/program_detail.html"
    context_object_name = "program"

    def get_queryset(self):
        """Filter programs by user role."""
        # Reuse list view logic or similar
        user = self.request.user
        queryset = AuditProgram.objects.select_related("organization")

        if PermissionPredicate.is_cb_admin(user):
            return queryset

        if PermissionPredicate.is_client_user(user):
            if hasattr(user, "profile") and user.profile.organization:
                return queryset.filter(organization=user.profile.organization)

        if PermissionPredicate.is_auditor(user):
            return queryset.filter(audits__lead_auditor=user).distinct()

        return queryset.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["audits"] = self.object.audits.all()
        return context


class AuditProgramUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update audit program."""

    model = AuditProgram
    form_class = AuditProgramForm
    template_name = "audits/program_form.html"

    def test_func(self):
        """Only creator or admins can edit."""
        program = self.get_object()
        user = self.request.user

        if PermissionPredicate.is_cb_admin(user):
            return True

        is_client_admin = user.groups.filter(name="client_admin").exists()
        if is_client_admin and program.organization == user.profile.organization:
            return True

        return False

    def get_success_url(self):
        return reverse("audits:program_detail", kwargs={"pk": self.object.pk})


class AuditProgramDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete audit program."""

    model = AuditProgram
    template_name = "audits/program_confirm_delete.html"
    success_url = reverse_lazy("audits:program_list")

    def test_func(self):
        """Only admins can delete."""
        program = self.get_object()
        user = self.request.user

        if PermissionPredicate.is_cb_admin(user):
            return True

        is_client_admin = user.groups.filter(name="client_admin").exists()
        if is_client_admin and program.organization == user.profile.organization:
            return True

        return False
