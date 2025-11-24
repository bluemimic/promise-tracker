from datetime import timedelta

from django.utils.translation import gettext as _
from django.utils.translation import ngettext as plural


class DomainError(Exception):
    def __init__(self, message: str, extra=None):
        super().__init__(message)

        self.message = message
        self.extra = extra or {}


class ApplicationError(DomainError):
    def __init__(self, message: str, extra=None):
        super().__init__(message, extra)


class PermissionViolationError(ApplicationError):
    def __init__(self, extra=None):
        super().__init__(_("You do not have permission to perform this action."), extra)


class NotFoundError(DomainError):
    def __init__(self, message: str, extra=None):
        super().__init__(message, extra)


class EmailDelayError(ApplicationError):
    def __init__(self, wait_time: timedelta, extra=None):
        minutes = round(wait_time.seconds / 60)

        if minutes == 0:
            message = _("Please wait a few seconds before requesting another verification email.")
        else:
            message = plural(
                "Please wait %(minutes)d minute before requesting another verification email.",
                "Please wait %(minutes)d minutes before requesting another verification email.",
                minutes,
            ) % {"minutes": minutes}
        super().__init__(message, extra)


class AuthenticationError(ApplicationError):
    def __init__(self, message: str = _("Authentication failed."), extra=None):
        super().__init__(message, extra)
