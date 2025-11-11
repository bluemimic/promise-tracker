from django.db.models import EmailField
from django.utils.translation import gettext as _


class UniqueEmailField(EmailField):
    def __init__(self, *args, **kwargs):
        kwargs["unique"] = True
        kwargs["error_messages"] = {
            "unique": _("A user with email {email} already exists.").format(email="%(value)s"),
        }
        super().__init__(*args, **kwargs)
