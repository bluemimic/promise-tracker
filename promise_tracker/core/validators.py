from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class CustomPasswordValidator:
    def validate(self, password, user=None):
        if not any(c.isdigit() for c in password):
            raise ValidationError(_("Password must contain at least one digit."), code="no_digit")

        if not any(c.isupper() for c in password):
            raise ValidationError(_("Password must contain at least one uppercase letter."), code="no_upper")

        if not any(c in "!@#$%^&*()-_=+[]{};:,.<>?/|\\~" for c in password):
            raise ValidationError(_("Password must contain at least one special character."), code="no_special")

    def get_help_text(self):
        return _("Your password must contain at least one digit, one uppercase letter, and one special character.")
