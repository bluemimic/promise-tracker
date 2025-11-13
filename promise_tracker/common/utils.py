from typing import Any, Optional, Type

from django.core.paginator import Page, Paginator
from django.db import models
from django.db.models import Model, QuerySet
from django.forms import Form
from django.forms.widgets import CheckboxInput, Select, SelectMultiple
from loguru import logger

from promise_tracker.common.forms import FIELD_INVALID, FIELD_REQUIRED
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


def bootstrapify_form(form: Form, floating: bool = False) -> Form:
    for field in form.__iter__():
        if isinstance(field.field.widget, CheckboxInput):
            field.field.widget.attrs["class"] = "form-check-input"
        elif isinstance(field.field.widget, (Select, SelectMultiple)):
            field.field.widget.attrs["class"] = "form-select"
        else:
            field.field.widget.attrs["class"] = "form-control"

        if floating:
            field.field.widget.attrs["placeholder"] = " "

        if field.errors:
            field.field.widget.attrs["class"] += " is-invalid"

    return form


def generate_model_form_errors(fields: list[str]) -> dict[str, dict[str, str]]:
    errors = {}

    for field in fields:
        errors[field] = {
            "required": FIELD_REQUIRED.format(field=field.capitalize()),
            "invalid": FIELD_INVALID.format(field=field.capitalize()),
        }

    return errors


def is_htmx_request(request) -> bool:
    return request.headers.get("HX-Request") == "true" or request.META.get("HTTP_HX_REQUEST") == "true"


def prepare_get_params(request, exclude: list[str] | None = None) -> str:
    exclude = exclude or []
    params = request.GET.copy()

    for param in exclude:
        if param in params:
            params.pop(param)

    querystring = params.urlencode()

    return querystring


def paginate_queryset(request, queryset: QuerySet, per_page: int = 10) -> Page:
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page", 1)

    page_obj = paginator.get_page(page_number)

    return page_obj
