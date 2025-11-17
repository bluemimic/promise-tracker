from datetime import date
from uuid import UUID

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from loguru import logger
from rolepermissions.checkers import has_role

from promise_tracker.common.services import BaseService
from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.core.exceptions import ApplicationError, PermissionViolationError
from promise_tracker.core.roles import Administrator
from promise_tracker.promises.models import Promise, PromiseResult
from promise_tracker.users.models import BaseUser


class PromiseResultService:
    def __init__(self, performed_by: BaseUser, base_service: BaseService[PromiseResult] | None = None) -> None:
        self.performed_by = performed_by
        self.base_service: BaseService[PromiseResult] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("Promise result not found.")

    PROMISE_NOT_FOUND = _("Promise does not exist!")
    CANNOT_ADD_TO_FINAL_PROMISE = _("Cannot add result to final promise!")
    CANNOT_ADD_FINAL_BECAUSE_LATER_RESULTS = _("Cannot add final result because promise has later results!")
    FINAL_STATUS_NOT_SPECIFIED = _("Final result status is not specified!")
    STATUS_NOT_ALLOWED_FOR_NON_FINAL = _("Cannot specify result status when result is not final!")
    UNIQUE_CONSTRAINT_MESSAGE = _("Result {name} already exists!")
    CANNOT_EDIT_REVIEWED = _("Cannot modify reviewed result!")
    CANNOT_DELETE_REVIEWED = _("Cannot delete reviewed result!")
    CANNOT_CHANGE_STATUS = _("Cannot change status of already reviewed result!")
    CANNOT_EVALUATE_BECAUSE_PROMISE_HAS_FINAL = _("Cannot evaluate result, because promise has a final result!")
    CANNOT_EVALUATE_FINAL_BECAUSE_LATER_RESULTS = _(
        "Cannot evaluate final result, because promise has later approved final results!"
    )
    DATE_IN_FUTURE = _("Promise result date is in the future.")
    RESULT_EARLIER_THAN_PROMISE = _("Result date is earlier than promise date.")

    def _ensure_dont_have_approved_final_result(self, promise: Promise, message: str) -> None:
        if promise.results.filter(is_final=True, review_status=PromiseResult.ReviewStatus.APPROVED).exists():
            raise ApplicationError(message)

    def _ensure_can_add_final_result(
        self, promise: Promise, date: date, status: PromiseResult.CompletionStatus | None
    ) -> None:
        self._ensure_status_is_not_null(status)

        self._ensure_dont_have_later_approved_final_result(promise, date, self.CANNOT_ADD_FINAL_BECAUSE_LATER_RESULTS)

    def _ensure_dont_have_later_approved_final_result(self, promise: Promise, date: date, message: str) -> None:
        latest_date = self._get_latest_approved_date(promise)

        if latest_date and latest_date > date:
            raise ApplicationError(message)

    def _ensure_status_is_not_null(self, status: PromiseResult.CompletionStatus | None) -> None:
        if status is None:
            raise ApplicationError(self.FINAL_STATUS_NOT_SPECIFIED)

    def _get_latest_approved_date(self, promise: Promise):
        qs = promise.results.filter(review_status=PromiseResult.ReviewStatus.APPROVED).order_by("-date")

        if not qs.exists():
            return None

        return qs.first().date

    def _ensure_is_owner_or_admin(self, result: PromiseResult) -> None:
        if not has_role(self.performed_by, Administrator):
            if result.created_by is None or self.performed_by.id != result.created_by.id:
                raise PermissionViolationError()

    def _ensure_is_not_reviewed(self, result: PromiseResult, message: str) -> None:
        if result.is_reviewed:
            raise ApplicationError(message)

    def _ensure_date_is_valid(self, promise: Promise, date: date) -> None:
        if date > timezone.now().date():
            raise ApplicationError(self.DATE_IN_FUTURE)

        if date < promise.date:
            raise ApplicationError(self.RESULT_EARLIER_THAN_PROMISE)

    @transaction.atomic
    def create_result(
        self,
        name: str,
        description: str,
        sources: list[str],
        is_final: bool,
        date: date,
        promise_id: UUID,
        status: PromiseResult.CompletionStatus | None = None,
    ) -> PromiseResult:
        logger.debug(f"Creating promise result: {name}")

        promise = get_object_or_raise(Promise, self.PROMISE_NOT_FOUND, id=promise_id)

        self._ensure_dont_have_approved_final_result(promise, self.CANNOT_ADD_TO_FINAL_PROMISE)
        self._ensure_date_is_valid(promise, date)

        if is_final:
            self._ensure_can_add_final_result(promise, date, status)

        if status and not is_final:
            raise ApplicationError(self.STATUS_NOT_ALLOWED_FOR_NON_FINAL)

        result = PromiseResult(
            name=name,
            description=description,
            sources=sources,
            is_final=is_final,
            date=date,
            status=status,
            promise=promise,
        )

        try:
            result = self.base_service.create_base(result, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        logger.info(f"Created promise result: {result.name} (ID: {result.id})")

        return result

    @transaction.atomic
    def edit_result(
        self,
        id: UUID,
        name: str,
        description: str,
        sources: list[str],
        is_final: bool,
        date: date,
        promise_id: UUID,
        status: PromiseResult.CompletionStatus | None = None,
    ) -> PromiseResult:
        result = get_object_or_raise(PromiseResult, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_is_owner_or_admin(result)
        self._ensure_is_not_reviewed(result, self.CANNOT_EDIT_REVIEWED)
        promise = get_object_or_raise(Promise, self.PROMISE_NOT_FOUND, id=promise_id)

        self._ensure_date_is_valid(promise, date)

        self._ensure_dont_have_approved_final_result(promise, self.CANNOT_ADD_TO_FINAL_PROMISE)

        if is_final:
            self._ensure_can_add_final_result(promise, date, status)

        if status and not is_final:
            raise ApplicationError(self.STATUS_NOT_ALLOWED_FOR_NON_FINAL)

        result.name = name
        result.description = description
        result.sources = sources
        result.is_final = is_final
        result.date = date
        result.status = status
        result.promise = promise

        try:
            result = self.base_service.edit_base(result, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        logger.info(f"Edited promise result: {result.id}")

        return result

    @transaction.atomic
    def delete_result(self, id: UUID) -> None:
        result = get_object_or_raise(PromiseResult, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_is_owner_or_admin(result)
        self._ensure_is_not_reviewed(result, self.CANNOT_DELETE_REVIEWED)

        self.base_service.delete_base(result)

    @transaction.atomic
    def evaluate_result(self, id: UUID, new_status: PromiseResult.ReviewStatus) -> PromiseResult:
        result = get_object_or_raise(PromiseResult, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_is_not_reviewed(result, self.CANNOT_CHANGE_STATUS)

        if new_status == PromiseResult.ReviewStatus.APPROVED:
            promise = result.promise

            self._ensure_dont_have_approved_final_result(promise, self.CANNOT_EVALUATE_BECAUSE_PROMISE_HAS_FINAL)

            if result.is_final:
                self._ensure_dont_have_later_approved_final_result(
                    promise, result.date, self.CANNOT_EVALUATE_FINAL_BECAUSE_LATER_RESULTS
                )

        result.review_status = new_status
        result.review_date = timezone.now()
        result.reviewer = self.performed_by

        result = self.base_service.edit_base(result, self.performed_by)

        logger.info(f"Evaluated promise result: {result.id} -> {result.review_status}")

        return result
