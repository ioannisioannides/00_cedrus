"""
Views for audits app: create, list, detail, edit audits and findings.

Different views have different permission requirements:
- CB Admin: Can create audits, view all, edit recommendations
- Auditor: Can view/edit assigned audits, add findings
- Client: Can view their audits, respond to nonconformities
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db import models as django_models
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.models import Certification, Organization, Site
from trunk.permissions.mixins import AuditorRequiredMixin, CBAdminRequiredMixin, ClientRequiredMixin
from trunk.permissions.predicates import PermissionPredicate
from trunk.services.audit_service import AuditService
from trunk.services.finding_service import FindingService

from .documentation_forms import AuditChangesForm, AuditPlanReviewForm, AuditSummaryForm
from .file_forms import EvidenceFileForm
from .forms import (
    NonconformityForm,
    NonconformityResponseForm,
    NonconformityVerificationForm,
    ObservationForm,
    OpportunityForImprovementForm,
)
from .models import (
    Audit,
    AuditChanges,
    AuditPlanReview,
    AuditRecommendation,
    AuditSummary,
    AuditTeamMember,
    CertificationDecision,
    EvidenceFile,
    Nonconformity,
    Observation,
    OpportunityForImprovement,
    TechnicalReview,
)
from .recommendation_forms import AuditRecommendationForm
from .workflows import AuditWorkflow

# ============================================================================
# PERMISSION HELPER FUNCTIONS
# ============================================================================


def can_add_finding(user, audit):
    """Check if user can add findings to this audit."""
    # CB Admin can always add findings
    if user.groups.filter(name="cb_admin").exists():
        return True

    # Auditors can add findings if they're assigned to the audit
    if (
        user.groups.filter(name="lead_auditor").exists()
        or user.groups.filter(name="auditor").exists()
    ):
        return audit.lead_auditor == user or audit.team_members.filter(user=user).exists()

    return False


def can_edit_finding(user, finding):
    """Check if user can edit this finding."""
    audit = finding.audit

    # CB Admin can always edit
    if user.groups.filter(name="cb_admin").exists():
        return True

    # Creator can edit (if auditor)
    if finding.created_by == user:
        return can_add_finding(user, audit)

    # Lead auditor can edit findings in their audits
    if user.groups.filter(name="lead_auditor").exists() and audit.lead_auditor == user:
        return True

    return False


def can_respond_to_nc(user, nonconformity):
    """Check if user (client) can respond to this nonconformity."""
    audit = nonconformity.audit

    # Must be client user
    if not (
        user.groups.filter(name="client_admin").exists()
        or user.groups.filter(name="client_user").exists()
    ):
        return False

    # Must be for their organization
    if not hasattr(user, "profile") or not user.profile.organization:
        return False

    if audit.organization != user.profile.organization:
        return False

    # Audit must be in client_review status
    if audit.status != "client_review":
        return False

    # NC must be open or client_responded (can update response)
    if nonconformity.verification_status not in ["open", "client_responded"]:
        return False

    return True


def can_verify_nc(user, nonconformity):
    """Check if user (auditor) can verify this nonconformity."""
    audit = nonconformity.audit

    # Must be auditor
    if not (
        user.groups.filter(name="lead_auditor").exists()
        or user.groups.filter(name="auditor").exists()
    ):
        return False

    # Must be assigned to audit
    if not (audit.lead_auditor == user or audit.team_members.filter(user=user).exists()):
        return False

    # NC must be in client_responded status
    if nonconformity.verification_status != "client_responded":
        return False

    return True


# ============================================================================
# AUDIT VIEWS
# ============================================================================


# Audit List Views
class AuditListView(LoginRequiredMixin, ListView):
    """List audits - filtered by role."""

    model = Audit
    template_name = "audits/audit_list.html"
    context_object_name = "audits"
    paginate_by = 20

    def get_queryset(self):
        """
        Get queryset of audits filtered by user role.

        Role-based filtering:
            - CB Admin: sees all audits
            - Auditor/Lead Auditor: sees assigned audits only
            - Client: sees their organization's audits only

        Query Parameters:
            organization: Filter by organization ID
            status: Filter by audit status
            audit_type: Filter by audit type

        Returns:
            QuerySet of Audit objects with related data pre-fetched
        """
        user = self.request.user
        queryset = Audit.objects.select_related("organization", "lead_auditor", "created_by")

        # CB Admin sees all
        if PermissionPredicate.is_cb_admin(user):
            pass  # Show all
        # Auditor sees assigned audits
        elif PermissionPredicate.is_auditor(user):
            queryset = queryset.filter(
                django_models.Q(lead_auditor=user) | django_models.Q(team_members__user=user)
            ).distinct()
        # Client sees their organization's audits
        elif PermissionPredicate.is_client_user(user):
            if hasattr(user, "profile") and user.profile.organization:
                queryset = queryset.filter(organization=user.profile.organization)
            else:
                queryset = queryset.none()
        else:
            queryset = queryset.none()

        # Apply filters
        org_id = self.request.GET.get("organization")
        if org_id:
            queryset = queryset.filter(organization_id=org_id)

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        audit_type = self.request.GET.get("audit_type")
        if audit_type:
            queryset = queryset.filter(audit_type=audit_type)

        return queryset.order_by("-total_audit_date_from", "-created_at")

    def get_context_data(self, **kwargs):
        """Add organizations to context for filter dropdown."""
        context = super().get_context_data(**kwargs)
        context["organizations"] = Organization.objects.all()
        return context


# Audit Create View (CB Admin only)
class AuditCreateView(LoginRequiredMixin, CBAdminRequiredMixin, CreateView):
    """Create a new audit (CB Admin only)."""

    model = Audit
    template_name = "audits/audit_form.html"
    fields = [
        "organization",
        "certifications",
        "sites",
        "audit_type",
        "total_audit_date_from",
        "total_audit_date_to",
        "planned_duration_hours",
        "lead_auditor",
        "status",
    ]

    def form_valid(self, form):
        """
        Create audit using AuditService and redirect to detail view.

        Args:
            form: Validated audit form data

        Returns:
            HttpResponse redirect to audit detail page
        """
        self.object = AuditService.create_audit(
            organization=form.cleaned_data["organization"],
            certifications=form.cleaned_data["certifications"],
            sites=form.cleaned_data["sites"],
            audit_data=form.cleaned_data,
            created_by=self.request.user,
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.object.pk})


# Audit Detail View (role-based permissions)
class AuditDetailView(LoginRequiredMixin, DetailView):
    """View audit details with role-based access control."""

    model = Audit
    template_name = "audits/audit_detail.html"
    context_object_name = "audit"

    def get_queryset(self):
        """Get audit queryset with optimized relationships based on user role."""
        user = self.request.user
        queryset = Audit.objects.select_related(
            "organization", "lead_auditor", "created_by"
        ).prefetch_related(
            "certifications",
            "sites",
            "team_members",
            "nonconformity_set",
            "observation_set",
            "opportunityforimprovement_set",
        )

        # CB Admin sees all
        if PermissionPredicate.is_cb_admin(user):
            return queryset

        # Auditor sees assigned audits
        if PermissionPredicate.is_auditor(user):
            return queryset.filter(
                django_models.Q(lead_auditor=user) | django_models.Q(team_members__user=user)
            ).distinct()

        # Client sees their organization's audits
        if PermissionPredicate.is_client_user(user):
            if hasattr(user, "profile") and user.profile.organization:
                return queryset.filter(organization=user.profile.organization)

        return queryset.none()

    def get_context_data(self, **kwargs):
        """Add additional context data to template."""
        context = super().get_context_data(**kwargs)
        audit = self.object
        user = self.request.user

        # Get related objects
        context["nonconformities"] = audit.nonconformity_set.all()
        context["observations"] = audit.observation_set.all()
        context["ofis"] = audit.opportunityforimprovement_set.all()

        # Add counts
        context["open_ncs_count"] = audit.nonconformity_set.exclude(
            verification_status="closed"
        ).count()

        # Check if user can edit
        context["can_edit"] = PermissionPredicate.is_cb_admin(user) or (
            PermissionPredicate.is_lead_auditor(user) and audit.lead_auditor == user
        )

        # Check if user is client
        context["is_client"] = PermissionPredicate.is_client_user(user)

        # Check if user can add findings
        context["can_add_findings"] = can_add_finding(user, audit) and audit.status != "decided"

        # Get available status transitions
        workflow = AuditWorkflow(audit)
        context["available_transitions"] = workflow.get_available_transitions(user)

        # Check if user can submit to client
        context["can_submit_to_client"] = (
            audit.status == "draft"
            and PermissionPredicate.is_lead_auditor(user)
            and audit.lead_auditor == user
        )

        # Check if user can make decision
        context["can_make_decision"] = (
            audit.status == "submitted_to_cb" and PermissionPredicate.is_cb_admin(user)
        )

        # Get or create related records
        context["changes"], _ = AuditChanges.objects.get_or_create(audit=audit)
        context["plan_review"], _ = AuditPlanReview.objects.get_or_create(audit=audit)
        context["summary"], _ = AuditSummary.objects.get_or_create(audit=audit)
        context["recommendation"], _ = AuditRecommendation.objects.get_or_create(audit=audit)

        # Multi-site sampling information (Sprint 8 - IAF MD1)
        total_sites = audit.sites.count()
        if total_sites > 1:
            from trunk.services.sampling import calculate_sample_size

            # Check if this is initial certification
            is_initial = audit.audit_type in ["stage1", "stage2"]

            # Calculate sampling requirements
            try:
                sampling_info = calculate_sample_size(
                    total_sites=total_sites, is_initial_certification=is_initial
                )
                context["sampling_info"] = sampling_info
                context["is_multi_site"] = True
            except (ValueError, TypeError, ZeroDivisionError) as e:
                # Sampling calculation failed, don't block page load
                context["sampling_error"] = str(e)
                context["is_multi_site"] = True
        else:
            context["is_multi_site"] = False

        return context


# Audit Update View (CB Admin and Lead Auditor)
class AuditUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update audit (CB Admin or Lead Auditor of the audit)."""

    model = Audit
    template_name = "audits/audit_form.html"
    fields = [
        "organization",
        "certifications",
        "sites",
        "audit_type",
        "total_audit_date_from",
        "total_audit_date_to",
        "planned_duration_hours",
        "lead_auditor",
    ]  # Removed "status" - status changes via workflow only

    def test_func(self):
        """Check if user can edit this audit."""
        user = self.request.user
        audit = self.get_object()

        if PermissionPredicate.is_cb_admin(user):
            return True

        if (
            PermissionPredicate.is_lead_auditor(user)
            and audit.lead_auditor == user
            and audit.status == "draft"
        ):
            return True

        return False

    def form_valid(self, form):
        """Update audit using AuditService."""
        self.object = AuditService.update_audit(audit=self.object, data=form.cleaned_data)
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.object.pk})


# Audit Print View
@login_required
def audit_print(request, pk):
    """Print-friendly view of audit."""
    audit = get_object_or_404(Audit, pk=pk)

    # Permission check using centralized predicate
    if not PermissionPredicate.can_view_audit(request.user, audit):
        return redirect("audits:audit_list")

    context = {
        "audit": audit,
        "nonconformities": audit.nonconformity_set.all(),
        "observations": audit.observation_set.all(),
        "ofis": audit.opportunityforimprovement_set.all(),
    }

    # Get or create related records
    context["changes"], _ = AuditChanges.objects.get_or_create(audit=audit)
    context["plan_review"], _ = AuditPlanReview.objects.get_or_create(audit=audit)
    context["summary"], _ = AuditSummary.objects.get_or_create(audit=audit)
    context["recommendation"], _ = AuditRecommendation.objects.get_or_create(audit=audit)

    return render(request, "audits/audit_print.html", context)


# ============================================================================
# STATUS WORKFLOW VIEWS
# ============================================================================


@login_required
def audit_transition_status(request, pk, new_status):
    """
    Handle audit status transitions via workflow.

    This view enforces workflow rules and validates transitions.
    """
    audit = get_object_or_404(Audit, pk=pk)
    user = request.user

    # Permission check - only lead auditor or CB admin can transition
    can_transition_audit = user.groups.filter(name="cb_admin").exists() or (
        user.groups.filter(name="lead_auditor").exists() and audit.lead_auditor == user
    )
    if not can_transition_audit:
        messages.error(request, "You do not have permission to change this audit's status.")
        return redirect("audits:audit_detail", pk=pk)

    workflow = AuditWorkflow(audit)

    try:
        # Validate and perform the transition
        workflow.transition(new_status, user)

        # Success messages based on transition
        if new_status == "client_review":
            messages.success(request, "Audit submitted to client for review.")
        elif new_status == "submitted":
            messages.success(request, "Audit submitted to Certification Body for decision.")
        elif new_status == "decided":
            messages.success(request, "Certification decision has been made.")
        else:
            messages.success(request, f"Audit status updated to {audit.get_status_display()}.")

    except ValidationError as e:
        messages.error(request, str(e))

    return redirect("audits:audit_detail", pk=pk)


# ============================================================================
# AUDIT DOCUMENTATION VIEWS
# ============================================================================


@login_required
def audit_changes_edit(request, audit_pk):
    """Edit organization changes for an audit."""
    audit = get_object_or_404(Audit, pk=audit_pk)

    # Permission check
    user = request.user
    can_edit = user.groups.filter(name="cb_admin").exists() or (
        user.groups.filter(name="lead_auditor").exists() and audit.lead_auditor == user
    )
    if not can_edit:
        messages.error(request, "You do not have permission to edit this audit's documentation.")
        return redirect("audits:audit_detail", pk=audit_pk)

    changes, _ = AuditChanges.objects.get_or_create(audit=audit)

    if request.method == "POST":
        form = AuditChangesForm(request.POST, instance=changes)
        if form.is_valid():
            form.save()
            messages.success(request, "Organization changes updated successfully.")
            return redirect("audits:audit_detail", pk=audit_pk)
    else:
        form = AuditChangesForm(instance=changes)

    return render(
        request,
        "audits/audit_changes_form.html",
        {"form": form, "audit": audit, "changes": changes},
    )


@login_required
def audit_plan_review_edit(request, audit_pk):
    """Edit audit plan review for an audit."""
    audit = get_object_or_404(Audit, pk=audit_pk)

    # Permission check
    user = request.user
    can_edit = user.groups.filter(name="cb_admin").exists() or (
        user.groups.filter(name="lead_auditor").exists() and audit.lead_auditor == user
    )
    if not can_edit:
        messages.error(request, "You do not have permission to edit this audit's documentation.")
        return redirect("audits:audit_detail", pk=audit_pk)

    plan_review, _ = AuditPlanReview.objects.get_or_create(audit=audit)

    if request.method == "POST":
        form = AuditPlanReviewForm(request.POST, instance=plan_review)
        if form.is_valid():
            form.save()
            messages.success(request, "Audit plan review updated successfully.")
            return redirect("audits:audit_detail", pk=audit_pk)
    else:
        form = AuditPlanReviewForm(instance=plan_review)

    return render(
        request,
        "audits/audit_plan_review_form.html",
        {"form": form, "audit": audit, "plan_review": plan_review},
    )


@login_required
def audit_summary_edit(request, audit_pk):
    """Edit audit summary for an audit."""
    audit = get_object_or_404(Audit, pk=audit_pk)

    # Permission check
    user = request.user
    can_edit = user.groups.filter(name="cb_admin").exists() or (
        user.groups.filter(name="lead_auditor").exists() and audit.lead_auditor == user
    )
    if not can_edit:
        messages.error(request, "You do not have permission to edit this audit's documentation.")
        return redirect("audits:audit_detail", pk=audit_pk)

    summary, _ = AuditSummary.objects.get_or_create(audit=audit)

    if request.method == "POST":
        form = AuditSummaryForm(request.POST, instance=summary)
        if form.is_valid():
            form.save()
            messages.success(request, "Audit summary updated successfully.")
            return redirect("audits:audit_detail", pk=audit_pk)
    else:
        form = AuditSummaryForm(instance=summary)

        return render(
            request,
            "audits/audit_summary_form.html",
            {"form": form, "audit": audit, "summary": summary},
        )


# ============================================================================
# RECOMMENDATIONS & DECISION VIEWS
# ============================================================================


@login_required
def audit_recommendation_edit(request, audit_pk):
    """Edit audit recommendations."""
    audit = get_object_or_404(Audit, pk=audit_pk)

    # Permission check - Lead Auditor or CB Admin
    user = request.user
    can_edit = user.groups.filter(name="cb_admin").exists() or (
        user.groups.filter(name="lead_auditor").exists() and audit.lead_auditor == user
    )
    if not can_edit:
        messages.error(request, "You do not have permission to edit recommendations.")
        return redirect("audits:audit_detail", pk=audit_pk)

    recommendation, _ = AuditRecommendation.objects.get_or_create(audit=audit)

    if request.method == "POST":
        form = AuditRecommendationForm(request.POST, instance=recommendation)
        if form.is_valid():
            form.save()
            messages.success(request, "Recommendations updated successfully.")
            return redirect("audits:audit_detail", pk=audit_pk)
    else:
        form = AuditRecommendationForm(instance=recommendation)

    return render(
        request,
        "audits/audit_recommendation_form.html",
        {"form": form, "audit": audit, "recommendation": recommendation},
    )


@login_required
def audit_make_decision(request, audit_pk):
    """Make certification decision for an audit."""
    audit = get_object_or_404(Audit, pk=audit_pk)

    # Only CB Admin can make decisions
    if not PermissionPredicate.is_cb_admin(request.user):
        messages.error(
            request, "Only Certification Body Administrators can make certification decisions."
        )
        return redirect("audits:audit_detail", pk=audit_pk)

    # Audit must be in submitted_to_cb status
    if audit.status != "submitted_to_cb":
        messages.error(request, "Audit must be in 'Submitted to CB' status to make a decision.")
        return redirect("audits:audit_detail", pk=audit_pk)

    recommendation, _ = AuditRecommendation.objects.get_or_create(audit=audit)

    if request.method == "POST":
        # Update recommendation if provided
        form = AuditRecommendationForm(request.POST, instance=recommendation)
        if form.is_valid():
            form.save()

            # Transition to decided status
            try:
                workflow = AuditWorkflow(audit)
                workflow.transition("decided", request.user)

                # Update certification statuses based on recommendations
                # This is a simplified version - can be enhanced
                if recommendation.suspension_recommended:
                    # Update certifications to suspended
                    for cert in audit.certifications.all():
                        cert.certificate_status = "suspended"
                        cert.save()

                if recommendation.revocation_recommended:
                    # Update certifications to withdrawn
                    for cert in audit.certifications.all():
                        cert.certificate_status = "withdrawn"
                        cert.save()

                messages.success(
                    request, "Certification decision has been made and audit is now decided."
                )
                return redirect("audits:audit_detail", pk=audit_pk)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = AuditRecommendationForm(instance=recommendation)

    return render(
        request,
        "audits/audit_decision_form.html",
        {"form": form, "audit": audit, "recommendation": recommendation},
    )


# ============================================================================
# EVIDENCE FILE MANAGEMENT VIEWS
# ============================================================================


@login_required
def evidence_file_upload(request, audit_pk):
    """Upload evidence file to an audit."""
    audit = get_object_or_404(Audit, pk=audit_pk)

    # Permission check - auditors and clients can upload
    user = request.user
    can_upload = (
        PermissionPredicate.is_cb_admin(user)
        or can_add_finding(user, audit)
        or (
            PermissionPredicate.is_client_user(user)
            and hasattr(user, "profile")
            and user.profile.organization == audit.organization
        )
    )

    if not can_upload:
        messages.error(request, "You do not have permission to upload files to this audit.")
        return redirect("audits:audit_detail", pk=audit_pk)

    if request.method == "POST":
        form = EvidenceFileForm(request.POST, request.FILES, audit=audit)
        if form.is_valid():
            evidence_file = form.save(commit=False)
            evidence_file.audit = audit
            evidence_file.uploaded_by = user
            evidence_file.save()
            messages.success(request, "File uploaded successfully.")
            return redirect("audits:audit_detail", pk=audit_pk)
    else:
        form = EvidenceFileForm(audit=audit)

    return render(request, "audits/evidence_file_upload.html", {"form": form, "audit": audit})


@login_required
def evidence_file_download(request, file_pk):
    """Download an evidence file."""
    from django.http import FileResponse, Http404

    evidence_file = get_object_or_404(EvidenceFile, pk=file_pk)
    audit = evidence_file.audit

    # Permission check - same as viewing audit
    user = request.user
    can_view = False

    if user.groups.filter(name="cb_admin").exists():
        can_view = True
    elif (
        user.groups.filter(name="lead_auditor").exists()
        or user.groups.filter(name="auditor").exists()
    ):
        can_view = audit.lead_auditor == user or audit.team_members.filter(user=user).exists()
    elif (
        user.groups.filter(name="client_admin").exists()
        or user.groups.filter(name="client_user").exists()
    ):
        if hasattr(user, "profile") and user.profile.organization:
            can_view = audit.organization == user.profile.organization

    if not can_view:
        raise Http404("File not found or access denied.")

    try:
        response = FileResponse(
            evidence_file.file.open(),
            as_attachment=True,
            filename=evidence_file.file.name.split("/")[-1],
        )
        return response
    except FileNotFoundError:
        raise Http404("File not found on server.")


@login_required
def evidence_file_delete(request, file_pk):
    """Delete an evidence file."""
    evidence_file = get_object_or_404(EvidenceFile, pk=file_pk)
    audit = evidence_file.audit

    # Permission check - uploader or CB Admin can delete
    user = request.user
    can_delete = user.groups.filter(name="cb_admin").exists() or evidence_file.uploaded_by == user

    if not can_delete:
        messages.error(request, "You do not have permission to delete this file.")
        return redirect("audits:audit_detail", pk=audit.pk)

    if request.method == "POST":
        audit_pk = audit.pk
        evidence_file.file.delete()  # Delete file from storage
        evidence_file.delete()  # Delete database record
        messages.success(request, "File deleted successfully.")
        return redirect("audits:audit_detail", pk=audit_pk)

    return render(
        request,
        "audits/evidence_file_delete.html",
        {"evidence_file": evidence_file, "audit": audit},
    )


# ============================================================================
# FINDING VIEWS
# ============================================================================


# Nonconformity Views
class NonconformityCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new nonconformity."""

    model = Nonconformity
    form_class = NonconformityForm
    template_name = "audits/nonconformity_form.html"

    def test_func(self):
        """Check if user can create nonconformities for this audit."""
        audit = get_object_or_404(Audit, pk=self.kwargs["audit_pk"])
        # Check audit status allows findings
        if audit.status == "decided":
            return False
        return can_add_finding(self.request.user, audit)

    def get_audit(self):
        """Retrieve the audit instance from URL parameters."""
        return get_object_or_404(Audit, pk=self.kwargs["audit_pk"])

    def get_form_kwargs(self):
        """Pass additional kwargs to form initialization."""
        kwargs = super().get_form_kwargs()
        kwargs["audit"] = self.get_audit()
        return kwargs

    def form_valid(self, form):
        """Create nonconformity using FindingService."""
        audit = self.get_audit()
        # Use FindingService to create nonconformity
        FindingService.create_nonconformity(
            audit=audit, user=self.request.user, data=form.cleaned_data
        )
        messages.success(self.request, "Nonconformity created successfully.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.kwargs["audit_pk"]})

    def get_context_data(self, **kwargs):
        """Add additional context data to template."""
        context = super().get_context_data(**kwargs)
        context["audit"] = self.get_audit()
        context["finding_type"] = "Nonconformity"
        return context


class NonconformityDetailView(LoginRequiredMixin, DetailView):
    """View nonconformity details."""

    model = Nonconformity
    template_name = "audits/nonconformity_detail.html"
    context_object_name = "nc"

    def get_queryset(self):
        """Get nonconformity queryset with role-based filtering."""
        # Use same permission logic as audit detail
        user = self.request.user
        queryset = Nonconformity.objects.select_related(
            "audit", "standard", "created_by", "verified_by"
        )

        if user.groups.filter(name="cb_admin").exists():
            return queryset

        if (
            user.groups.filter(name="lead_auditor").exists()
            or user.groups.filter(name="auditor").exists()
        ):
            return queryset.filter(
                django_models.Q(audit__lead_auditor=user)
                | django_models.Q(audit__team_members__user=user)
            ).distinct()

        if (
            user.groups.filter(name="client_admin").exists()
            or user.groups.filter(name="client_user").exists()
        ):
            if hasattr(user, "profile") and user.profile.organization:
                return queryset.filter(audit__organization=user.profile.organization)

        return queryset.none()

    def get_context_data(self, **kwargs):
        """Add permission flags to template context."""
        context = super().get_context_data(**kwargs)
        nc = self.object
        user = self.request.user

        context["can_edit"] = can_edit_finding(user, nc)
        context["can_respond"] = can_respond_to_nc(user, nc)
        context["can_verify"] = can_verify_nc(user, nc)
        context["is_client"] = (
            user.groups.filter(name="client_admin").exists()
            or user.groups.filter(name="client_user").exists()
        )
        return context


class NonconformityUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update a nonconformity."""

    model = Nonconformity
    form_class = NonconformityForm
    template_name = "audits/nonconformity_form.html"

    def test_func(self):
        """Check if user can update this nonconformity."""
        nc = self.get_object()
        # Can't edit if audit is decided
        if nc.audit.status == "decided":
            return False
        return can_edit_finding(self.request.user, nc)

    def get_form_kwargs(self):
        """Pass additional kwargs to form initialization."""
        kwargs = super().get_form_kwargs()
        kwargs["audit"] = self.object.audit
        return kwargs

    def form_valid(self, form):
        """Process valid form submission."""
        messages.success(self.request, "Nonconformity updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:nonconformity_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        """Add additional context data to template."""
        context = super().get_context_data(**kwargs)
        context["audit"] = self.object.audit
        context["finding_type"] = "Nonconformity"
        return context


class NonconformityResponseView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Client response to nonconformity."""

    model = Nonconformity
    form_class = NonconformityResponseForm
    template_name = "audits/nonconformity_response.html"
    context_object_name = "nc"

    def test_func(self):
        """Check if user has permission to access this view."""
        return can_respond_to_nc(self.request.user, self.get_object())

    def form_valid(self, form):
        """Process valid form submission."""
        # Use FindingService to handle response
        FindingService.respond_to_nonconformity(nc=self.object, response_data=form.cleaned_data)
        messages.success(self.request, "Response submitted successfully.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:nonconformity_detail", kwargs={"pk": self.object.pk})


class NonconformityVerifyView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Auditor verification of nonconformity response."""

    model = Nonconformity
    form_class = NonconformityVerificationForm
    template_name = "audits/nonconformity_verify.html"
    context_object_name = "nc"

    def test_func(self):
        """Check if user has permission to access this view."""
        return can_verify_nc(self.request.user, self.get_object())

    def form_valid(self, form):
        """Process valid form submission."""
        try:
            # Use FindingService to verify
            FindingService.verify_nonconformity(
                nc=self.object,
                user=self.request.user,
                action=form.cleaned_data["verification_action"],
                notes=form.cleaned_data.get("verification_notes"),
            )

            action = form.cleaned_data["verification_action"]
            if action == "accept":
                messages.success(self.request, "Response accepted.")
            elif action == "request_changes":
                messages.info(self.request, "Changes requested. Client can update their response.")
            elif action == "close":
                messages.success(self.request, "Nonconformity closed.")

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:nonconformity_detail", kwargs={"pk": self.object.pk})


# Observation Views
class ObservationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new observation."""

    model = Observation
    form_class = ObservationForm
    template_name = "audits/observation_form.html"

    def test_func(self):
        """Check if user has permission to access this view."""
        audit = get_object_or_404(Audit, pk=self.kwargs["audit_pk"])
        if audit.status == "decided":
            return False
        return can_add_finding(self.request.user, audit)

    def get_audit(self):
        """Retrieve the audit instance from URL parameters."""
        return get_object_or_404(Audit, pk=self.kwargs["audit_pk"])

    def get_form_kwargs(self):
        """Pass additional kwargs to form initialization."""
        kwargs = super().get_form_kwargs()
        kwargs["audit"] = self.get_audit()
        return kwargs

    def form_valid(self, form):
        """Process valid form submission."""
        audit = self.get_audit()
        # Use FindingService to create observation
        FindingService.create_observation(
            audit=audit, user=self.request.user, data=form.cleaned_data
        )
        messages.success(self.request, "Observation created successfully.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.kwargs["audit_pk"]})

    def get_context_data(self, **kwargs):
        """Add additional context data to template."""
        context = super().get_context_data(**kwargs)
        context["audit"] = self.get_audit()
        context["finding_type"] = "Observation"
        return context


class ObservationDetailView(LoginRequiredMixin, DetailView):
    """View observation details."""

    model = Observation
    template_name = "audits/observation_detail.html"
    context_object_name = "observation"

    def get_queryset(self):
        """Get observation queryset with role-based filtering."""
        user = self.request.user
        queryset = Observation.objects.select_related("audit", "standard", "created_by")

        if PermissionPredicate.is_cb_admin(user):
            return queryset

        if PermissionPredicate.is_auditor(user):
            return queryset.filter(
                django_models.Q(audit__lead_auditor=user)
                | django_models.Q(audit__team_members__user=user)
            ).distinct()

        if PermissionPredicate.is_client_user(user):
            if hasattr(user, "profile") and user.profile.organization:
                return queryset.filter(audit__organization=user.profile.organization)

        return queryset.none()

    def get_context_data(self, **kwargs):
        """Add permission flags to template context."""
        context = super().get_context_data(**kwargs)
        observation = self.object
        user = self.request.user

        context["can_edit"] = (
            can_edit_finding(user, observation) and observation.audit.status != "decided"
        )
        context["audit"] = observation.audit
        return context


class ObservationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an observation."""

    model = Observation
    form_class = ObservationForm
    template_name = "audits/observation_form.html"

    def test_func(self):
        """Check if user has permission to access this view."""
        obs = self.get_object()
        if obs.audit.status == "decided":
            return False
        return can_edit_finding(self.request.user, obs)

    def get_form_kwargs(self):
        """Pass additional kwargs to form initialization."""
        kwargs = super().get_form_kwargs()
        kwargs["audit"] = self.object.audit
        return kwargs

    def form_valid(self, form):
        """Process valid form submission."""
        messages.success(self.request, "Observation updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.object.audit.pk})

    def get_context_data(self, **kwargs):
        """Add additional context data to template."""
        context = super().get_context_data(**kwargs)
        context["audit"] = self.object.audit
        context["finding_type"] = "Observation"
        return context


# Opportunity for Improvement Views
class OpportunityForImprovementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new opportunity for improvement."""

    model = OpportunityForImprovement
    form_class = OpportunityForImprovementForm
    template_name = "audits/ofi_form.html"

    def test_func(self):
        """Check if user has permission to access this view."""
        audit = get_object_or_404(Audit, pk=self.kwargs["audit_pk"])
        if audit.status == "decided":
            return False
        return can_add_finding(self.request.user, audit)

    def get_audit(self):
        """Retrieve the audit instance from URL parameters."""
        return get_object_or_404(Audit, pk=self.kwargs["audit_pk"])

    def get_form_kwargs(self):
        """Pass additional kwargs to form initialization."""
        kwargs = super().get_form_kwargs()
        kwargs["audit"] = self.get_audit()
        return kwargs

    def form_valid(self, form):
        """Process valid form submission."""
        audit = self.get_audit()
        # Use FindingService to create OFI
        FindingService.create_ofi(audit=audit, user=self.request.user, data=form.cleaned_data)
        messages.success(self.request, "Opportunity for Improvement created successfully.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.kwargs["audit_pk"]})

    def get_context_data(self, **kwargs):
        """Add additional context data to template."""
        context = super().get_context_data(**kwargs)
        context["audit"] = self.get_audit()
        context["finding_type"] = "Opportunity for Improvement"
        return context


class OpportunityForImprovementDetailView(LoginRequiredMixin, DetailView):
    """View opportunity for improvement details."""

    model = OpportunityForImprovement
    template_name = "audits/ofi_detail.html"
    context_object_name = "ofi"

    def get_queryset(self):
        """Get OFI queryset with role-based filtering."""
        user = self.request.user
        queryset = OpportunityForImprovement.objects.select_related(
            "audit", "standard", "created_by"
        )

        if PermissionPredicate.is_cb_admin(user):
            return queryset

        if PermissionPredicate.is_auditor(user):
            return queryset.filter(
                django_models.Q(audit__lead_auditor=user)
                | django_models.Q(audit__team_members__user=user)
            ).distinct()

        if PermissionPredicate.is_client_user(user):
            if hasattr(user, "profile") and user.profile.organization:
                return queryset.filter(audit__organization=user.profile.organization)

        return queryset.none()

    def get_context_data(self, **kwargs):
        """Add permission flags to template context."""
        context = super().get_context_data(**kwargs)
        ofi = self.object
        user = self.request.user

        context["can_edit"] = can_edit_finding(user, ofi) and ofi.audit.status != "decided"
        context["audit"] = ofi.audit
        return context


class OpportunityForImprovementUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an opportunity for improvement."""

    model = OpportunityForImprovement
    form_class = OpportunityForImprovementForm
    template_name = "audits/ofi_form.html"

    def test_func(self):
        """Check if user has permission to access this view."""
        ofi = self.get_object()
        if ofi.audit.status == "decided":
            return False
        return can_edit_finding(self.request.user, ofi)

    def get_form_kwargs(self):
        """Pass additional kwargs to form initialization."""
        kwargs = super().get_form_kwargs()
        kwargs["audit"] = self.object.audit
        return kwargs

    def form_valid(self, form):
        """Process valid form submission."""
        messages.success(self.request, "Opportunity for Improvement updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.object.audit.pk})

    def get_context_data(self, **kwargs):
        """Add additional context data to template."""
        context = super().get_context_data(**kwargs)
        context["audit"] = self.object.audit
        context["finding_type"] = "Opportunity for Improvement"
        return context


# Delete Views (for all finding types)


class NonconformityDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a nonconformity."""

    model = Nonconformity

    def test_func(self):
        """Check if user has permission to access this view."""
        nc = self.get_object()
        if nc.audit.status == "decided":
            return False
        return can_edit_finding(self.request.user, nc)

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.object.audit.pk})

    def delete(self, request, *args, **kwargs):
        """Handle deletion with success message."""
        messages.success(request, "Nonconformity deleted successfully.")
        return super().delete(request, *args, **kwargs)


class ObservationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an observation."""

    model = Observation

    def test_func(self):
        """Check if user has permission to access this view."""
        obs = self.get_object()
        if obs.audit.status == "decided":
            return False
        return can_edit_finding(self.request.user, obs)

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.object.audit.pk})

    def delete(self, request, *args, **kwargs):
        """Handle deletion with success message."""
        messages.success(request, "Observation deleted successfully.")
        return super().delete(request, *args, **kwargs)


class OpportunityForImprovementDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an opportunity for improvement."""

    model = OpportunityForImprovement

    def test_func(self):
        """Check if user has permission to access this view."""
        ofi = self.get_object()
        if ofi.audit.status == "decided":
            return False
        return can_edit_finding(self.request.user, ofi)

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.object.audit.pk})

    def delete(self, request, *args, **kwargs):
        """Handle deletion with success message."""
        messages.success(request, "Opportunity for Improvement deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# TECHNICAL REVIEW AND CERTIFICATION DECISION VIEWS (ISO 17021 Compliance)
# ============================================================================


class TechnicalReviewView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Technical Review (ISO 17021 Clause 9.5).
    Only CB Technical Reviewers or CB Admins can conduct reviews.
    """

    model = TechnicalReview
    template_name = "audits/technical_review_form.html"
    fields = [
        "scope_verified",
        "objectives_verified",
        "findings_reviewed",
        "conclusion_clear",
        "reviewer_notes",
        "clarification_requested",
        "status",
    ]

    def test_func(self):
        """Only technical reviewers or CB admins can access."""
        audit = get_object_or_404(Audit, pk=self.kwargs["audit_pk"])

        # Check audit is in technical_review status
        if audit.status != "technical_review":
            return False

        # Check user has permission
        return PermissionPredicate.can_conduct_technical_review(self.request.user)

    def get_context_data(self, **kwargs):
        """Add additional context data to template."""
        context = super().get_context_data(**kwargs)
        context["audit"] = get_object_or_404(Audit, pk=self.kwargs["audit_pk"])
        return context

    def form_valid(self, form):
        """Process valid form submission."""
        audit = get_object_or_404(Audit, pk=self.kwargs["audit_pk"])

        # Check if technical review already exists
        if hasattr(audit, "technicalreview"):
            messages.error(self.request, "Technical review already exists for this audit.")
            return redirect("audits:audit_detail", pk=audit.pk)

        # Create technical review
        form.instance.audit = audit
        form.instance.reviewer = self.request.user
        self.object = form.save()

        # If approved, transition to decision_pending
        if self.object.status == "approved":
            try:
                workflow = AuditWorkflow(audit)
                workflow.transition(
                    "decision_pending",
                    self.request.user,
                    notes=f"Technical review approved by {self.request.user.get_full_name()}",
                )
                messages.success(
                    self.request, "Technical review completed. Audit moved to decision pending."
                )
            except ValidationError as e:
                messages.error(self.request, f"Error transitioning audit: {e}")
        else:
            messages.success(
                self.request, "Technical review saved. Audit remains in technical review status."
            )

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.kwargs["audit_pk"]})


class TechnicalReviewUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update technical review."""

    model = TechnicalReview
    template_name = "audits/technical_review_form.html"
    fields = [
        "scope_verified",
        "objectives_verified",
        "findings_reviewed",
        "conclusion_clear",
        "reviewer_notes",
        "clarification_requested",
        "status",
    ]

    def test_func(self):
        """Only technical reviewers or CB admins can update."""
        return PermissionPredicate.can_conduct_technical_review(self.request.user)

    def form_valid(self, form):
        """Process valid form submission."""
        self.object = form.save()

        # If approved and audit still in technical_review, transition
        if self.object.status == "approved" and self.object.audit.status == "technical_review":
            try:
                workflow = AuditWorkflow(self.object.audit)
                workflow.transition(
                    "decision_pending",
                    self.request.user,
                    notes=f"Technical review approved by {self.request.user.get_full_name()}",
                )
                messages.success(
                    self.request, "Technical review approved. Audit moved to decision pending."
                )
            except ValidationError as e:
                messages.error(self.request, f"Error transitioning audit: {e}")
        else:
            messages.success(self.request, "Technical review updated.")

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.object.audit.pk})


class CertificationDecisionView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Certification Decision (ISO 17021 Clause 9.6).
    Only CB Decision Makers or CB Admins can make decisions.
    """

    model = CertificationDecision
    template_name = "audits/certification_decision_form.html"
    fields = ["decision", "decision_notes", "certifications_affected"]

    def test_func(self):
        """Only decision makers or CB admins can access."""
        audit = get_object_or_404(Audit, pk=self.kwargs["audit_pk"])

        # Check audit is in decision_pending status
        if audit.status != "decision_pending":
            return False

        # Check user has permission
        return PermissionPredicate.can_make_certification_decision(self.request.user)

    def get_context_data(self, **kwargs):
        """Add additional context data to template."""
        context = super().get_context_data(**kwargs)
        audit = get_object_or_404(Audit, pk=self.kwargs["audit_pk"])
        context["audit"] = audit
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit certifications to those associated with this audit
        audit = get_object_or_404(Audit, pk=self.kwargs["audit_pk"])
        form.fields["certifications_affected"].queryset = audit.certifications.all()
        return form

    def form_valid(self, form):
        """Process valid form submission."""
        audit = get_object_or_404(Audit, pk=self.kwargs["audit_pk"])

        # Check if decision already exists
        if hasattr(audit, "certificationdecision"):
            messages.error(self.request, "Certification decision already exists for this audit.")
            return redirect("audits:audit_detail", pk=audit.pk)

        # Create certification decision
        form.instance.audit = audit
        form.instance.decision_maker = self.request.user
        self.object = form.save()

        # Transition to closed
        try:
            workflow = AuditWorkflow(audit)
            workflow.transition(
                "closed",
                self.request.user,
                notes=f"Decision: {self.object.get_decision_display()} by {self.request.user.get_full_name()}",
            )
            messages.success(
                self.request,
                f"Certification decision made: {self.object.get_decision_display()}. Audit closed.",
            )
        except ValidationError as e:
            messages.error(self.request, f"Error transitioning audit: {e}")

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.kwargs["audit_pk"]})


class CertificationDecisionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update certification decision."""

    model = CertificationDecision
    template_name = "audits/certification_decision_form.html"
    fields = ["decision", "decision_notes", "certifications_affected"]

    def test_func(self):
        """Only decision makers or CB admins can update."""
        return PermissionPredicate.can_make_certification_decision(self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit certifications to those associated with this audit
        form.fields["certifications_affected"].queryset = self.object.audit.certifications.all()
        return form

    def form_valid(self, form):
        """Process valid form submission."""
        self.object = form.save()
        messages.success(self.request, "Certification decision updated.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audits:audit_detail", kwargs={"pk": self.object.audit.pk})


# ============================================================================
# TEAM MEMBER MANAGEMENT VIEWS (Sprint 8 - US-010)
# ============================================================================


@login_required
def team_member_add(request, audit_pk):
    """
    Add a team member to an audit.

    Only lead auditor or CB admin can add team members.
    Displays competence warnings if applicable.
    """
    from audits.models import AuditorCompetenceWarning

    from .team_forms import AuditTeamMemberForm

    audit = get_object_or_404(Audit, pk=audit_pk)
    user = request.user

    # Permission check: must be lead auditor or CB admin
    is_cb_admin = user.groups.filter(name="cb_admin").exists()
    is_lead_auditor = audit.lead_auditor == user

    if not (is_cb_admin or is_lead_auditor):
        messages.error(request, "You don't have permission to add team members to this audit.")
        return redirect("audits:audit_detail", pk=audit_pk)

    competence_warnings = []

    if request.method == "POST":
        form = AuditTeamMemberForm(request.POST, audit=audit)
        if form.is_valid():
            team_member = form.save()

            # Check for competence warnings (only if user is selected)
            if team_member.user:
                # Check for warnings related to this team member
                warnings = AuditorCompetenceWarning.objects.filter(
                    audit=audit, auditor=team_member.user
                )
                if warnings.exists():
                    competence_warnings = list(warnings)
                    messages.warning(
                        request,
                        f"Team member added with {warnings.count()} competence warning(s). Review warnings in audit detail.",
                    )
                else:
                    messages.success(request, f"Team member {team_member.name} added successfully.")
            else:
                messages.success(request, f"External expert {team_member.name} added successfully.")

            return redirect("audits:audit_detail", pk=audit_pk)
    else:
        form = AuditTeamMemberForm(audit=audit)

    context = {
        "audit": audit,
        "form": form,
        "competence_warnings": competence_warnings,
        "page_title": "Add Team Member",
    }

    return render(request, "audits/team_member_form.html", context)


@login_required
def team_member_edit(request, pk):
    """
    Edit an existing audit team member.

    Only lead auditor or CB admin can edit team members.
    """
    from .team_forms import AuditTeamMemberForm

    team_member = get_object_or_404(AuditTeamMember, pk=pk)
    audit = team_member.audit
    user = request.user

    # Permission check: must be lead auditor or CB admin
    is_cb_admin = user.groups.filter(name="cb_admin").exists()
    is_lead_auditor = audit.lead_auditor == user

    if not (is_cb_admin or is_lead_auditor):
        messages.error(request, "You don't have permission to edit team members for this audit.")
        return redirect("audits:audit_detail", pk=audit.pk)

    if request.method == "POST":
        form = AuditTeamMemberForm(request.POST, instance=team_member, audit=audit)
        if form.is_valid():
            team_member = form.save()
            messages.success(request, f"Team member {team_member.name} updated successfully.")
            return redirect("audits:audit_detail", pk=audit.pk)
    else:
        form = AuditTeamMemberForm(instance=team_member, audit=audit)

    context = {
        "audit": audit,
        "form": form,
        "team_member": team_member,
        "page_title": "Edit Team Member",
    }

    return render(request, "audits/team_member_form.html", context)


@login_required
def team_member_delete(request, pk):
    """
    Delete an audit team member.

    Only lead auditor or CB admin can delete team members.
    """
    team_member = get_object_or_404(AuditTeamMember, pk=pk)
    audit = team_member.audit
    user = request.user

    # Permission check: must be lead auditor or CB admin
    is_cb_admin = user.groups.filter(name="cb_admin").exists()
    is_lead_auditor = audit.lead_auditor == user

    if not (is_cb_admin or is_lead_auditor):
        messages.error(request, "You don't have permission to delete team members from this audit.")
        return redirect("audits:audit_detail", pk=audit.pk)

    if request.method == "POST":
        member_name = team_member.name
        team_member.delete()
        messages.success(request, f"Team member {member_name} removed from audit.")
        return redirect("audits:audit_detail", pk=audit.pk)

    context = {
        "audit": audit,
        "team_member": team_member,
        "page_title": "Delete Team Member",
    }

    return render(request, "audits/team_member_confirm_delete.html", context)


# ============================================================================
# FINDINGS VIEWS (US-012, US-013, US-014)
# ============================================================================


@login_required
def nonconformity_add(request, audit_pk):
    """
    Add a nonconformity to an audit.

    Only auditors (lead_auditor, auditor, cb_admin) can create findings.
    """
    audit = get_object_or_404(Audit, pk=audit_pk)
    user = request.user

    # Permission check: must be auditor, lead auditor, or CB admin
    has_permission = user.groups.filter(name__in=["auditor", "lead_auditor", "cb_admin"]).exists()

    if not has_permission:
        messages.error(request, "You don't have permission to add findings to this audit.")
        return redirect("audits:audit_detail", pk=audit_pk)

    from audits.finding_forms import NonconformityForm

    if request.method == "POST":
        form = NonconformityForm(request.POST, audit=audit)
        if form.is_valid():
            nc = form.save(commit=False)
            nc.audit = audit
            nc.created_by = user
            nc.save()
            form.save_m2m()

            messages.success(
                request, f"{nc.get_category_display()} nonconformity added to clause {nc.clause}."
            )
            return redirect("audits:audit_detail", pk=audit_pk)
    else:
        form = NonconformityForm(audit=audit)

    context = {
        "audit": audit,
        "form": form,
        "finding_type": "Nonconformity",
        "page_title": "Add Nonconformity",
    }

    return render(request, "audits/finding_form.html", context)


@login_required
def observation_add(request, audit_pk):
    """
    Add an observation to an audit.

    Only auditors can create findings.
    """
    audit = get_object_or_404(Audit, pk=audit_pk)
    user = request.user

    # Permission check
    has_permission = user.groups.filter(name__in=["auditor", "lead_auditor", "cb_admin"]).exists()

    if not has_permission:
        messages.error(request, "You don't have permission to add findings to this audit.")
        return redirect("audits:audit_detail", pk=audit_pk)

    from audits.finding_forms import ObservationForm

    if request.method == "POST":
        form = ObservationForm(request.POST, audit=audit)
        if form.is_valid():
            obs = form.save(commit=False)
            obs.audit = audit
            obs.created_by = user
            obs.save()
            form.save_m2m()

            messages.success(request, f"Observation added to clause {obs.clause}.")
            return redirect("audits:audit_detail", pk=audit_pk)
    else:
        form = ObservationForm(audit=audit)

    context = {
        "audit": audit,
        "form": form,
        "finding_type": "Observation",
        "page_title": "Add Observation",
    }

    return render(request, "audits/finding_form.html", context)


@login_required
def ofi_add(request, audit_pk):
    """
    Add an opportunity for improvement to an audit.

    Only auditors can create findings.
    """
    audit = get_object_or_404(Audit, pk=audit_pk)
    user = request.user

    # Permission check
    has_permission = user.groups.filter(name__in=["auditor", "lead_auditor", "cb_admin"]).exists()

    if not has_permission:
        messages.error(request, "You don't have permission to add findings to this audit.")
        return redirect("audits:audit_detail", pk=audit_pk)

    from audits.finding_forms import OpportunityForImprovementForm

    if request.method == "POST":
        form = OpportunityForImprovementForm(request.POST, audit=audit)
        if form.is_valid():
            ofi = form.save(commit=False)
            ofi.audit = audit
            ofi.created_by = user
            ofi.save()
            form.save_m2m()

            messages.success(request, f"Opportunity for improvement added to clause {ofi.clause}.")
            return redirect("audits:audit_detail", pk=audit_pk)
    else:
        form = OpportunityForImprovementForm(audit=audit)

    context = {
        "audit": audit,
        "form": form,
        "finding_type": "Opportunity for Improvement",
        "page_title": "Add OFI",
    }

    return render(request, "audits/finding_form.html", context)


@login_required
def nonconformity_edit(request, pk):
    """
    Edit a nonconformity.

    Only the creator or CB admin can edit. Cannot edit if client has responded.
    """
    nc = get_object_or_404(Nonconformity, pk=pk)
    audit = nc.audit
    user = request.user

    # Permission check
    is_creator = nc.created_by == user
    is_cb_admin = user.groups.filter(name="cb_admin").exists()

    if not (is_creator or is_cb_admin):
        messages.error(request, "You don't have permission to edit this nonconformity.")
        return redirect("audits:audit_detail", pk=audit.pk)

    # Cannot edit if client has responded
    if nc.verification_status != "open":
        messages.error(
            request,
            "Cannot edit nonconformity - client has already responded or it has been verified.",
        )
        return redirect("audits:audit_detail", pk=audit.pk)

    from audits.finding_forms import NonconformityForm

    if request.method == "POST":
        form = NonconformityForm(request.POST, instance=nc, audit=audit)
        if form.is_valid():
            nc = form.save()
            messages.success(request, "Nonconformity updated successfully.")
            return redirect("audits:audit_detail", pk=audit.pk)
    else:
        form = NonconformityForm(instance=nc, audit=audit)

    context = {
        "audit": audit,
        "form": form,
        "finding": nc,
        "finding_type": "Nonconformity",
        "page_title": "Edit Nonconformity",
    }

    return render(request, "audits/finding_form.html", context)


@login_required
def observation_edit(request, pk):
    """Edit an observation."""
    obs = get_object_or_404(Observation, pk=pk)
    audit = obs.audit
    user = request.user

    # Permission check
    is_creator = obs.created_by == user
    is_cb_admin = user.groups.filter(name="cb_admin").exists()

    if not (is_creator or is_cb_admin):
        messages.error(request, "You don't have permission to edit this observation.")
        return redirect("audits:audit_detail", pk=audit.pk)

    from audits.finding_forms import ObservationForm

    if request.method == "POST":
        form = ObservationForm(request.POST, instance=obs, audit=audit)
        if form.is_valid():
            obs = form.save()
            messages.success(request, "Observation updated successfully.")
            return redirect("audits:audit_detail", pk=audit.pk)
    else:
        form = ObservationForm(instance=obs, audit=audit)

    context = {
        "audit": audit,
        "form": form,
        "finding": obs,
        "finding_type": "Observation",
        "page_title": "Edit Observation",
    }

    return render(request, "audits/finding_form.html", context)


@login_required
def ofi_edit(request, pk):
    """Edit an opportunity for improvement."""
    ofi = get_object_or_404(OpportunityForImprovement, pk=pk)
    audit = ofi.audit
    user = request.user

    # Permission check
    is_creator = ofi.created_by == user
    is_cb_admin = user.groups.filter(name="cb_admin").exists()

    if not (is_creator or is_cb_admin):
        messages.error(request, "You don't have permission to edit this OFI.")
        return redirect("audits:audit_detail", pk=audit.pk)

    from audits.finding_forms import OpportunityForImprovementForm

    if request.method == "POST":
        form = OpportunityForImprovementForm(request.POST, instance=ofi, audit=audit)
        if form.is_valid():
            ofi = form.save()
            messages.success(request, "Opportunity for improvement updated successfully.")
            return redirect("audits:audit_detail", pk=audit.pk)
    else:
        form = OpportunityForImprovementForm(instance=ofi, audit=audit)

    context = {
        "audit": audit,
        "form": form,
        "finding": ofi,
        "finding_type": "Opportunity for Improvement",
        "page_title": "Edit OFI",
    }

    return render(request, "audits/finding_form.html", context)


@login_required
def finding_delete(request, finding_type, pk):
    """
    Delete a finding (NC, Observation, or OFI).

    Only creator or CB admin can delete. Cannot delete NC if client has responded.
    """
    user = request.user

    # Get the appropriate finding model
    if finding_type == "nc":
        finding = get_object_or_404(Nonconformity, pk=pk)
        type_name = "Nonconformity"
    elif finding_type == "observation":
        finding = get_object_or_404(Observation, pk=pk)
        type_name = "Observation"
    elif finding_type == "ofi":
        finding = get_object_or_404(OpportunityForImprovement, pk=pk)
        type_name = "Opportunity for Improvement"
    else:
        messages.error(request, "Invalid finding type.")
        return redirect("audits:audit_list")

    audit = finding.audit

    # Permission check
    is_creator = finding.created_by == user
    is_cb_admin = user.groups.filter(name="cb_admin").exists()

    if not (is_creator or is_cb_admin):
        messages.error(request, f"You don't have permission to delete this {type_name.lower()}.")
        return redirect("audits:audit_detail", pk=audit.pk)

    # Cannot delete NC if client has responded
    if finding_type == "nc" and finding.verification_status != "open":
        messages.error(
            request,
            "Cannot delete nonconformity - client has already responded or it has been verified.",
        )
        return redirect("audits:audit_detail", pk=audit.pk)

    if request.method == "POST":
        finding.delete()
        messages.success(request, f"{type_name} deleted successfully.")
        return redirect("audits:audit_detail", pk=audit.pk)

    context = {
        "audit": audit,
        "finding": finding,
        "finding_type": type_name,
        "page_title": f"Delete {type_name}",
    }

    return render(request, "audits/finding_confirm_delete.html", context)


@login_required
def nonconformity_respond(request, pk):
    """
    Client response to a nonconformity.

    Only clients from the organization can respond.
    """
    nc = get_object_or_404(Nonconformity, pk=pk)
    audit = nc.audit
    user = request.user

    # Permission check: must be client from the organization
    is_client = user.groups.filter(name="client").exists()

    # Note: Organization membership check will be added when User-Organization
    # relationship model is implemented. For now, clients can respond to any NC.

    if not is_client:
        messages.error(request, "You don't have permission to respond to this nonconformity.")
        return redirect("audits:audit_detail", pk=audit.pk)

    # Can only respond if status is 'open'
    if nc.verification_status != "open":
        messages.error(request, "This nonconformity has already been responded to or verified.")
        return redirect("audits:audit_detail", pk=audit.pk)

    from audits.finding_forms import NonconformityResponseForm

    if request.method == "POST":
        form = NonconformityResponseForm(request.POST, instance=nc)
        if form.is_valid():
            nc = form.save(commit=False)
            nc.verification_status = "client_responded"
            nc.save()

            messages.success(
                request,
                "Response submitted successfully. The auditor will review your corrective action.",
            )
            return redirect("audits:audit_detail", pk=audit.pk)
    else:
        form = NonconformityResponseForm(instance=nc)

    context = {"audit": audit, "nc": nc, "form": form, "page_title": "Respond to Nonconformity"}

    return render(request, "audits/nc_response_form.html", context)


@login_required
def nonconformity_verify(request, pk):
    """
    Auditor verification of client response to nonconformity.

    Only auditors can verify.
    """
    nc = get_object_or_404(Nonconformity, pk=pk)
    audit = nc.audit
    user = request.user

    # Permission check: must be auditor
    has_permission = user.groups.filter(name__in=["auditor", "lead_auditor", "cb_admin"]).exists()

    if not has_permission:
        messages.error(request, "You don't have permission to verify nonconformities.")
        return redirect("audits:audit_detail", pk=audit.pk)

    # Can only verify if client has responded
    if nc.verification_status != "client_responded":
        messages.error(
            request,
            "Cannot verify - client has not responded or this NC has already been verified.",
        )
        return redirect("audits:audit_detail", pk=audit.pk)

    from django.utils import timezone

    from audits.finding_forms import NonconformityVerificationForm

    if request.method == "POST":
        form = NonconformityVerificationForm(request.POST, instance=nc)
        if form.is_valid():
            nc = form.save(commit=False)
            nc.verified_by = user
            nc.verified_at = timezone.now()
            nc.save()

            messages.success(
                request,
                f"Nonconformity verification completed - status: {nc.get_verification_status_display()}.",
            )
            return redirect("audits:audit_detail", pk=audit.pk)
    else:
        form = NonconformityVerificationForm(instance=nc)

    context = {
        "audit": audit,
        "nc": nc,
        "form": form,
        "page_title": "Verify Nonconformity Response",
    }

    return render(request, "audits/nc_verification_form.html", context)
