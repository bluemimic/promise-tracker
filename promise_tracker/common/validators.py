from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator, EmailValidator, FileExtensionValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext as _


@deconstructible
class CustomEmailValidator(EmailValidator):
    def __init__(self, **kwargs):
        super().__init__(message=_("Enter a valid email address."), **kwargs)


@deconstructible
class ImageValidator(FileExtensionValidator):
    def __init__(self, **kwargs):
        super().__init__(
            allowed_extensions=["jpg", "jpeg", "png", "webp", "svg"],
            message=_("Image in not in valid format!"),
            **kwargs,
        )


@deconstructible
class FileSizeValidator(BaseValidator):
    def __init__(self, max_size_mb: int | None = None, **kwargs):
        max_size_mb = max_size_mb or settings.FILE_MAX_SIZE // (1024 * 1024)
        message = _("Image size exceds {max_size} MB.").format(max_size=max_size_mb)

        super().__init__(limit_value=max_size_mb * 1024 * 1024, message=message, **kwargs)

    def compare(self, a, b):
        return a > b

    def clean(self, x):
        return x.size


@deconstructible
class CommaSeparatedStringValidator:
    def __init__(
        self,
        allow_empty_items: bool = False,
        max_items: int | None = None,
        max_item_length: int | None = None,
        **kwargs,
    ):
        self.max_items = max_items
        self.max_item_length = max_item_length
        self.allow_empty_items = allow_empty_items

    def __call__(self, value: list[str] | str):
        if isinstance(value, list):
            items = [item.strip() for item in value]
        else:
            items = [item.strip() for item in value.split(",")]

        if not self.allow_empty_items and any(not item for item in items):
            raise ValidationError(
                _("Empty items are not allowed."),
                code="empty_item_not_allowed",
            )

        if self.max_items is not None and len(items) > self.max_items:
            raise ValidationError(
                _(f"Ensure there are no more than {self.max_items} items (there are {len(items)})."),
                code="max_items_exceeded",
            )

        if self.max_item_length is not None:
            for item in items:
                if len(item) > self.max_item_length:
                    raise ValidationError(
                        _(
                            f"Ensure each item has no more than {self.max_item_length} characters "
                            f"(item '{item}' has {len(item)} characters)."
                        ),
                        code="max_item_length_exceeded",
                    )
