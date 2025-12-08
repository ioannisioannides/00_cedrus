import importlib
import sys
from unittest.mock import MagicMock

from django.test import SimpleTestCase, override_settings
from django.urls import resolve, reverse


class TestUrls(SimpleTestCase):
    def test_admin_url(self):
        url = reverse("admin:index")
        assert resolve(url).view_name == "admin:index"

    def test_home_redirect(self):
        url = reverse("home")
        assert resolve(url).view_name == "home"

    def test_health_check_urls(self):
        assert reverse("health") == "/health/"
        assert reverse("readiness") == "/health/ready/"
        assert reverse("liveness") == "/health/live/"

    def test_api_docs_urls(self):
        assert reverse("schema") == "/api/schema/"
        assert reverse("swagger-ui") == "/api/docs/"
        assert reverse("redoc") == "/api/redoc/"

    @override_settings(DEBUG=True)
    def test_debug_toolbar_urls(self):
        # We need to reload the module to pick up the changes based on DEBUG setting
        if "cedrus.urls" in sys.modules:
            import cedrus.urls

            importlib.reload(cedrus.urls)

        from cedrus.urls import urlpatterns

        # Check if debug toolbar is in urlpatterns
        # This depends on whether debug_toolbar is installed in the environment
        try:
            import debug_toolbar  # noqa: F401

            has_debug_toolbar = True
        except ImportError:
            has_debug_toolbar = False

        if has_debug_toolbar:
            debug_urls = [p for p in urlpatterns if hasattr(p, "pattern") and str(p.pattern) == "__debug__/"]
            assert len(debug_urls) > 0

    @override_settings(DEBUG=True)
    def test_debug_toolbar_urls_mocked(self):
        """Test that debug toolbar URLs are added when the module is present."""
        # Mock debug_toolbar module
        mock_toolbar = MagicMock()
        mock_toolbar.urls = []

        # Save original modules
        original_modules = sys.modules.copy()

        try:
            sys.modules["debug_toolbar"] = mock_toolbar

            # Force reload of cedrus.urls
            if "cedrus.urls" in sys.modules:
                import cedrus.urls

                importlib.reload(cedrus.urls)
            else:
                import cedrus.urls

            from cedrus.urls import urlpatterns

            # Verify __debug__ is in urlpatterns
            debug_urls = [p for p in urlpatterns if hasattr(p, "pattern") and str(p.pattern) == "__debug__/"]
            assert len(debug_urls) > 0

        finally:
            # Restore original modules
            sys.modules = original_modules
            # Reload cedrus.urls to restore original state
            if "cedrus.urls" in sys.modules:
                import cedrus.urls

                importlib.reload(cedrus.urls)

    @override_settings(DEBUG=False)
    def test_production_urls(self):
        # Reload to reset to production mode
        if "cedrus.urls" in sys.modules:
            import cedrus.urls

            importlib.reload(cedrus.urls)

        from cedrus.urls import urlpatterns

        # Check that debug toolbar is NOT in urlpatterns
        debug_urls = [p for p in urlpatterns if hasattr(p, "pattern") and str(p.pattern) == "__debug__/"]
        assert len(debug_urls) == 0
