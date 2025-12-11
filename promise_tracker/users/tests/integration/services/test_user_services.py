from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone
from faker import Faker

from promise_tracker.users.enums import ModerationAction
from promise_tracker.users.models import BaseUser
from promise_tracker.users.services import UserService
from promise_tracker.users.tests.factories import AdminUserFactory, UnverifiedUserFactory

faker = Faker()


class UserServicesIntegrationTests(TestCase):
    def setUp(self):
        self.mock_base_service = MagicMock()

        self.mocked_service = UserService(
            performed_by=MagicMock(spec=BaseUser),
            base_service=self.mock_base_service,
        )

        self.service = UserService(
            performed_by=AdminUserFactory.create(),
        )

    @patch("promise_tracker.users.services.email_send_task.delay")
    def test_create_calls_email_send_task(self, mock_email_send_task):
        new_user = UnverifiedUserFactory.build()

        self.mocked_service.create_user(
            name=new_user.name,
            surname=new_user.surname,
            email=new_user.email,
            username=new_user.username,
            password=new_user.password,
            another_password=new_user.password,
            is_admin=new_user.is_admin,
        )

        mock_email_send_task.assert_called_once()

    def test_create_calls_base_service_create(self):
        new_user = UnverifiedUserFactory.build()

        self.mocked_service.create_user(
            name=new_user.name,
            surname=new_user.surname,
            email=new_user.email,
            username=new_user.username,
            password=new_user.password,
            another_password=new_user.password,
            is_admin=new_user.is_admin,
        )

        self.mock_base_service.create_base.assert_called_once()

    @patch("promise_tracker.users.services.email_send_task.delay")
    def test_update_calls_email_send_task_on_email_change(self, mock_email_send_task):
        user = UnverifiedUserFactory.create()
        new_email = faker.unique.email()

        self.service.edit_user(
            id=user.id,
            name=user.name,
            surname=user.surname,
            email=new_email,
            username=user.username,
            is_admin=user.is_admin,
        )

        mock_email_send_task.assert_called_once()

    def test_update_calls_base_service_update(self):
        user = UnverifiedUserFactory.create()
        new_email = faker.unique.email()

        self.mocked_service.edit_user(
            id=user.id,
            name=user.name,
            surname=user.surname,
            email=new_email,
            username=user.username,
            is_admin=user.is_admin,
        )

        self.mock_base_service.edit_base.assert_called_once()

    @patch("promise_tracker.users.services.email_send_task.delay")
    def test_send_verification_email_sends_email(self, mock_email_send_task):
        user = UnverifiedUserFactory.create()

        self.service.send_verification_email(id=user.id)

        mock_email_send_task.assert_called_once()

    def test_send_verification_email_calls_base_service(self):
        user = UnverifiedUserFactory.create()

        self.mocked_service.send_verification_email(id=user.id)

        self.mock_base_service.edit_base.assert_called_once()

    def test_verify_email_calls_base_service(self):
        user = UnverifiedUserFactory.create(
            verification_code="123456",
            verification_code_expires_at=timezone.make_aware(faker.future_datetime()),
        )
        verification_code = "123456"

        self.mocked_service.verify_user_email(id=user.id, verification_code=verification_code)

        self.mock_base_service.edit_base.assert_called_once()

    def test_moderate_user_calls_base_service(self):
        user = UnverifiedUserFactory.create()

        self.mocked_service.moderate_user(id=user.id, action=ModerationAction.BAN)

        self.mock_base_service.edit_base.assert_called_once()
