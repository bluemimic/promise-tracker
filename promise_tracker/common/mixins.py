from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from rolepermissions.checkers import has_role
from rolepermissions.roles import AbstractUserRole

from promise_tracker.core.exceptions import ApplicationError, DomainError, NotFoundError, PermissionViolationError


class VerifiedLoginRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_verified:
            return redirect("users:verify")
        return super().dispatch(request, *args, **kwargs)


class RoleBasedAccessMixin(AccessMixin):
    required_roles: list[type[AbstractUserRole]] = []
    allow_guests: bool = False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if self.allow_guests:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()

        if not any(has_role(request.user, role) for role in self.required_roles):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class HandleErrorsMixin:
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)

        except PermissionViolationError as e:
            messages.error(request, e.message)
            return self.handle_no_permission()

        except NotFoundError as e:
            messages.error(request, e.message)
            raise Http404(e.message)

        except ApplicationError as e:
            messages.error(request, e.message)
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        except DomainError as e:
            messages.error(request, e.message)
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
