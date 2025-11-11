from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils.translation import gettext as _
from loguru import logger


class EmailService:
    @transaction.atomic
    @logger.catch(reraise=True)
    def send_verification_email(self, user_email: str, verification_code: str) -> None:
        logger.debug(f"Sending verification email to {user_email}")

        subject = _("Your Verification Code")
        to = user_email
        from_email = settings.EMAIL_SENDER
        plain_text = _("Your verification code is: {code}").format(code=verification_code)
        html = _("<p>Your verification code is: <strong>{code}</strong></p>").format(code=verification_code)

        msg = EmailMultiAlternatives(subject, plain_text, from_email, [to])
        msg.attach_alternative(html, "text/html")

        msg.send(fail_silently=False)

        logger.info(f"Sent verification email to {user_email}")
