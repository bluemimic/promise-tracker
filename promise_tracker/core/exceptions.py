from django.utils.translation import gettext as _
from datetime import datetime


class ApplicationError(Exception):
    def __init__(self, message: str, extra=None):
        super().__init__(message)

        self.message = message
        self.extra = extra or {}


class PermissionViolationError(ApplicationError):
    def __init__(self, extra=None):
        super().__init__(_("You do not have permission to perform this action."), extra)


class NotFoundError(ApplicationError):
    def __init__(self, message: str, extra=None):
        super().__init__(message, extra)


class EmailDelayError(ApplicationError):
    def __init__(self, wait_time: datetime, extra=None):
        message = _("Please wait {wait} minutes before requesting another email.").format(wait=wait_time.minute)
        super().__init__(message, extra)


class AuthenticationError(ApplicationError):
    def __init__(self, message: str = _("Authentication failed."), extra=None):
        super().__init__(message, extra)
