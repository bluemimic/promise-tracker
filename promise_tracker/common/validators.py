from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class CustomEmailValidator(EmailValidator):
    def __init__(self, **kwargs):
        super().__init__(message=_("Enter a valid email address."), **kwargs)


@deconstructible
class CommaSeparatedStringValidator:
    def __init__(
        self,
        allow_empty_items: bool = False,
        max_items: int | None = None,
        max_item_length: int | None = None,
        min_items: int | None = None,
        **kwargs,
    ):
        self.max_items = max_items
        self.max_item_length = max_item_length
        self.allow_empty_items = allow_empty_items
        self.min_items = min_items

    def __call__(self, value: list[str] | str):
        if isinstance(value, list):
            items = [item.strip() for item in value]
        else:
            items = [item.strip() for item in value.split(",")]

        if not self.allow_empty_items and (len(items) == 0 or any(not item for item in items)):
            raise ValidationError(
                _("Empty items are not allowed."),
                code="empty_item_not_allowed",
            )

        if self.max_items is not None and len(items) > self.max_items:
            raise ValidationError(
                _(
                    "Ensure there are no more than {max_items} items (there are {number_of_items}).".format(
                        max_items=self.max_items,
                        number_of_items=len(items),
                    )
                ),
                code="max_items_exceeded",
            )

        if self.max_item_length is not None:
            for item in items:
                if len(item) > self.max_item_length:
                    raise ValidationError(
                        _(
                            "Ensure each item has no more than {max_item_length} characters (item '{item}' has {length} characters).".format(
                                max_item_length=self.max_item_length,
                                item=item,
                                length=len(item),
                            ),
                        ),
                        code="max_item_length_exceeded",
                    )

        if self.min_items is not None and len(items) < self.min_items:
            raise ValidationError(
                _(
                    "Ensure there are at least {min_items} items (there are {number_of_items}).".format(
                        min_items=self.min_items,
                        number_of_items=len(items),
                    )
                ),
                code="min_items_not_met",
            )
