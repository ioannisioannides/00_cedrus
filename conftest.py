import pytest


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
