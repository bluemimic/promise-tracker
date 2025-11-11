from django.core.validators import EmailValidator
from django.utils.translation import gettext as _


class CustomEmailValidator(EmailValidator):
    def __init__(self, **kwargs):
        super().__init__(message=_("Enter a valid email address."), **kwargs)
