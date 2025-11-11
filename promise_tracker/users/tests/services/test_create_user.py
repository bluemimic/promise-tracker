from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from faker import Faker
from loguru import logger

from promise_tracker.core.exceptions import ApplicationError, PermissionViolationError
from promise_tracker.users.services import UserService
from promise_tracker.users.tests.factories import AdministratorUserFactory, UniversalUserFactory

logger.remove()


class CreateUserTests(TestCase):
    def test_should_not_create_when_registred_user_creating_admim(self):
        registered_user = UniversalUserFactory()
        user_service = UserService(performed_by=registered_user)

        with self.assertRaises(PermissionViolationError):
            user_service.create_user(
                name=Faker().first_name(),
                surname=Faker().last_name(),
                email=Faker().email(),
                username=Faker().user_name(),
                password="SomePassword123!",
                another_password="SomePassword123!",
                is_admin=True,
            )

    @patch("promise_tracker.users.services.email_send_task.delay")
    def test_should_create_when_admin_creating_admim(self, mock_email_send):
        admin_user = AdministratorUserFactory()
        user_service = UserService(performed_by=admin_user)

        user = user_service.create_user(
            name=Faker().first_name(),
            surname=Faker().last_name(),
            email=Faker().email(),
            username=Faker().user_name(),
            password="SomePassword123!",
            another_password="SomePassword123!",
            is_admin=True,
        )

        self.assertIsNotNone(user)
        self.assertTrue(user.is_admin)

        mock_email_send.assert_called_once_with(user.email, user.verification_code)

    def test_should_not_create_when_passwords_do_not_match(self):
        admin_user = AdministratorUserFactory()
        user_service = UserService(performed_by=admin_user)

        with self.assertRaises(ApplicationError):
            user_service.create_user(
                name=Faker().first_name(),
                surname=Faker().last_name(),
                email=Faker().email(),
                username=Faker().user_name(),
                password="SomePassword123!",
                another_password="DifferentPassword123!",
                is_admin=True,
            )

    @patch("promise_tracker.users.services.email_send_task")
    @patch("promise_tracker.users.models.BaseUser.set_verification_code")
    def test_should_create_user_successfully(self, mock_set_verification_code, mock_email_send):
        admin_user = AdministratorUserFactory()
        user_service = UserService(performed_by=admin_user)

        email = Faker().email()

        user = user_service.create_user(
            name=Faker().first_name(),
            surname=Faker().last_name(),
            email=email,
            username=Faker().user_name(),
            password="SomePassword123!",
            another_password="SomePassword123!",
            is_admin=False,
        )

        self.assertIsNotNone(user)

        mock_set_verification_code.assert_called_once_with(
            user, user.verification_code, user.verification_code_expires_at
        )
        mock_email_send.delay.assert_called_once_with(email, user.verification_code)

        self.assertIsNotNone(user.verification_code)
        self.assertIsNotNone(user.verification_code_expires_at)
        self.assertGreater(user.verification_code_expires_at, timezone.now())
        self.assertIsNotNone(user.verification_email_sent_at)
        self.assertFalse(user.is_verified)
