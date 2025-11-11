from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext as _
from loguru import logger

from promise_tracker.core.exceptions import ApplicationError, AuthenticationError
from promise_tracker.users.models import BaseUser
from promise_tracker.users.services import UserService


class AuthService:
    def __init__(self, user_service: UserService, request: HttpRequest):
        self.request = request
        self.user_service = user_service

    def _verify_user_not_deleted(self, user: BaseUser):
        if user.is_deleted:
            logger.warning(f"Deleted user {user.id} attempted to log in.")
            raise ApplicationError(_("User has been deleted."))

    def _verify_user_is_active(self, user: BaseUser):
        if not user.is_active:
            logger.warning(f"Inactive user {user.id} attempted to log in.")
            raise AuthenticationError(_("User account is inactive."))

    def login(self, email: str, password: str) -> bool:
        logger.debug(f"Attempting login for email: {email}")

        abstract_user = authenticate(username=email, password=password)

        if not abstract_user:
            logger.warning(f"Failed login attempt for email: {email}")
            raise AuthenticationError(_("Incorrect email or password."))

        user = self.user_service.get_user_by_id(abstract_user.pk)

        self._verify_user_not_deleted(user)
        self._verify_user_is_active(user)

        login(self.request, user)

        if not user.is_verified and user.verification_code_expires_at < timezone.now():
            self.user_service.send_verification_email(user.id)

        return True

    def logout(self) -> None:
        logger.debug(f"Logging out user ID: {self.request.user.pk}")
        logout(self.request)
