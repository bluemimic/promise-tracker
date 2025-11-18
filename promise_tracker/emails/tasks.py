from celery import shared_task
from loguru import logger

from promise_tracker.emails.services import EmailService
from promise_tracker.tasks.models import BaseTask


@shared_task(bind=True, base=BaseTask, name="send_email_task")
def email_send_task(self, user_email: str, verification_code: str) -> None:
    logger.info(f"Starting task {self.name} (id: {self.request.id})")

    email_service = EmailService()

    try:
        email_service.send_verification_email(user_email, verification_code)
    except Exception as exc:
        logger.warning(f"Exception occurred while sending email: {exc}")
        self.retry(exc=exc)

    logger.info(f"Completed task {self.name} (id: {self.request.id})")
