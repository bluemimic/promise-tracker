from typing import TypeVar

from django.db import models

from promise_tracker.common.models import BaseModel

BaseModelType = TypeVar("BaseModelType", bound=BaseModel)
DjangoModelType = TypeVar("DjangoModelType", bound=models.Model)
