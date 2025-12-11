from __future__ import annotations

from django.db import models
from django.db.models import CheckConstraint, Q
from django.db.models.fields import Field
from django.utils.translation import gettext_lazy as _

from promise_tracker.classifiers.models import Convocation, PoliticalParty
from promise_tracker.common.fields import CommaSeparatedField
from promise_tracker.common.models import BaseModel
from promise_tracker.common.validators import CommaSeparatedStringValidator
from promise_tracker.users.models import BaseUser


class Promise(BaseModel):
    class ReviewStatus(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        APPROVED = "APPROVED", _("Approved")
        REJECTED = "REJECTED", _("Rejected")

    name: Field = models.CharField(
        max_length=255,
        unique=True,
        null=False,
        blank=False,
        verbose_name=_("Name"),
        help_text=_("The name of the promise."),
    )
    description: Field = models.TextField(
        max_length=2000,
        null=False,
        blank=False,
        verbose_name=_("Description"),
        help_text=_("A detailed description of the promise."),
    )
    sources: Field = CommaSeparatedField(
        null=False,
        blank=False,
        validators=[
            CommaSeparatedStringValidator(
                min_items=1,
                max_item_length=1000,
            )
        ],
        verbose_name=_("Sources"),
        help_text=_("A comma-separated list of sources related to the promise."),
        error_messages={
            "null": _("Sources are null."),
            "empty_item_not_allowed": _("Sources list is not valid."),
        },
    )
    date: Field = models.DateField(
        null=False,
        blank=False,
        verbose_name=_("Date"),
        help_text=_("The date when the promise was made."),
    )
    party: Field = models.ForeignKey(
        to=PoliticalParty,
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        related_name="promises",
        verbose_name=_("Political Party"),
        help_text=_("The political party associated with this promise."),
    )
    convocation: Field = models.ForeignKey(
        to=Convocation,
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        related_name="promises",
        verbose_name=_("Convocation"),
        help_text=_("The convocation during which this promise was made."),
    )

    review_status: Field = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        null=False,
        blank=False,
        verbose_name=_("Review status"),
        help_text=_("The review status of the promise."),
    )
    review_date: Field = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Review Date"),
        help_text=_("The date and time when the promise was reviewed."),
    )
    reviewer: Field = models.ForeignKey(
        to=BaseUser,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reviewed_promises",
        verbose_name=_("Reviewer"),
        help_text=_("The user who reviewed the promise."),
    )

    @property
    def is_final(self) -> bool:
        return self.results.filter(is_final=True, review_status=PromiseResult.ReviewStatus.APPROVED).exists()

    @property
    def is_reviewed(self) -> bool:
        return self.review_status != self.ReviewStatus.PENDING

    @property
    def is_unreviewed(self) -> bool:
        return self.review_status == self.ReviewStatus.PENDING

    @property
    def is_approved(self) -> bool:
        return self.review_status == self.ReviewStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.review_status == self.ReviewStatus.REJECTED

    @property
    def final_result(self) -> PromiseResult.CompletionStatus | None:
        final_result_qs = self.results.filter(is_final=True, review_status=PromiseResult.ReviewStatus.APPROVED)

        if final_result_qs.exists():
            return final_result_qs.first()
        return None

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Promise")
        verbose_name_plural = _("Promises")

        constraints = [
            CheckConstraint(
                check=(~Q(review_status="PENDING") & Q(review_date__isnull=False))
                | (Q(review_status="PENDING") & Q(review_date__isnull=True)),
                name="promise_review_date_status_consistency",
                violation_error_message=_("Inconsistent review date and status."),
            ),
        ]


class PromiseResult(BaseModel):
    class CompletionStatus(models.TextChoices):
        COMPLETED = "COMPLETED", _("Completed")
        ABANDONED = "ABANDONED", _("Abandoned")

    class ReviewStatus(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        APPROVED = "APPROVED", _("Approved")
        REJECTED = "REJECTED", _("Rejected")

    name: Field = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_("Name"),
        help_text=_("The name of the promise result."),
    )
    description: Field = models.TextField(
        max_length=2000,
        null=False,
        blank=False,
        verbose_name=_("Description"),
        help_text=_("A detailed description of the promise result."),
    )
    sources: Field = CommaSeparatedField(
        null=False,
        blank=False,
        validators=[
            CommaSeparatedStringValidator(
                min_items=1,
                max_item_length=1000,
            )
        ],
        verbose_name=_("Sources"),
        help_text=_("A comma-separated list of sources related to the promise result."),
        error_messages={
            "null": _("Sources are null."),
            "empty_item_not_allowed": _("Sources list is not valid."),
        },
    )
    date: Field = models.DateField(
        null=False,
        blank=False,
        verbose_name=_("Date"),
        help_text=_("The date when the promise result was determined."),
    )
    is_final: Field = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        verbose_name=_("Is Final"),
        help_text=_("Indicates whether this is the final result for the promise."),
    )
    status: Field = models.CharField(
        max_length=20,
        choices=CompletionStatus.choices,
        null=True,
        blank=True,
        verbose_name=_("Status"),
        help_text=_("The status of the promise result."),
    )
    promise: Field = models.ForeignKey(
        to=Promise,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name=_("Promise"),
        help_text=_("The promise associated with this result."),
    )

    review_status: Field = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        null=False,
        blank=False,
        verbose_name=_("Review status"),
        help_text=_("The review status of the promise result."),
    )
    review_date: Field = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Review Date"),
        help_text=_("The date and time when the promise result was reviewed."),
    )
    reviewer: Field = models.ForeignKey(
        to=BaseUser,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reviewed_promise_results",
        verbose_name=_("Reviewer"),
        help_text=_("The user who reviewed the promise result."),
    )

    @property
    def is_reviewed(self) -> bool:
        return self.review_status != self.ReviewStatus.PENDING

    @property
    def is_unreviewed(self) -> bool:
        return self.review_status == self.ReviewStatus.PENDING

    @property
    def is_completed(self) -> bool:
        return self.status == self.CompletionStatus.COMPLETED

    @property
    def is_abandoned(self) -> bool:
        return self.status == self.CompletionStatus.ABANDONED

    @property
    def is_approved(self) -> bool:
        return self.review_status == self.ReviewStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.review_status == self.ReviewStatus.REJECTED

    def __str__(self) -> str:
        return f"{self.name} ({self.promise.name})"

    class Meta:
        verbose_name = _("Promise Result")
        verbose_name_plural = _("Promise Results")

        constraints = [
            CheckConstraint(
                check=Q(is_final=True, status__isnull=False) | Q(is_final=False),
                name="promiseresult_final_status_consistency",
                violation_error_message=_("Final promise result status is not set."),
            ),
            CheckConstraint(
                check=(~Q(review_status="PENDING") & Q(review_date__isnull=False))
                | (Q(review_status="PENDING") & Q(review_date__isnull=True)),
                name="promiseresult_review_date_status_consistency",
                violation_error_message=_("Inconsistent review date and status."),
            ),
        ]

        unique_together = [
            ("promise", "name"),
        ]
