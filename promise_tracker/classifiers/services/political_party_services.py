from datetime import datetime
from uuid import UUID

from django.core.files import File
from django.db import IntegrityError, transaction
from django.utils.translation import gettext as _
from loguru import logger

from promise_tracker.classifiers.models import PoliticalParty
from promise_tracker.common.services import BaseService
from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.core.exceptions import ApplicationError
from promise_tracker.users.models import BaseUser


class oliticalPartyService:
    def __init__(
        self,
        performed_by: BaseUser,
        base_service: BaseService[PoliticalParty] | None = None,
    ) -> None:
        self.performed_by = performed_by
        self.base_service: BaseService[PoliticalParty] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("Political party not found.")
    UNIQUE_CONSTRAINT_MESSAGE = _("A political party {name} already exists.")
    CANNOT_DELETE_PARTICIPATES_IN_UNIONS = _("Cannot delete political party because it participates in unions!")
    CANNOT_DELETE_ELECTED_IN_CONVOCATIONS = _("Cannot delete political party because it has been elected in convocations!")
    CANNOT_DELETE_HAS_ASSOCIATED_PROMISES = _("Cannot delete political party because it has associated promises!")

    def _ensure_doesnt_participate_in_unions(self, political_party: PoliticalParty) -> None:
        if political_party.unions.exists():
            raise ApplicationError(self.CANNOT_DELETE_PARTICIPATES_IN_UNIONS)

    def _ensure_has_not_been_elected(self, political_party: PoliticalParty) -> None:
        if political_party.convocations.exists():
            raise ApplicationError(self.CANNOT_DELETE_ELECTED_IN_CONVOCATIONS)

    def _ensure_doesnt_have_promises(self, political_party: PoliticalParty) -> None:
        if political_party.promises.exists():
            raise ApplicationError(self.CANNOT_DELETE_HAS_ASSOCIATED_PROMISES)

    @transaction.atomic
    def create_political_party(
        self,
        name: str,
        email: str,
        established_date: datetime,
        liquidated_date: datetime | None = None,
        ideologies: list[str] | None = None,
        logo: File | None = None,
    ) -> PoliticalParty:
        logger.debug(f"Creating political party with name: {name}")

        political_party = PoliticalParty(
            name=name,
            email=email,
            established_date=established_date,
            liquidated_date=liquidated_date,
            ideologies=ideologies or [],
            logo=logo,
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
        email: str,
        established_date: datetime,
        liquidated_date: datetime | None = None,
        ideologies: list[str] | None = None,
        logo: File | None = None,
    ) -> PoliticalParty:
        political_party = get_object_or_raise(PoliticalParty, self.NOT_FOUND_MESSAGE, id=id)

        logger.debug(f"Editing political party: {political_party.id}")

        political_party.name = name
        political_party.email = email
        political_party.established_date = established_date
        political_party.liquidated_date = liquidated_date

        if ideologies is not None:
            political_party.ideologies = ideologies

        if logo is not None:
            political_party.logo = logo

        try:
            political_party = self.base_service.edit_base(political_party, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        logger.info(f"Edited political party: {political_party.id}")

        return political_party

    @transaction.atomic
    def delete_political_party(self, id: UUID) -> None:
        political_party = get_object_or_raise(PoliticalParty, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_doesnt_participate_in_unions(political_party)
        self._ensure_has_not_been_elected(political_party)
        self._ensure_doesnt_have_promises(political_party)

        logger.debug(f"Deleting political party: {political_party.id}")

        self.base_service.delete_base(political_party)

        logger.info(f"Deleted political party: {political_party.id}")
