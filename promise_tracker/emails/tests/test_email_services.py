from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _

from promise_tracker.emails.services import EmailService
from promise_tracker.users.tests.factories import UnverifiedUserFactory


class EmailServicesIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.service = EmailService()

    @override_settings(EMAIL_SENDER="aa@aa.aa")
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_verification_email_sends_email(self):
        user = UnverifiedUserFactory.create()
        verification_code = "123456"

        self.service.send_verification_email(user_email=user.email, verification_code=verification_code)

        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]

        self.assertEqual(sent_email.subject, _("Your Verification Code"))
        self.assertEqual(sent_email.from_email, settings.EMAIL_SENDER)
        self.assertEqual(sent_email.to, [user.email])
        self.assertIn(verification_code, sent_email.body)
