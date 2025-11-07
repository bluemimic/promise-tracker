# import logging
# import sys

# from loguru import logger


# class IgnoreFilter(logging.Filter):
#     def filter(self, record):
#         return False


# class LoggersSetup:
#     @staticmethod
#     def setup_settings(INSTALLED_APPS, MIDDLEWARE, middleware_position=None):
#         django_loguru_middleware = "config.settings.loggers.middleware.LoguruMiddleware"

#         if middleware_position is None:
#             MIDDLEWARE = MIDDLEWARE + [django_loguru_middleware]
#         else:
#             _middleware = MIDDLEWARE[:]
#             _middleware.insert(middleware_position, django_loguru_middleware)
#             MIDDLEWARE = _middleware

#         return INSTALLED_APPS, MIDDLEWARE

#     @staticmethod
#     def setup_loguru():
#         from config.settings.loggers.settings import LOGGING_FORMAT, LOG_LEVEL, LOG_PATH, LoggingFormat

#         logger.remove()

#         if LOGGING_FORMAT == LoggingFormat.DEV:
#             logger.add(
#                 sys.stdout,
#                 level=LOG_LEVEL,
#                 format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
#                 "| <level>{level}</level> "
#                 "| <cyan>{module}</cyan> "
#                 "| {file}:{line} {function}"
#                 "| pid={process} tid={thread} "
#                 "| {message}",
#                 colorize=True,
#             )

#         if LOGGING_FORMAT == LoggingFormat.PROD:
#             logger.add(
#                 LOG_PATH,
#                 level=LOG_LEVEL,
#                 rotation="10 MB",
#                 retention="7 days",
#                 serialize=True,
#                 encoding="utf-8",
#             )

#     @staticmethod
#     def setup_logging_dict():
#         class InterceptHandler(logging.Handler):
#             def emit(self, record):
#                 try:
#                     level = logger.level(record.levelname).name

#                 except ValueError:
#                     level = record.levelno

#                 logger.opt(exception=record.exc_info).log(level, record.getMessage())

#         return {
#             "version": 1,
#             "disable_existing_loggers": False,
#             "handlers": {
#                 "loguru": {
#                     "class": "logging.StreamHandler",
#                 },
#             },
#             "loggers": {
#                 "django.server": {
#                     "handlers": ["loguru"],
#                     "propagate": False,
#                     "filters": ["ignore"],
#                 },
#                 "django.request": {
#                     "handlers": ["loguru"],
#                     "propagate": False,
#                     "filters": ["ignore"],
#                 },
#                 "django": {
#                     "handlers": ["loguru"],
#                     "level": "INFO",
#                 },
#             },
#             "filters": {
#                 "ignore": {
#                     "()": "config.settings.loggers.setup.IgnoreFilter",
#                 }
#             },
#         }
