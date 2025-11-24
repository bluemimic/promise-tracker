from django.db.models import CharField, ImageField
from django.forms import Field

from promise_tracker.common.utils import get_image_upload_to_path


class UploadImageField(ImageField):
    def __init__(self, *args, **kwargs):
        kwargs["upload_to"] = get_image_upload_to_path
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if "upload_to" in kwargs:
            del kwargs["upload_to"]
        return name, path, args, kwargs


class CommaSeparatedField(CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    def to_python(self, value: list[str] | str | None):
        if isinstance(value, list):
            return value
        if value is None:
            return []
        return [item.strip() for item in value.split(",")]

    def get_prep_value(self, value: list[str] | None):
        if not value:
            return ""
        if isinstance(value, (list, tuple, set)):
            return ",".join(str(item).strip() for item in value)
        return str(value).strip()


class CommaSeparatedFormField(Field):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return []

        if isinstance(value, list) or isinstance(value, tuple):
            return [str(v).strip() for v in value if v and str(v).strip()]

        if isinstance(value, str):
            return [s.strip() for s in value.split(",") if s.strip()]

        return []
