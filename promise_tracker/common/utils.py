from typing import Any, Optional, Type

from django.db import models
from loguru import logger

from promise_tracker.common.types import DjangoModelType
from promise_tracker.core.exceptions import NotFoundError


def get_object_or_none(model: Type[DjangoModelType], **kwargs) -> Optional[DjangoModelType]:
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


def get_object_or_raise(model: Type[DjangoModelType], message: str, **kwargs) -> DjangoModelType:
    obj = get_object_or_none(model, **kwargs)

    if obj is None:
        logger.error(f"Object not found: {model.__name__} with {kwargs}")
        raise NotFoundError(message)

    return obj


def has_changed_field(instance: models.Model, field: str, new_value: Any) -> bool:
    return getattr(instance, field) != new_value


def generate_randon_string(length: int) -> str:
    import random
    import string

    return "".join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))


def generate_random_email() -> str:
    random_username = generate_randon_string(10)
    random_domain = generate_randon_string(5)
    random_email = f"{random_username}@{random_domain}.com"

    return random_email
