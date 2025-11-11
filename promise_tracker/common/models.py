import uuid

from django.conf import settings
from django.db import models
from django.db.models.fields import Field


class BaseModel(models.Model):
    id: Field = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at: Field = models.DateTimeField(db_index=True, auto_now_add=True)
    updated_at: Field = models.DateTimeField(auto_now=True)

    created_by: Field = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )

    updated_by: Field = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
    )

    class Meta:
        abstract = True
