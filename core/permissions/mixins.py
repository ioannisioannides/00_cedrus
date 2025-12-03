from django.contrib.auth.mixins import UserPassesTestMixin

from .predicates import PermissionPredicate


class CBAdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin that restricts view access to users with CB Admin role.

    Usage:
        class MyView(CBAdminRequiredMixin, View):
            # Only CB Admins can access this view
            pass
    """

    def test_func(self):
        """Check if the current user is a CB Admin."""
        return PermissionPredicate.is_cb_admin(self.request.user)


class AuditorRequiredMixin(UserPassesTestMixin):
    """
    Mixin that restricts view access to users with Auditor or Lead Auditor role.

    Usage:
        class MyView(AuditorRequiredMixin, View):
            # Only Auditors/Lead Auditors can access this view
            pass
    """

    def test_func(self):
        """Check if the current user is an Auditor or Lead Auditor."""
        return PermissionPredicate.is_auditor(self.request.user)


class ClientRequiredMixin(UserPassesTestMixin):
    """
    Mixin that restricts view access to users with Client role (Client Admin or Client User).

    Usage:
        class MyView(ClientRequiredMixin, View):
            # Only Client users can access this view
            pass
    """

    def test_func(self):
        """Check if the current user is a Client Admin or Client User."""
        return PermissionPredicate.is_client_user(self.request.user)
