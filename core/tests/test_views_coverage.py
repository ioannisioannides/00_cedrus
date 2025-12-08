from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from core.views import CertificateHistoryCreateView

User = get_user_model()


class TestViewsCoverage(TestCase):
    def test_certificate_history_create_view_no_certification_pk(self):
        """Test get_initial when certification_pk is not in kwargs."""
        view = CertificateHistoryCreateView()
        view.kwargs = {}
        view.request = RequestFactory().get("/")

        initial = view.get_initial()

        assert "certification" not in initial
