from datetime import date
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from loguru import logger
from rolepermissions.checkers import has_role

from promise_tracker.classifiers.models import Convocation, PoliticalParty
from promise_tracker.common.services import BaseService
from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.common.wrappers import handle_unique_error
from promise_tracker.core.exceptions import ApplicationError, PermissionViolationError
from promise_tracker.core.roles import Administrator
from promise_tracker.promises.models import Promise, PromiseResult
from promise_tracker.users.models import BaseUser


class PromiseService:
    def __init__(self, performed_by: BaseUser, base_service: BaseService[Promise] | None = None) -> None:
        self.performed_by = performed_by
        self.base_service: BaseService[Promise] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("Promise not found.")

    PARTY_NOT_FOUND = _("Political party does not exist!")
    CONVOCATION_NOT_FOUND = _("Convocation does not exist!")
    UNIQUE_CONSTRAINT_MESSAGE = _("Promise {name} already exists!")
    CANNOT_EDIT_REVIEWED = _("Cannot modify reviewed promise!")
    CANNOT_DELETE_REVIEWED = _("Cannot delete reviewed promise!")
    CANNOT_EVALUATE_REVIEWED = _("Cannot evaluate already reviewed promise!")
    CANNOT_DELETE_HAS_RESULTS = _("Cannot delete promise because it has reviewed results!")
    STATUSES_ARE_SAME = _("Promise is already in status {status}!")
    DATE_IN_FUTURE = _("Promise date is in the future.")
    ESTABLISHED_DATE_LATER_THAN_PROMISE = _("Party {name} established date is later than the promise date.")
    LIQIDATED_DATE_EARLIER_THAN_PROMISE = _("Party {name} liquidated date is earlier than the promise date.")
    PARTY_NOT_ELECTED_IN_CONVOCATION = _("Party {name} is not elected in convocation {convocation}.")

    def _ensure_elected_in_convocation(self, convocation: Convocation, party: PoliticalParty | None) -> None:
        if party is not None:
            if not convocation.political_parties.filter(id=party.id).exists():
                raise ApplicationError(
                    self.PARTY_NOT_ELECTED_IN_CONVOCATION.format(name=party.name, convocation=convocation.name)
                )

    def _ensure_doesnt_have_results(self, promise: Promise) -> None:
        if promise.results.exclude(review_status=PromiseResult.ReviewStatus.PENDING).exists():
            raise ApplicationError(self.CANNOT_DELETE_HAS_RESULTS)

    def _ensure_is_not_reviewed(self, promise: Promise, message: str) -> None:
        if promise.is_reviewed:
            raise ApplicationError(message)

    def _ensure_status_is_different(self, promise: Promise, new_status: Promise.ReviewStatus) -> None:
        if promise.review_status == new_status:
            raise ApplicationError(self.STATUSES_ARE_SAME.format(status=new_status))

    def _ensure_is_owner_or_admin(self, promise: Promise) -> None:
        if not has_role(self.performed_by, Administrator):
            if promise.created_by is None or self.performed_by.id != promise.created_by.id:
                logger.error(f"User {self.performed_by.id} attempted to edit promise {promise.id} without permission.")
                raise PermissionViolationError()

    def _ensure_date_is_valid(self, date: date) -> None:
        if date > timezone.now().date():
            raise ApplicationError(self.DATE_IN_FUTURE)

    def _ensure_party_dates_are_valid(self, date: date, party: PoliticalParty | None) -> None:
        if party:
            if party.established_date and party.established_date > date:
                raise ApplicationError(self.ESTABLISHED_DATE_LATER_THAN_PROMISE.format(name=party.name))
            if party.liquidated_date and party.liquidated_date <= date:
                raise ApplicationError(self.LIQIDATED_DATE_EARLIER_THAN_PROMISE.format(name=party.name))

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def create_promise(
        self,
        name: str,
        description: str,
        sources: list[str],
        date: date,
        party_id: UUID,
        convocation_id: UUID,
    ) -> Promise:
        logger.debug(f"Creating promise with name: {name}")

        self._ensure_date_is_valid(date)

        party = get_object_or_raise(PoliticalParty, self.PARTY_NOT_FOUND, id=party_id)
        convocation = get_object_or_raise(Convocation, self.CONVOCATION_NOT_FOUND, id=convocation_id)

        self._ensure_elected_in_convocation(convocation, party)
        self._ensure_party_dates_are_valid(date, party)

        promise = Promise(
            name=name,
            description=description,
            sources=sources,
            date=date,
            party=party,
            convocation=convocation,
        )

        promise = self.base_service.create_base(promise, self.performed_by)

        logger.info(f"Created promise: {promise.name} (ID: {promise.id})")

        return promise

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def edit_promise(
        self,
        id: UUID,
        name: str,
        description: str,
        sources: list[str],
        date: date,
        convocation_id: UUID,
        party_id: UUID,
    ) -> Promise:
        promise = get_object_or_raise(Promise, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_is_owner_or_admin(promise)
        self._ensure_is_not_reviewed(promise, self.CANNOT_EDIT_REVIEWED)
        self._ensure_date_is_valid(date)

        party = get_object_or_raise(PoliticalParty, self.PARTY_NOT_FOUND, id=party_id)
        convocation = get_object_or_raise(Convocation, self.CONVOCATION_NOT_FOUND, id=convocation_id)

        self._ensure_elected_in_convocation(convocation, party)
        self._ensure_party_dates_are_valid(date, party)

        promise.name = name
        promise.description = description
        promise.sources = sources
        promise.date = date
        promise.party = party
        promise.convocation = convocation

        promise = self.base_service.edit_base(promise, self.performed_by)

        logger.info(f"Edited promise: {promise.id}")

        return promise

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def delete_promise(self, id: UUID) -> None:
        promise = get_object_or_raise(Promise, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_is_owner_or_admin(promise)
        self._ensure_is_not_reviewed(promise, self.CANNOT_DELETE_REVIEWED)
        self._ensure_doesnt_have_results(promise)

        logger.debug(f"Deleting promise: {promise.id}")

        self.base_service.delete_base(promise)

        logger.info(f"Deleted promise: {promise.id}")

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def evaluate_promise(self, id: UUID, new_status: Promise.ReviewStatus) -> Promise:
        promise = get_object_or_raise(Promise, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_is_not_reviewed(promise, self.CANNOT_EVALUATE_REVIEWED)
        self._ensure_status_is_different(promise, new_status)

        promise.review_status = new_status
        promise.review_date = timezone.now()
        promise.reviewer = self.performed_by

        promise = self.base_service.edit_base(promise, self.performed_by)

        logger.info(f"Evaluated promise: {promise.id} -> {promise.review_status}")

        return promise
