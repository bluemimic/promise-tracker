# mypy: disable-error-code="assignment"

from django.db import models
from django.db.models import CheckConstraint, F, Q
from django.db.models.fields import Field
from django.db.models.functions import Now
from django.utils import timezone
from django.utils.translation import gettext as _

from promise_tracker.common.fields import CommaSeparatedField, UploadImageField
from promise_tracker.common.models import BaseModel
from promise_tracker.common.validators import CommaSeparatedStringValidator, FileSizeValidator, ImageValidator


class LegislativeInstitution(BaseModel):
    class Type(models.TextChoices):
        PARLIAMENT = "Parliament", _("Parliament")
        COUNCIL = "Council", _("Council")

    class Level(models.TextChoices):
        NATIONAL = "National", _("National")
        REGIONAL = "Regional", _("Regional")
        STATE_CITY = "State City", _("State City")

    name: Field = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_("Name"),
        help_text=_("The name of the legislative institution."),
    )
    institution_type: Field = models.CharField(
        max_length=50,
        choices=Type.choices,
        null=False,
        blank=False,
        verbose_name=_("Type"),
        help_text=_("The type of legislative institution."),
    )
    institution_level: Field = models.CharField(
        max_length=50,
        choices=Level.choices,
        null=False,
        blank=False,
        verbose_name=_("Level"),
        help_text=_("The level of the legislative institution."),
    )
    logo: Field = UploadImageField(
        null=True,
        blank=True,
        validators=[
            ImageValidator(),
            FileSizeValidator(),
        ],
        verbose_name=_("Logo"),
        help_text=_("The logo of the legislative institution."),
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Legislative Institution")
        verbose_name_plural = _("Legislative Institutions")
        constraints = [
            models.UniqueConstraint(
                fields=["name", "institution_type", "institution_level"],
                name="unique_institution_name_type_level",
                violation_error_message=_(
                    "A legislative institution with the same name, type and level already exists."
                ),
            ),
        ]


class PoliticalParty(BaseModel):
    name: Field = models.CharField(
        unique=True,
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_("Name"),
        help_text=_("The name of the political party."),
        error_messages={
            "unique": _("A political party %(value)s already exists."),
        },
    )
    email: Field = models.EmailField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_("Email"),
        help_text=_("The contact email of the political party."),
    )
    established_date: Field = models.DateField(
        null=False,
        blank=False,
        verbose_name=_("Established Date"),
        help_text=_("The date when the political party was established."),
    )
    liquidated_date: Field = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Liquidated Date"),
        help_text=_("The date when the political party was liquidated, if applicable."),
    )
    ideologies: Field = CommaSeparatedField(
        null=True,
        blank=True,
        validators=[
            CommaSeparatedStringValidator(max_item_length=255),
        ],
        verbose_name=_("Ideologies"),
        help_text=_("The ideologies associated with the political party, separated by commas."),
        error_messages={
            "empty_item_not_allowed": _("Ideology array is not valid!"),
        },
    )
    logo: Field = UploadImageField(
        null=True,
        blank=True,
        validators=[
            ImageValidator(),
            FileSizeValidator(),
        ],
        verbose_name=_("Logo"),
        help_text=_("The logo of the political party."),
    )

    @property
    def is_active(self) -> bool:
        return self.liquidated_date is None or self.liquidated_date > timezone.now()

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Political Party")
        verbose_name_plural = _("Political Parties")

        constraints = [
            CheckConstraint(
                check=(Q(liquidated_date__isnull=True) | Q(liquidated_date__gte=F("established_date"))),
                name="liquidated_date_gte_established_date",
                violation_error_message=_("Liquidated date is smaller than established date."),
            ),
            CheckConstraint(
                check=Q(established_date__lte=Now()),
                name="established_date_lte_today",
                violation_error_message=_("Established date is in the future."),
            ),
            CheckConstraint(
                check=(Q(liquidated_date__isnull=True) | Q(liquidated_date__lte=Now())),
                name="liquidated_date_lte_today",
                violation_error_message=_("Liquidated date is in the future."),
            ),
        ]


class PoliticalUnion(BaseModel):
    name: Field = models.CharField(
        unique=True,
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_("Name"),
        help_text=_("The name of the political union."),
        error_messages={
            "unique": _("A political union %(value)s already exists."),
        },
    )
    email: Field = models.EmailField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_("Email"),
        help_text=_("The contact email of the political union."),
    )
    established_date: Field = models.DateField(
        null=False,
        blank=False,
        verbose_name=_("Established Date"),
        help_text=_("The date when the political union was established."),
    )
    liquidated_date: Field = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Liquidated Date"),
        help_text=_("The date when the political union was liquidated, if applicable."),
    )
    ideologies: Field = CommaSeparatedField(
        null=True,
        blank=True,
        validators=[
            CommaSeparatedStringValidator(max_item_length=255),
        ],
        verbose_name=_("Ideologies"),
        help_text=_("The ideologies associated with the political union, separated by commas."),
        error_messages={
            "empty_item_not_allowed": _("Ideology array is not valid!"),
        },
    )
    logo: Field = UploadImageField(
        null=True,
        blank=True,
        validators=[
            ImageValidator(),
            FileSizeValidator(),
        ],
        verbose_name=_("Logo"),
        help_text=_("The logo of the political union."),
    )
    parties: Field = models.ManyToManyField(
        to=PoliticalParty,
        related_name="unions",
        verbose_name=_("Parties"),
        help_text=_("The political parties that are part of this union."),
    )

    @property
    def is_active(self) -> bool:
        return self.liquidated_date is None or self.liquidated_date > timezone.now().date()

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Political Union")
        verbose_name_plural = _("Political Unions")

        constraints = [
            CheckConstraint(
                check=(Q(liquidated_date__isnull=True) | Q(liquidated_date__gte=F("established_date"))),
                name="union_liquidated_date_gte_established_date",
                violation_error_message=_("Liquidated date is smaller than established date."),
            ),
            CheckConstraint(
                check=Q(established_date__lte=Now()),
                name="union_established_date_lte_today",
                violation_error_message=_("Established date is in the future."),
            ),
            CheckConstraint(
                check=(Q(liquidated_date__isnull=True) | Q(liquidated_date__lte=Now())),
                name="union_liquidated_date_lte_today",
                violation_error_message=_("Liquidated date is in the future."),
            ),
        ]


class Convocation(BaseModel):
    name: Field = models.CharField(
        unique=True,
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_("Name"),
        help_text=_("The name of the convocation."),
        error_messages={
            "unique": _("A convocation %(value)s already exists."),
        },
    )
    start_date: Field = models.DateField(
        null=False,
        blank=False,
        verbose_name=_("Start Date"),
        help_text=_("The start date of the convocation."),
    )
    end_date: Field = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("End Date"),
        help_text=_("The end date of the convocation, if applicable."),
    )
    legislative_institution: Field = models.ForeignKey(
        to=LegislativeInstitution,
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        related_name="convocations",
        verbose_name=_("Legislative Institution"),
        help_text=_("The legislative institution associated with this convocation."),
    )
    political_parties: Field = models.ManyToManyField(
        to=PoliticalParty,
        related_name="convocations",
        verbose_name=_("Political Parties"),
        help_text=_("The political parties participating in this convocation."),
    )
    political_unions: Field = models.ManyToManyField(
        to=PoliticalUnion,
        related_name="convocations",
        verbose_name=_("Political Unions"),
        help_text=_("The political unions participating in this convocation."),
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Convocation")
        verbose_name_plural = _("Convocations")

        constraints = [
            CheckConstraint(
                check=(Q(end_date__isnull=True) | Q(end_date__gte=F("start_date"))),
                name="convocation_end_date_gte_start_date",
                violation_error_message=_("End date is smaller than start date."),
            ),
            CheckConstraint(
                check=Q(start_date__lte=Now()),
                name="convocation_start_date_lte_today",
                violation_error_message=_("Start date is in the future."),
            ),
            CheckConstraint(
                check=(Q(end_date__isnull=True) | Q(end_date__lte=Now())),
                name="convocation_end_date_lte_today",
                violation_error_message=_("End date is in the future."),
            ),
        ]
