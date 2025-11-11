from config.env import env

# https://docs.celeryproject.org/en/stable/userguide/configuration.html

celery_user = env.str("CELERY_BROKER_USER", default="guest")
celery_password = env.str("CELERY_BROKER_PASSWORD", default="guest")
celery_host = env.str("CELERY_BROKER_HOST", default="rabbitmq")
celery_port = env.str("CELERY_BROKER_PORT", default="5672")

CELERY_BROKER_URL = f"amqp://{celery_user}:{celery_password}@{celery_host}:{celery_port}//"
CELERY_RESULT_BACKEND = "django-db"

CELERY_TIMEZONE = env.str("CELERY_TIMEZONE", default="UTC")

CELERY_TASK_SOFT_TIME_LIMIT = env.int("CELERY_TASK_SOFT_TIME_LIMIT", default=20)
CELERY_TASK_TIME_LIMIT = env.int("CELERY_TASK_TIME_LIMIT", default=30)
CELERY_TASK_MAX_RETRIES = env.int("CELERY_TASK_MAX_RETRIES", default=3)
CELERY_TASK_DEFAULT_RETRY_DELAY = env.int("CELERY_TASK_DEFAULT_RETRY_DELAY", default=5)
