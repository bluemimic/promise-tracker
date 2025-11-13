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


class CommaSeparatedStringValidator:
    def __init__(self, max_items=None):
        self.max_items = max_items

    def __call__(self, value):
        items = [item.strip() for item in value.split(",")]

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
