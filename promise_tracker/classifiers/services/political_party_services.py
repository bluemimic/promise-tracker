from datetime import date
from uuid import UUID

from django.core.files import File
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from loguru import logger

from promise_tracker.classifiers.models import PoliticalParty
from promise_tracker.common.services import BaseService
from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.core.exceptions import ApplicationError
from promise_tracker.users.models import BaseUser


class PoliticalPartyService:
    def __init__(
        self,
        performed_by: BaseUser,
        base_service: BaseService[PoliticalParty] | None = None,
    ) -> None:
        self.performed_by = performed_by
        self.base_service: BaseService[PoliticalParty] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("Political party not found.")
    UNIQUE_CONSTRAINT_MESSAGE = _("A political party {name} already exists.")
    CANNOT_DELETE_ELECTED_IN_CONVOCATIONS = _(
        "Cannot delete political party because it has been elected in convocations!"
    )
    CANNOT_DELETE_HAS_ASSOCIATED_PROMISES = _("Cannot delete political party because it has associated promises!")
    LIQUIDATED_DATE_IN_FUTURE = _("Liquidated date is in the future.")
    ESTABLISHED_DATE_IN_FUTURE = _("Established date is in the future.")
    LIQUIDATED_DATE_SMALLER_THAN_ESTABLISHED_DATE = _("Liquidated date is smaller than established date.")

    def _ensure_has_not_been_elected(self, political_party: PoliticalParty) -> None:
        if political_party.convocations.exists():
            raise ApplicationError(self.CANNOT_DELETE_ELECTED_IN_CONVOCATIONS)

    def _ensure_doesnt_have_promises(self, political_party: PoliticalParty) -> None:
        if political_party.promises.exists():
            raise ApplicationError(self.CANNOT_DELETE_HAS_ASSOCIATED_PROMISES)

    def _ensure_dates_are_valid(
        self,
        established_date: date,
        liquidated_date: date | None = None,
    ) -> None:
        now = timezone.now().date()

        if established_date > now:
            raise ApplicationError(self.ESTABLISHED_DATE_IN_FUTURE)

        if liquidated_date and liquidated_date > now:
            raise ApplicationError(self.LIQUIDATED_DATE_IN_FUTURE)

        if liquidated_date and liquidated_date < established_date:
            raise ApplicationError(self.LIQUIDATED_DATE_SMALLER_THAN_ESTABLISHED_DATE)

    @transaction.atomic
    def create_political_party(
        self,
        name: str,
        established_date: date,
        liquidated_date: date | None = None,
    ) -> PoliticalParty:
        logger.debug(f"Creating political party with name: {name}")

        self._ensure_dates_are_valid(established_date, liquidated_date)

        political_party = PoliticalParty(
            name=name,
            established_date=established_date,
            liquidated_date=liquidated_date,
        )

        try:
            political_party = self.base_service.create_base(political_party, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        logger.info(f"Created political party: {political_party.name} (ID: {political_party.id})")

        return political_party

    @transaction.atomic
    def edit_political_party(
        self,
        id: UUID,
        name: str,
        established_date: date,
        liquidated_date: date | None = None,
    ) -> PoliticalParty:
        political_party = get_object_or_raise(PoliticalParty, self.NOT_FOUND_MESSAGE, id=id)

        logger.debug(f"Editing political party: {political_party.id}")

        self._ensure_dates_are_valid(established_date, liquidated_date)

        political_party.name = name
        political_party.established_date = established_date
        political_party.liquidated_date = liquidated_date

        try:
            political_party = self.base_service.edit_base(political_party, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        logger.info(f"Edited political party: {political_party.id}")

        return political_party

    @transaction.atomic
    def delete_political_party(self, id: UUID) -> None:
        political_party = get_object_or_raise(PoliticalParty, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_has_not_been_elected(political_party)
        self._ensure_doesnt_have_promises(political_party)

        logger.debug(f"Deleting political party: {political_party.id}")

        self.base_service.delete_base(political_party)

        logger.info(f"Deleted political party: {political_party.id}")
