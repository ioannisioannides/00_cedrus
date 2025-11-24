from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Django app configuration for the core application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        """Register event handlers on app startup."""
        from trunk.events.handlers import register_event_handlers

        register_event_handlers()
