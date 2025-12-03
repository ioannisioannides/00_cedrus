from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, UpdateView

from audit_management.models import Audit
from certification.domain.services.review_service import ReviewService
from certification.models import CertificationDecision, TechnicalReview
from core.permissions.predicates import PermissionPredicate


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

        try:
            self.object = ReviewService.conduct_technical_review(
                audit=audit, reviewer=self.request.user, data=form.cleaned_data
            )

            if self.object.status == "approved":
                messages.success(self.request, "Technical review completed. Audit moved to decision pending.")
            else:
                messages.success(self.request, "Technical review saved. Audit remains in technical review status.")

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        # TODO: Update URL name to point to audit detail in new app
        return reverse("audit_management:audit_detail", kwargs={"pk": self.kwargs["audit_pk"]})


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
        try:
            self.object = ReviewService.conduct_technical_review(
                audit=self.object.audit, reviewer=self.request.user, data=form.cleaned_data
            )

            if self.object.status == "approved":
                messages.success(self.request, "Technical review approved. Audit moved to decision pending.")
            else:
                messages.success(self.request, "Technical review updated.")

        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audit_management:audit_detail", kwargs={"pk": self.object.audit.pk})


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

        try:
            self.object = ReviewService.make_certification_decision(
                audit=audit, decision_maker=self.request.user, data=form.cleaned_data
            )
            messages.success(
                self.request,
                f"Certification decision made: {self.object.get_decision_display()}. Audit closed.",
            )
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audit_management:audit_detail", kwargs={"pk": self.kwargs["audit_pk"]})


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
        self.object = ReviewService.update_certification_decision(
            decision=self.object, decision_maker=self.request.user, data=form.cleaned_data
        )
        messages.success(self.request, "Certification decision updated.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to appropriate page after successful form submission."""
        return reverse("audit_management:audit_detail", kwargs={"pk": self.object.audit.pk})
