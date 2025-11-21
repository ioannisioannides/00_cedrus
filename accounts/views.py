"""
Views for accounts app: login, logout, and role-based dashboards.
"""

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy


class CustomLoginView(LoginView):
    """Custom login view with template."""

    template_name = "accounts/login.html"
    redirect_authenticated_user = True  # Redirect if already logged in

    def get_success_url(self):
        """Redirect to appropriate dashboard based on user role."""
        return reverse_lazy("accounts:dashboard")


@login_required
def dashboard(request):
    """
    Role-based dashboard redirect.

    Redirects users to their appropriate dashboard based on their group membership.
    """
    user = request.user

    # Check groups in priority order
    if user.groups.filter(name="cb_admin").exists():
        return redirect("accounts:dashboard_cb")
    elif (
        user.groups.filter(name="lead_auditor").exists()
        or user.groups.filter(name="auditor").exists()
    ):
        return redirect("accounts:dashboard_auditor")
    elif (
        user.groups.filter(name="client_admin").exists()
        or user.groups.filter(name="client_user").exists()
    ):
        return redirect("accounts:dashboard_client")
    else:
        # No role assigned - show basic dashboard
        return render(
            request,
            "accounts/dashboard.html",
            {"user": user, "message": "No role assigned. Please contact an administrator."},
        )


@login_required
def dashboard_cb(request):
    """CB Admin dashboard."""
    if not request.user.groups.filter(name="cb_admin").exists():
        return redirect("accounts:dashboard")

    from audits.models import Audit
    from core.models import Certification, Organization

    context = {
        "user": request.user,
        "organizations_count": Organization.objects.count(),
        "certifications_count": Certification.objects.count(),
        "audits_count": Audit.objects.count(),
        "recent_audits": Audit.objects.all()[:5],
    }
    return render(request, "accounts/dashboard_cb.html", context)


@login_required
def dashboard_auditor(request):
    """Auditor dashboard."""
    if not (
        request.user.groups.filter(name="lead_auditor").exists()
        or request.user.groups.filter(name="auditor").exists()
    ):
        return redirect("accounts:dashboard")

    from django.db.models import Q

    from audits.models import Audit

    # Show audits where user is lead auditor or team member
    all_audits = (
        Audit.objects.filter(Q(lead_auditor=request.user) | Q(team_members__user=request.user))
        .distinct()
        .order_by("-total_audit_date_from")
    )

    context = {
        "user": request.user,
        "audits": all_audits[:10],
        "audits_count": all_audits.count(),
    }
    return render(request, "accounts/dashboard_auditor.html", context)


@login_required
def dashboard_client(request):
    """Client dashboard."""
    if not (
        request.user.groups.filter(name="client_admin").exists()
        or request.user.groups.filter(name="client_user").exists()
    ):
        return redirect("accounts:dashboard")

    from audits.models import Audit

    # Get user's organization
    organization = None
    if hasattr(request.user, "profile") and request.user.profile.organization:
        organization = request.user.profile.organization
        audits = Audit.objects.filter(organization=organization).order_by("-total_audit_date_from")
    else:
        audits = Audit.objects.none()

    context = {
        "user": request.user,
        "organization": organization,
        "audits": audits[:10],
        "audits_count": audits.count(),
    }
    return render(request, "accounts/dashboard_client.html", context)


@login_required
def logout_view(request):
    """Logout view - accepts both GET and POST for convenience."""
    logout(request)
    return redirect("accounts:login")
