from unittest.mock import MagicMock

from django.test import RequestFactory, TestCase
from faker import Faker

from promise_tracker.authentication.services import AuthService
from promise_tracker.core.exceptions import ApplicationError, AuthenticationError
from promise_tracker.users.tests.factories import VerifiedUserFactory

faker = Faker()


class FakeSession(dict):
    def flush(self):
        self.clear()


class AuthenticationServicesUnitTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        self.request.session = MagicMock()
        self.request.user = None

        self.service = AuthService(
            request=self.request,
        )

        self.regular_user_service = AuthService(
            request=self.request,
        )

    def test_login_raises_error_when_user_not_found(self):
        with self.assertRaisesMessage(
            AuthenticationError,
            str(self.service.INCORRECT_CREDENTIALS),
        ):
            self.service.login(
                email=faker.unique.email(),
                password="some2233SSPassword!",
            )

    def test_login_raises_error_when_user_is_deleted(self):
        deleted_user = VerifiedUserFactory.create(is_deleted=True)

        with self.assertRaisesMessage(
            ApplicationError,
            str(self.service.USER_IS_DELETED),
        ):
            self.service.login(
                email=deleted_user.email,
                password="some2233SSPassword!",
            )

    def test_login_raises_error_when_user_is_inactive(self):
        inactive_user = VerifiedUserFactory.create(is_active=False)

        with self.assertRaisesMessage(
            AuthenticationError,
            str(self.service.INCORRECT_CREDENTIALS),
        ):
            self.service.login(
                email=inactive_user.email,
                password="some2233SSPassword!",
            )

    def test_login_raises_error_when_credentials_incorrect(self):
        user = VerifiedUserFactory.create()

        with self.assertRaisesMessage(
            AuthenticationError,
            str(self.service.INCORRECT_CREDENTIALS),
        ):
            self.service.login(
                email=user.email,
                password="WrongPassword123!",
            )

    def test_login_successful(self):
        user = VerifiedUserFactory.create()

        result = self.service.login(
            email=user.email,
            password="some2233SSPassword!",
        )

        self.assertTrue(result)
        self.assertIsNotNone(self.request.user)
        self.assertTrue(self.request.user.is_authenticated)

    def test_logout_logs_out_user(self):
        user = VerifiedUserFactory.create()

        self.request.user = user

        self.service.logout()

        self.assertFalse(hasattr(self.request, "user") and self.request.user.is_authenticated)
