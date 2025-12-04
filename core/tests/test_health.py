from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory

from core.health import detailed_status, health_check, liveness_check, readiness_check


class TestHealthChecks:
    def setup_method(self):
        self.factory = RequestFactory()

    def test_health_check(self):
        request = self.factory.get("/health/")
        response = health_check(request)

        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert '"status": "healthy"' in data
        assert '"version": "0.1.0"' in data

    @patch("core.health.connection")
    @patch("core.health.cache")
    @patch("core.health.get_user_model")
    def test_readiness_check_success(self, mock_get_user_model, mock_cache, mock_connection):
        # Mock DB
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        mock_connection.cursor.return_value = mock_cursor

        # Mock Cache
        mock_cache.get.return_value = "test_value"

        # Mock Models
        mock_get_user_model.return_value._meta.model_name = "user"

        request = self.factory.get("/health/ready/")
        response = readiness_check(request)

        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert '"status": "ready"' in data
        assert '"database": "healthy"' in data
        assert '"cache": "healthy"' in data
        assert '"models": "healthy"' in data

    @patch("core.health.connection")
    @patch("core.health.cache")
    @patch("core.health.get_user_model")
    def test_readiness_check_failure(self, mock_get_user_model, mock_cache, mock_connection):
        # Mock DB Failure
        mock_connection.cursor.side_effect = Exception("DB Error")

        # Mock Cache Failure
        mock_cache.set.side_effect = Exception("Cache Error")

        # Mock Models Failure
        mock_get_user_model.side_effect = Exception("Model Error")

        request = self.factory.get("/health/ready/")
        response = readiness_check(request)

        assert response.status_code == 503
        data = response.content.decode("utf-8")
        assert '"status": "not_ready"' in data
        assert '"database": "unhealthy"' in data
        assert '"cache": "unhealthy"' in data
        assert '"models": "unhealthy"' in data
        assert "DB Error" in data

    def test_liveness_check(self):
        request = self.factory.get("/health/live/")
        response = liveness_check(request)

        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert '"status": "alive"' in data
        assert '"python_version":' in data

    @patch("core.health.settings")
    def test_detailed_status_forbidden(self, mock_settings):
        mock_settings.DEBUG = False
        request = self.factory.get("/health/status/")
        request.user = AnonymousUser()

        response = detailed_status(request)

        assert response.status_code == 403
        assert '"error": "Forbidden' in response.content.decode("utf-8")

    @patch("core.health.settings")
    @patch("core.health.connection")
    @patch("core.health.cache")
    def test_detailed_status_success_superuser(self, mock_cache, mock_connection, mock_settings):
        mock_settings.DEBUG = False
        mock_settings.DJANGO_VERSION = "4.2"
        mock_settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

        request = self.factory.get("/health/status/")
        request.user = Mock(spec=User)
        request.user.is_authenticated = True
        request.user.is_superuser = True

        # Mock DB
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ("PostgreSQL 14.5",)
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.settings_dict = {"ENGINE": "django.db.backends.postgresql", "NAME": "cedrus_db"}

        # Mock Cache
        mock_cache.get.return_value = "test"

        response = detailed_status(request)

        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert '"status": "healthy"' in data
        assert '"database":' in data
        assert '"cache":' in data
        assert '"system":' in data

    @patch("core.health.settings")
    def test_detailed_status_success_debug(self, mock_settings):
        mock_settings.DEBUG = True
        mock_settings.DJANGO_VERSION = "4.2"
        mock_settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

        request = self.factory.get("/health/status/")
        request.user = AnonymousUser()

        # We need to mock connection and cache here too or they will fail/use real ones
        with patch("core.health.connection") as mock_conn, patch("core.health.cache") as mock_cache:
            mock_cursor = MagicMock()
            mock_cursor.__enter__.return_value = mock_cursor
            mock_cursor.fetchone.return_value = ("PostgreSQL 14.5",)
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.settings_dict = {"ENGINE": "django.db.backends.postgresql", "NAME": "cedrus_db"}

            mock_cache.get.return_value = "test"

            response = detailed_status(request)

        assert response.status_code == 200

    @patch("core.health.timezone")
    def test_liveness_check_failure(self, mock_timezone):
        # First call raises exception (triggering except block), second call succeeds (in except block)
        mock_timezone.now.side_effect = [Exception("Error"), Mock(isoformat=lambda: "2025-01-01")]

        request = self.factory.get("/health/live/")
        response = liveness_check(request)

        assert response.status_code == 503
        assert '"status": "dead"' in response.content.decode("utf-8")

    @patch("core.health.settings")
    @patch("core.health.connection")
    @patch("core.health.cache")
    def test_detailed_status_partial_failure(self, mock_cache, mock_connection, mock_settings):
        mock_settings.DEBUG = True
        mock_settings.DJANGO_VERSION = "4.2"

        request = self.factory.get("/health/status/")
        request.user = AnonymousUser()

        # Mock DB Failure
        mock_connection.cursor.side_effect = Exception("DB Error")

        # Mock Cache Failure
        mock_cache.set.side_effect = Exception("Cache Error")

        response = detailed_status(request)

        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert '"status": "healthy"' in data
        assert '"database":' in data
        assert '"status": "error"' in data
        assert '"cache":' in data
        assert '"error": "Cache Error"' in data

    @patch("core.health.connection")
    @patch("core.health.cache")
    @patch("core.health.get_user_model")
    def test_readiness_check_unexpected_results(self, mock_get_user_model, mock_cache, mock_connection):
        # Mock DB Unexpected Result
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (0,)  # Not 1
        mock_connection.cursor.return_value = mock_cursor

        # Mock Cache Unexpected Result
        mock_cache.get.return_value = "wrong_value"

        # Mock Models Success
        mock_get_user_model.return_value._meta.model_name = "user"

        request = self.factory.get("/health/ready/")
        response = readiness_check(request)

        assert response.status_code == 503
        data = response.content.decode("utf-8")
        assert '"status": "not_ready"' in data
        assert '"database": "unhealthy"' in data
        assert '"cache": "unhealthy"' in data
        assert "Database query returned unexpected result" in data
        assert "Cache read/write test failed" in data
