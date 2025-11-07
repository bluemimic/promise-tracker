from config.env import env

# https://docs.celeryproject.org/en/stable/userguide/configuration.html

celery_user = env.str("CELERY_BROKER_USER", default="guest")
celery_password = env.str("CELERY_BROKER_PASSWORD", default="guest")
celery_host = env.str("CELERY_BROKER_HOST", default="rabbitmq")
celery_port = env.str("CELERY_BROKER_PORT", default="5672")

CELERY_BROKER_URL = f"amqp://{celery_user}:{celery_password}@{celery_host}:{celery_port}//"
CELERY_RESULT_BACKEND = "django-db"

CELERY_TIMEZONE = "UTC"

CELERY_TASK_SOFT_TIME_LIMIT = 20
CELERY_TASK_TIME_LIMIT = 30
CELERY_TASK_MAX_RETRIES = 3
