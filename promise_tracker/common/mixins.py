from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from rolepermissions.checkers import has_role
from rolepermissions.roles import AbstractUserRole


class VerificationRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_verified:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class VerifiedLoginRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_verified:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class RoleBasedAccessMixin(AccessMixin):
    required_roles: AbstractUserRole = []
    allow_guests: bool = False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if self.allow_guests:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()

        if not has_role(request.user, self.required_roles):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)
