from datetime import date
from uuid import UUID

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from loguru import logger

from promise_tracker.classifiers.models import (
    Convocation,
    PoliticalParty,
)
from promise_tracker.common.services import BaseService
from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.core.exceptions import ApplicationError
from promise_tracker.users.models import BaseUser


class ConvocationService:
    def __init__(
        self,
        performed_by: BaseUser,
        base_service: BaseService[Convocation] | None = None,
    ) -> None:
        self.performed_by = performed_by
        self.base_service: BaseService[Convocation] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("Convocation not found.")

    PARTIES_LIST_INVALID = _("Political parties list is not valid!")
    PARTY_LIQUIDATED_BEFORE_START = _("Party {party_name} liquidated date is smaller than convocation start date!")
    PARTY_ESTABLISHED_AFTER_END = _("Party {party_name} established date is greater than convocation end date!")
    UNIQUE_CONSTRAINT_MESSAGE = _("Convocation {name} already exists!")
    CANNOT_DELETE_HAS_ASSOCIATED_PROMISES = _("Cannot delete convocation because it has associated promises!")
    END_DATE_IN_FUTURE = _("End date is in the future.")
    START_DATE_IN_FUTURE = _("Start date is in the future.")
    END_DATE_SMALLER_THAN_START = _("End date is smaller than start date.")

    def _fetch_parties(self, party_ids: list[UUID] | None) -> list[PoliticalParty]:
        if party_ids is None:
            return []

        non_empty_ids = [pid for pid in party_ids if pid is not None]

        if len(non_empty_ids) != len(set(non_empty_ids)):
            raise ApplicationError(self.PARTIES_LIST_INVALID)

        parties_qs = PoliticalParty.objects.filter(id__in=party_ids)
        parties = list(parties_qs)

        if len(parties) != len(set(party_ids)):
            raise ApplicationError(self.PARTIES_LIST_INVALID)

        return parties

    def _check_date_constraints(self, parties: list[PoliticalParty], start_date: date, end_date: date | None) -> None:
        for party in parties:
            if party.liquidated_date is not None and party.liquidated_date < start_date:
                raise ApplicationError(self.PARTY_LIQUIDATED_BEFORE_START.format(party_name=party.name))

            if end_date is not None and party.established_date is not None and party.established_date > end_date:
                raise ApplicationError(self.PARTY_ESTABLISHED_AFTER_END.format(party_name=party.name))

    def _ensure_has_no_promises(self, convocation: Convocation) -> None:
        if convocation.promises.exists():
            raise ApplicationError(self.CANNOT_DELETE_HAS_ASSOCIATED_PROMISES)

    def _ensure_dates_are_valid(self, start_date: date, end_date: date | None) -> None:
        today = timezone.now().date()

        if start_date > today:
            raise ApplicationError(self.START_DATE_IN_FUTURE)

        if end_date is not None and end_date > today:
            raise ApplicationError(self.END_DATE_IN_FUTURE)

        if end_date is not None and end_date < start_date:
            raise ApplicationError(self.END_DATE_SMALLER_THAN_START)

    @transaction.atomic
    def create_convocation(
        self,
        name: str,
        start_date: date,
        party_ids: list[UUID],
        end_date: date | None = None,
    ) -> Convocation:
        logger.debug(f"Creating convocation with name: {name}")

        self._ensure_dates_are_valid(start_date, end_date)

        parties = self._fetch_parties(party_ids)

        self._check_date_constraints(parties, start_date, end_date)

        convocation = Convocation(
            name=name,
            start_date=start_date,
            end_date=end_date,
        )

        try:
            convocation = self.base_service.create_base(convocation, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        if parties:
            convocation.political_parties.set(parties)

        logger.info(f"Created convocation: {convocation.name} (ID: {convocation.id})")

        return convocation

    @transaction.atomic
    def edit_convocation(
        self,
        id: UUID,
        name: str,
        start_date: date,
        party_ids: list[UUID],
        end_date: date | None = None,
    ) -> Convocation:
        convocation = get_object_or_raise(Convocation, self.NOT_FOUND_MESSAGE, id=id)

        logger.debug(f"Editing convocation: {convocation.id}")

        self._ensure_dates_are_valid(start_date, end_date)

        parties = self._fetch_parties(party_ids)

        self._check_date_constraints(parties, start_date, end_date)

        convocation.name = name
        convocation.start_date = start_date
        convocation.end_date = end_date

        try:
            convocation = self.base_service.edit_base(convocation, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        convocation.political_parties.set(parties)

        logger.info(f"Edited convocation: {convocation.id}")

        return convocation

    @transaction.atomic
    def delete_convocation(self, id: UUID) -> None:
        convocation = get_object_or_raise(Convocation, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_has_no_promises(convocation)

        logger.debug(f"Deleting convocation: {convocation.id}")

        self.base_service.delete_base(convocation)

        logger.info(f"Deleted convocation: {convocation.id}")
