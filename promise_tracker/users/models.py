# mypy: disable-error-code="assignment"

from datetime import datetime

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.fields import Field
from django.utils.translation import gettext as _

from promise_tracker.common.fields import UniqueEmailField
from promise_tracker.common.models import BaseModel
from promise_tracker.common.validators import CustomEmailValidator


class BaseUser(BaseModel, AbstractBaseUser, PermissionsMixin):
    name: Field = models.CharField(
        max_length=255, null=False, blank=False, verbose_name=_("Name"), help_text=_("The name of the user.")
    )
    surname: Field = models.CharField(
        max_length=255, null=False, blank=False, verbose_name=_("Surname"), help_text=_("The surname of the user.")
    )
    email: Field = UniqueEmailField(
        validators=[
            CustomEmailValidator(),
        ],
        max_length=255,
        unique=True,
        null=False,
        blank=False,
        verbose_name=_("Email address"),
        help_text=_("The email address of the user."),
    )
    username: Field = models.CharField(
        max_length=255, null=False, blank=False, verbose_name=_("Username"), help_text=_("The username of the user.")
    )
    password: Field = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_("Password"),
        help_text=_("The hashed password of the user."),
    )

    verification_code: Field = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Verification code"),
        help_text=_("The verification code for email verification."),
    )
    verification_code_expires_at: Field = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Verification code expiry"),
        help_text=_("The expiry date and time of the verification code."),
    )
    verification_email_sent_at: Field = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Verification email sent at"),
        help_text=_("The date and time when the verification email was sent."),
    )

    is_active: Field = models.BooleanField(
        default=True,
        verbose_name=_("Is active?"),
        help_text=_("Designates whether this user should be treated as active."),
        null=False,
        blank=False,
    )
    is_admin: Field = models.BooleanField(
        default=False,
        verbose_name=_("Is admin?"),
        help_text=_("Designates whether the user has admin privileges."),
        null=False,
        blank=False,
    )
    is_verified: Field = models.BooleanField(
        default=False,
        verbose_name=_("Is verified?"),
        help_text=_("Designates whether the user has verified their email address."),
        null=False,
        blank=False,
    )
    is_deleted: Field = models.BooleanField(
        default=False,
        verbose_name=_("Is deleted?"),
        help_text=_("Designates whether the user has been soft-deleted."),
        null=False,
        blank=False,
    )

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["username", "name", "surname", "password"]

    def set_verification_code(self, code: str, expires_at: datetime) -> None:
        self.verification_code = code
        self.verification_code_expires_at = expires_at

    def __str__(self):
        return f"{self.name} {self.surname} ({self.email})"

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
