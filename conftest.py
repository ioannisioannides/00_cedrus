import os

import pytest

# Allow synchronous Django DB operations in async contexts (like Playwright tests)
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@pytest.fixture(autouse=True)
def enable_celery_always_eager(settings):
    """
    Force Celery to run in eager mode during tests.
    This avoids the need for a running Redis broker.
    """
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    settings.CELERY_BROKER_URL = "memory://"
    settings.CELERY_RESULT_BACKEND = "cache+memory://"


@pytest.fixture(autouse=True)
def disable_axes_in_tests(settings):
    """
    Use plain ModelBackend in tests so Client.login() works without a request object.
    Axes lockout behaviour is tested by the django-axes package itself.
    """
    settings.AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
