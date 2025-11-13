# mypy: disable-error-code="assignment"

from django.db import models
from django.db.models import CheckConstraint, F, Q
from django.db.models.fields import Field
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from promise_tracker.common.models import BaseModel


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
            )
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
    political_parties: Field = models.ManyToManyField(
        to=PoliticalParty,
        related_name="convocations",
        verbose_name=_("Political Parties"),
        help_text=_("The political parties participating in this convocation."),
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
            )
        ]
