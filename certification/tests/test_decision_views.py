from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from audit_management.models import Audit
from core.models import Certification, Organization, Standard

User = get_user_model()


class TechnicalReviewViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="reviewer", password="password")
        self.client.login(username="reviewer", password="password")

        # Create minimal valid Organization and Audit
        self.org = Organization.objects.create(name="Test Org", total_employee_count=50)
        self.audit = Audit.objects.create(
            organization=self.org,
            status="technical_review",
            total_audit_date_from=timezone.now().date(),
            total_audit_date_to=timezone.now().date(),
            created_by=self.user,
            lead_auditor=self.user,
        )

    @patch("certification.api.views.decision.PermissionPredicate")
    def test_technical_review_create_get(self, MockPermissionPredicate):
        """Test GET request for technical review creation."""
        MockPermissionPredicate.can_conduct_technical_review.return_value = True

        url = reverse("certification:technical_review_create", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "audits/technical_review_form.html")
        self.assertEqual(response.context["audit"], self.audit)

    @patch("certification.api.views.decision.PermissionPredicate")
    def test_technical_review_create_permission_denied(self, MockPermissionPredicate):
        """Test permission denied for technical review creation."""
        MockPermissionPredicate.can_conduct_technical_review.return_value = False

        url = reverse("certification:technical_review_create", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    @patch("certification.api.views.decision.PermissionPredicate")
    def test_technical_review_create_wrong_status(self, MockPermissionPredicate):
        """Test technical review creation fails if audit is not in technical_review status."""
        MockPermissionPredicate.can_conduct_technical_review.return_value = True
        self.audit.status = "draft"
        self.audit.save()

        url = reverse("certification:technical_review_create", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    @patch("certification.api.views.decision.PermissionPredicate")
    @patch("certification.api.views.decision.ReviewService")
    def test_technical_review_create_post_success(self, MockReviewService, MockPermissionPredicate):
        """Test successful POST request for technical review creation."""
        MockPermissionPredicate.can_conduct_technical_review.return_value = True

        mock_review = MagicMock()
        mock_review.status = "approved"
        mock_review.audit = self.audit
        MockReviewService.conduct_technical_review.return_value = mock_review

        url = reverse("certification:technical_review_create", kwargs={"audit_pk": self.audit.pk})
        data = {
            "scope_verified": True,
            "objectives_verified": True,
            "findings_reviewed": True,
            "conclusion_clear": True,
            "reviewer_notes": "Looks good",
            "clarification_requested": False,
            "status": "approved",
        }
        response = self.client.post(url, data)

        self.assertRedirects(
            response,
            reverse("audit_management:audit_detail", kwargs={"pk": self.audit.pk}),
            fetch_redirect_response=False,
        )
        MockReviewService.conduct_technical_review.assert_called_once()


class CertificationDecisionViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="decision_maker", password="password")
        self.client.login(username="decision_maker", password="password")

        # Create minimal valid Organization and Audit
        self.org = Organization.objects.create(name="Test Org", total_employee_count=50)
        self.standard = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")
        self.certification = Certification.objects.create(
            organization=self.org, standard=self.standard, certificate_status="active"
        )
        self.audit = Audit.objects.create(
            organization=self.org,
            status="decision_pending",
            total_audit_date_from=timezone.now().date(),
            total_audit_date_to=timezone.now().date(),
            created_by=self.user,
            lead_auditor=self.user,
        )
        self.audit.certifications.add(self.certification)

    @patch("certification.api.views.decision.PermissionPredicate")
    def test_certification_decision_create_get(self, MockPermissionPredicate):
        """Test GET request for certification decision creation."""
        MockPermissionPredicate.can_make_certification_decision.return_value = True

        url = reverse("certification:certification_decision_create", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "audits/certification_decision_form.html")
        self.assertEqual(response.context["audit"], self.audit)

    @patch("certification.api.views.decision.PermissionPredicate")
    def test_certification_decision_create_permission_denied(self, MockPermissionPredicate):
        """Test permission denied for certification decision creation."""
        MockPermissionPredicate.can_make_certification_decision.return_value = False

        url = reverse("certification:certification_decision_create", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    @patch("certification.api.views.decision.PermissionPredicate")
    def test_certification_decision_create_wrong_status(self, MockPermissionPredicate):
        """Test certification decision creation fails if audit is not in decision_pending status."""
        MockPermissionPredicate.can_make_certification_decision.return_value = True
        self.audit.status = "technical_review"
        self.audit.save()

        url = reverse("certification:certification_decision_create", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    @patch("certification.api.views.decision.PermissionPredicate")
    @patch("certification.api.views.decision.ReviewService")
    def test_certification_decision_create_post_success(self, MockReviewService, MockPermissionPredicate):
        """Test successful POST request for certification decision creation."""
        MockPermissionPredicate.can_make_certification_decision.return_value = True

        mock_decision = MagicMock()
        mock_decision.get_decision_display.return_value = "Granted"
        mock_decision.audit = self.audit
        MockReviewService.make_certification_decision.return_value = mock_decision

        url = reverse("certification:certification_decision_create", kwargs={"audit_pk": self.audit.pk})
        data = {
            "decision": "grant",
            "decision_notes": "Approved",
            "certifications_affected": [self.certification.pk],
        }
        response = self.client.post(url, data)

        self.assertRedirects(
            response,
            reverse("audit_management:audit_detail", kwargs={"pk": self.audit.pk}),
            fetch_redirect_response=False,
        )
        MockReviewService.make_certification_decision.assert_called_once()
