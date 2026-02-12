"""
Views for identity app: login, logout, and role-based dashboards.
"""

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from identity.adapters.models import (
    AuditorCompetenceEvaluation,
    AuditorQualification,
    AuditorTrainingRecord,
    ConflictOfInterest,
)
from identity.api.forms import (
    AuditorCompetenceEvaluationForm,
    AuditorQualificationForm,
    AuditorTrainingRecordForm,
    ConflictOfInterestForm,
)


class CustomLoginView(LoginView):
    """Custom login view with template."""

    template_name = "identity/login.html"
    redirect_authenticated_user = True  # Redirect if already logged in

    def get_success_url(self):
        """Redirect to appropriate dashboard based on user role."""
        return reverse_lazy("identity:dashboard")


@login_required
def dashboard(request):
    """
    Role-based dashboard redirect.

    Redirects users to their appropriate dashboard based on their group membership.
    """
    user = request.user

    # Check groups in priority order
    if user.groups.filter(name="cb_admin").exists():
        return redirect("identity:dashboard_cb")
    if user.groups.filter(name="lead_auditor").exists() or user.groups.filter(name="auditor").exists():
        return redirect("identity:dashboard_auditor")
    if user.groups.filter(name="client_admin").exists() or user.groups.filter(name="client_user").exists():
        return redirect("identity:dashboard_client")

    # No role assigned - show basic dashboard
    return render(
        request,
        "identity/dashboard.html",
        {"user": user, "message": "No role assigned. Please contact an administrator."},
    )


@login_required
def dashboard_cb(request):
    """CB Admin dashboard."""
    if not request.user.groups.filter(name="cb_admin").exists():
        return redirect("identity:dashboard")

    # pylint: disable=import-outside-toplevel
    from audit_management.models import Audit
    from core.models import Certification, Organization

    context = {
        "user": request.user,
        "organizations_count": Organization.objects.count(),
        "certifications_count": Certification.objects.count(),
        "audits_count": Audit.objects.count(),
        "recent_audits": Audit.objects.select_related("organization", "lead_auditor").order_by("-created_at")[:5],
    }
    return render(request, "identity/dashboard_cb.html", context)


@login_required
def dashboard_auditor(request):
    """Auditor dashboard."""
    if not (
        request.user.groups.filter(name="lead_auditor").exists() or request.user.groups.filter(name="auditor").exists()
    ):
        return redirect("identity:dashboard")

    # pylint: disable=import-outside-toplevel
    from audit_management.models import Audit

    # Show audits where user is lead auditor or team member
    all_audits = (
        Audit.objects.filter(Q(lead_auditor=request.user) | Q(team_members__user=request.user))
        .select_related("organization", "lead_auditor")
        .distinct()
        .order_by("-total_audit_date_from")
    )

    context = {
        "user": request.user,
        "audits": all_audits[:10],
        "audits_count": all_audits.count(),
    }
    return render(request, "identity/dashboard_auditor.html", context)


@login_required
def dashboard_client(request):
    """Client dashboard."""
    if not (
        request.user.groups.filter(name="client_admin").exists()
        or request.user.groups.filter(name="client_user").exists()
    ):
        return redirect("identity:dashboard")

    # pylint: disable=import-outside-toplevel
    from audit_management.models import Audit

    # Get user's organization
    organization = None
    if hasattr(request.user, "profile") and request.user.profile.organization:
        organization = request.user.profile.organization
        audits = (
            Audit.objects.filter(organization=organization)
            .select_related("organization", "lead_auditor")
            .order_by("-total_audit_date_from")
        )
    else:
        audits = Audit.objects.none()

    context = {
        "user": request.user,
        "organization": organization,
        "audits": audits[:10],
        "audits_count": audits.count(),
    }
    return render(request, "identity/dashboard_client.html", context)


@login_required
def logout_view(request):
    """Logout view - accepts both GET and POST for convenience."""
    logout(request)
    return redirect("identity:login")


class CBAdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require CB Admin role."""

    def test_func(self):
        return self.request.user.groups.filter(name="cb_admin").exists()


# ---------------------------------------------------------------------------
# Auditor Qualification Views
# ---------------------------------------------------------------------------


class AuditorQualificationListView(LoginRequiredMixin, CBAdminRequiredMixin, ListView):
    model = AuditorQualification
    template_name = "identity/qualification_list.html"
    context_object_name = "qualifications"
    paginate_by = 20


class AuditorQualificationCreateView(LoginRequiredMixin, CBAdminRequiredMixin, CreateView):
    model = AuditorQualification
    form_class = AuditorQualificationForm
    template_name = "identity/qualification_form.html"
    success_url = reverse_lazy("identity:qualification_list")


class AuditorQualificationUpdateView(LoginRequiredMixin, CBAdminRequiredMixin, UpdateView):
    model = AuditorQualification
    form_class = AuditorQualificationForm
    template_name = "identity/qualification_form.html"
    success_url = reverse_lazy("identity:qualification_list")


# ---------------------------------------------------------------------------
# Auditor Training Views
# ---------------------------------------------------------------------------


class AuditorTrainingListView(LoginRequiredMixin, CBAdminRequiredMixin, ListView):
    model = AuditorTrainingRecord
    template_name = "identity/training_list.html"
    context_object_name = "training_records"
    paginate_by = 20


class AuditorTrainingCreateView(LoginRequiredMixin, CBAdminRequiredMixin, CreateView):
    model = AuditorTrainingRecord
    form_class = AuditorTrainingRecordForm
    template_name = "identity/training_form.html"
    success_url = reverse_lazy("identity:training_list")


class AuditorTrainingUpdateView(LoginRequiredMixin, CBAdminRequiredMixin, UpdateView):
    model = AuditorTrainingRecord
    form_class = AuditorTrainingRecordForm
    template_name = "identity/training_form.html"
    success_url = reverse_lazy("identity:training_list")


# ---------------------------------------------------------------------------
# Competence Evaluation Views
# ---------------------------------------------------------------------------


class CompetenceEvaluationListView(LoginRequiredMixin, CBAdminRequiredMixin, ListView):
    model = AuditorCompetenceEvaluation
    template_name = "identity/competence_list.html"
    context_object_name = "evaluations"
    paginate_by = 20


class CompetenceEvaluationCreateView(LoginRequiredMixin, CBAdminRequiredMixin, CreateView):
    model = AuditorCompetenceEvaluation
    form_class = AuditorCompetenceEvaluationForm
    template_name = "identity/competence_form.html"
    success_url = reverse_lazy("identity:competence_list")


class CompetenceEvaluationUpdateView(LoginRequiredMixin, CBAdminRequiredMixin, UpdateView):
    model = AuditorCompetenceEvaluation
    form_class = AuditorCompetenceEvaluationForm
    template_name = "identity/competence_form.html"
    success_url = reverse_lazy("identity:competence_list")


# ---------------------------------------------------------------------------
# Conflict of Interest Views
# ---------------------------------------------------------------------------


class ConflictOfInterestListView(LoginRequiredMixin, CBAdminRequiredMixin, ListView):
    model = ConflictOfInterest
    template_name = "identity/coi_list.html"
    context_object_name = "conflicts"
    paginate_by = 20


class ConflictOfInterestCreateView(LoginRequiredMixin, CBAdminRequiredMixin, CreateView):
    model = ConflictOfInterest
    form_class = ConflictOfInterestForm
    template_name = "identity/coi_form.html"
    success_url = reverse_lazy("identity:coi_list")


class ConflictOfInterestUpdateView(LoginRequiredMixin, CBAdminRequiredMixin, UpdateView):
    model = ConflictOfInterest
    form_class = ConflictOfInterestForm
    template_name = "identity/coi_form.html"
    success_url = reverse_lazy("identity:coi_list")
