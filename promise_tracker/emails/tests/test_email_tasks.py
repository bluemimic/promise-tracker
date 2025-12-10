from unittest.mock import patch

from django.test import TestCase

from promise_tracker.emails.services import EmailService
from promise_tracker.emails.tasks import email_send_task
from promise_tracker.users.tests.factories import UnverifiedUserFactory


class EmailTasksIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.service = EmailService()

    @patch("promise_tracker.emails.services.EmailService.send_verification_email")
    def test_email_send_task_calls_service_method(self, mock_send_email):
        user = UnverifiedUserFactory.create()
        verification_code = "123456"

        email_send_task(user_email=user.email, verification_code=verification_code)

        mock_send_email.assert_called_once_with(user.email, verification_code)
