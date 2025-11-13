from datetime import date, datetime
from uuid import UUID

from django.core.files import File
from django.db import IntegrityError, transaction
from django.utils.translation import gettext as _
from loguru import logger

from promise_tracker.classifiers.models import PoliticalParty, PoliticalUnion
from promise_tracker.common.services import BaseService
from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.core.exceptions import ApplicationError
from promise_tracker.users.models import BaseUser


class PoliticalUnionService:
    def __init__(
        self,
        performed_by: BaseUser,
        base_service: BaseService[PoliticalUnion] | None = None,
    ) -> None:
        self.performed_by = performed_by
        self.base_service: BaseService[PoliticalUnion] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("Political union not found.")

    PARTIES_LIST_INVALID = _("Political parties list is not valid!")
    PARTIES_TOO_FEW = _("At least two political parties are required!")
    PARTY_LIQUIDATED_BEFORE_UNION = _("Party {party_name} liquidated date is smaller than union established date!")
    PARTY_ESTABLISHED_AFTER_UNION_LIQUIDATED = _(
        "Party {party_name} established date is greater than union liquidated date!"
    )
    UNIQUE_CONSTRAINT_MESSAGE = _("Political union {name} already exists!")
    CANNOT_DELETE_INCLUDED_IN_CONVOCATION = _("Cannot delete political union because it was included in a convocation!")
    CANNOT_DELETE_HAS_ASSOCIATED_PROMISES = _("Cannot delete political union because it has associated promises!")

    def _fetch_parties(self, party_ids: list[UUID]) -> list[PoliticalParty]:
        parties_qs = PoliticalParty.objects.filter(id__in=party_ids)
        parties = list(parties_qs)

        if len(parties) != len(set(party_ids)):
            raise ApplicationError(self.PARTIES_LIST_INVALID)

        if len(parties) < 2:
            raise ApplicationError(self.PARTIES_TOO_FEW)

        return parties

    def _check_party_date_constraints(
        self, parties: list[PoliticalParty], established_date: date, liquidated_date: date | None
    ):
        for party in parties:
            if party.liquidated_date is not None and party.liquidated_date < established_date:
                raise ApplicationError(self.PARTY_LIQUIDATED_BEFORE_UNION.format(party_name=party.name))

            if liquidated_date is not None and party.established_date > liquidated_date:
                raise ApplicationError(self.PARTY_ESTABLISHED_AFTER_UNION_LIQUIDATED.format(party_name=party.name))

    def _ensure_not_in_convocations(self, political_union: PoliticalUnion) -> None:
        if political_union.convocations.exists():
            raise ApplicationError(self.CANNOT_DELETE_INCLUDED_IN_CONVOCATION)

    def _ensure_has_no_promises(self, political_union: PoliticalUnion) -> None:
        if political_union.promises.exists():
            raise ApplicationError(self.CANNOT_DELETE_HAS_ASSOCIATED_PROMISES)

    @transaction.atomic
    def create_political_union(
        self,
        name: str,
        email: str,
        party_ids: list[UUID],
        established_date: datetime,
        liquidated_date: datetime | None = None,
        ideologies: list[str] | None = None,
        logo: File | None = None,
    ) -> PoliticalUnion:
        logger.debug(f"Creating political union with name: {name}")

        parties = self._fetch_parties(party_ids)
        self._check_party_date_constraints(parties, established_date, liquidated_date)

        political_union = PoliticalUnion(
            name=name,
            email=email,
            established_date=established_date,
            liquidated_date=liquidated_date,
            ideologies=ideologies or [],
        )

        if logo is not None:
            political_union.logo = logo

        try:
            political_union = self.base_service.create_base(political_union, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        political_union.parties.set(parties)

        logger.info(f"Created political union: {political_union.name} (ID: {political_union.id})")

        return political_union

    @transaction.atomic
    def edit_political_union(
        self,
        id: UUID,
        name: str,
        email: str,
        party_ids: list[UUID],
        established_date: datetime,
        liquidated_date: datetime | None = None,
        ideologies: list[str] | None = None,
        logo: File | None = None,
    ) -> PoliticalUnion:
        political_union = get_object_or_raise(PoliticalUnion, self.NOT_FOUND_MESSAGE, id=id)

        logger.debug(f"Editing political union: {political_union.id}")

        parties = self._fetch_parties(party_ids)
        self._check_party_date_constraints(parties, established_date, liquidated_date)

        political_union.name = name
        political_union.email = email
        political_union.established_date = established_date
        political_union.liquidated_date = liquidated_date

        if ideologies is not None:
            political_union.ideologies = ideologies

        if logo is not None:
            political_union.logo = logo

        try:
            political_union = self.base_service.edit_base(political_union, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        political_union.parties.set(parties)

        logger.info(f"Edited political union: {political_union.id}")

        return political_union

    @transaction.atomic
    def delete_political_union(self, id: UUID) -> None:
        political_union = get_object_or_raise(PoliticalUnion, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_not_in_convocations(political_union)
        self._ensure_has_no_promises(political_union)

        logger.debug(f"Deleting political union: {political_union.id}")

        self.base_service.delete_base(political_union)

        logger.info(f"Deleted political union: {political_union.id}")
