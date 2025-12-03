from django import forms
from django.utils.translation import gettext_lazy as _

from promise_tracker.common.forms import FIELD_INVALID, FIELD_REQUIRED
from promise_tracker.common.utils import generate_model_form_errors
from promise_tracker.users.models import BaseUser


class UserCreateForm(forms.ModelForm):
    another_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        label=_("Confirm password"),
        help_text=_("Enter the same password as before, for verification."),
    )

    class Meta:
        model = BaseUser
        fields = ["email", "password", "another_password", "name", "surname", "username"]

        widgets = {
            "password": forms.PasswordInput(),
        }

        help_texts = {
            "password": _(
                "Password must be at least 10 characters long, and contain a mix of letters, numbers, and special characters."
            ),
        }

        error_messages = generate_model_form_errors(fields)


class UserCreateAdminForm(UserCreateForm):
    class Meta(UserCreateForm.Meta):
        fields = UserCreateForm.Meta.fields + ["is_admin"]

        error_messages = generate_model_form_errors(fields)


class UserEditForm(UserCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].required = False
        self.fields["another_password"].required = False


class UserEditAdminForm(UserCreateAdminForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].required = False
        self.fields["another_password"].required = False


class UserVerifyForm(forms.Form):
    verification_code = forms.CharField(
        required=True,
        max_length=6,
        label=_("Verification Code"),
        help_text=_("Enter the 6-digit verification code sent to your email."),
        error_messages={
            "required": FIELD_REQUIRED.format(field=_("Verification code")),
            "max_length": FIELD_INVALID.format(field=_("Verification code")),
        },
    )
