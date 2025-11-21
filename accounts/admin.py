"""
Django admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    """Inline admin for Profile model."""

    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


class UserAdmin(BaseUserAdmin):
    """Extended User admin with Profile inline."""

    inlines = (ProfileInline,)

    def get_inline_instances(self, request, obj=None):
        """Only show inline if editing existing user."""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
