from celery import Task
from django.conf import settings


class BaseTask(Task):
    max_retries = settings.CELERY_TASK_MAX_RETRIES
    default_retry_delay = settings.CELERY_TASK_DEFAULT_RETRY_DELAY
    time_limit = settings.CELERY_TASK_TIME_LIMIT
    soft_time_limit = settings.CELERY_TASK_SOFT_TIME_LIMIT
