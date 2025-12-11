from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from loguru import logger

from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.core.exceptions import ApplicationError, AuthenticationError
from promise_tracker.users.models import BaseUser
from promise_tracker.users.services import UserService


class AuthService:
    def __init__(self, request: HttpRequest):
        self.request = request

    USER_IS_DELETED = _("User has been deleted.")
    USER_IS_INACTIVE = _("User account is inactive.")
    INCORRECT_CREDENTIALS = _("Incorrect email or password.")
    USER_NOT_FOUND = _("User not found.")

    def _verify_user_not_deleted(self, user: BaseUser):
        if user.is_deleted:
            logger.warning(f"Deleted user {user.id} attempted to log in.")
            raise ApplicationError(self.USER_IS_DELETED)

    def _verify_user_is_active(self, user: BaseUser):
        if not user.is_active:
            logger.warning(f"Inactive user {user.id} attempted to log in.")
            raise AuthenticationError(self.USER_IS_INACTIVE)

    def _should_send_verification_email(self, user: BaseUser) -> bool:
        return not user.is_verified and (
            user.verification_code_expires_at is None or user.verification_code_expires_at < timezone.now()
        )

    def login(self, email: str, password: str) -> bool:
        logger.debug(f"Attempting login for email: {email}")

        abstract_user = authenticate(username=email, password=password)

        if not abstract_user:
            logger.warning(f"Failed login attempt for email: {email}")
            raise AuthenticationError(self.INCORRECT_CREDENTIALS)

        user = get_object_or_raise(BaseUser, self.USER_NOT_FOUND, pk=abstract_user.pk)

        self._verify_user_not_deleted(user)
        self._verify_user_is_active(user)

        login(self.request, user)

        if self._should_send_verification_email(user):
            user_service = UserService(performed_by=user)
            user_service.send_verification_email(user.id)

        return True

    def logout(self) -> None:
        logger.debug(f"Logging out user ID: {self.request.user.pk}")
        logout(self.request)
