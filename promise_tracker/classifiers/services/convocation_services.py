from datetime import date, datetime
from uuid import UUID

from django.db import IntegrityError, transaction
from django.utils.translation import gettext as _
from loguru import logger

from promise_tracker.classifiers.models import (
    Convocation,
    LegislativeInstitution,
    PoliticalParty,
    PoliticalUnion,
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

    NO_PARTY_OR_UNION = _("No party or union specified!")
    PARTIES_LIST_INVALID = _("Political parties list is not valid!")
    UNIONS_LIST_INVALID = _("Political unions list is not valid!")
    LEGISLATIVE_INSTITUTION_INVALID = _("Legislative institution is not valid!")
    PARTY_LIQUIDATED_BEFORE_START = _("Party {party_name} liquidated date is smaller than convocation start date!")
    PARTY_ESTABLISHED_AFTER_END = _("Party {party_name} established date is greater than convocation end date!")
    UNION_LIQUIDATED_BEFORE_START = _("Union {union_name} liquidated date is smaller than convocation start date!")
    UNION_ESTABLISHED_AFTER_END = _("Union {union_name} established date is greater than convocation end date!")
    PARTY_ALREADY_IN_UNION = _("Party {party_name} is already included from union {union_name}!")
    UNIQUE_CONSTRAINT_MESSAGE = _("Convocation {name} already exists!")
    CANNOT_DELETE_HAS_ASSOCIATED_PROMISES = _("Cannot delete convocation because it has associated promises!")

    def _fetch_parties(self, party_ids: list[UUID]) -> list[PoliticalParty]:
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

    def _fetch_unions(self, union_ids: list[UUID]) -> list[PoliticalUnion]:
        if union_ids is None:
            return []

        non_empty_ids = [uid for uid in union_ids if uid is not None]
        if len(non_empty_ids) != len(set(non_empty_ids)):
            raise ApplicationError(self.UNIONS_LIST_INVALID)

        unions_qs = PoliticalUnion.objects.filter(id__in=union_ids)
        unions = list(unions_qs)

        if len(unions) != len(set(union_ids)):
            raise ApplicationError(self.UNIONS_LIST_INVALID)

        return unions

    def _check_party_union_conflicts(self, parties: list[PoliticalParty], unions: list[PoliticalUnion]) -> None:
        parties_ids = {party.id for party in parties}

        for union in unions:
            overlapping_parties = union.parties.filter(id__in=parties_ids)
            
            if overlapping_parties.exists():
                party = overlapping_parties.first()
                raise ApplicationError(self.PARTY_ALREADY_IN_UNION.format(party_name=party.name, union_name=union.name))

    def _check_date_constraints(
        self, parties: list[PoliticalParty], unions: list[PoliticalUnion], start_date: date, end_date: date | None
    ) -> None:
        for party in parties:
            if party.liquidated_date is not None and party.liquidated_date < start_date:
                raise ApplicationError(self.PARTY_LIQUIDATED_BEFORE_START.format(party_name=party.name))

            if end_date is not None and party.established_date is not None and party.established_date > end_date:
                raise ApplicationError(self.PARTY_ESTABLISHED_AFTER_END.format(party_name=party.name))

        for union in unions:
            if union.liquidated_date is not None and union.liquidated_date < start_date:
                raise ApplicationError(self.UNION_LIQUIDATED_BEFORE_START.format(union_name=union.name))

            if end_date is not None and union.established_date is not None and union.established_date > end_date:
                raise ApplicationError(self.UNION_ESTABLISHED_AFTER_END.format(union_name=union.name))

    def _ensure_has_no_promises(self, convocation: Convocation) -> None:
        if convocation.promises.exists():
            raise ApplicationError(self.CANNOT_DELETE_HAS_ASSOCIATED_PROMISES)

    @transaction.atomic
    def create_convocation(
        self,
        name: str,
        start_date: datetime,
        end_date: datetime | None,
        legislative_institution_id: UUID,
        party_ids: list[UUID] | None = None,
        union_ids: list[UUID] | None = None,
    ) -> Convocation:
        logger.debug(f"Creating convocation with name: {name}")

        parties = self._fetch_parties(party_ids)
        unions = self._fetch_unions(union_ids)

        if not parties and not unions:
            raise ApplicationError(self.NO_PARTY_OR_UNION)

        legislative_institution = get_object_or_raise(
            LegislativeInstitution, self.LEGISLATIVE_INSTITUTION_INVALID, id=legislative_institution_id
        )

        self._check_date_constraints(parties, unions, start_date, end_date)
        self._check_party_union_conflicts(parties, unions)

        convocation = Convocation(
            name=name,
            start_date=start_date,
            end_date=end_date,
            legislative_institution=legislative_institution,
        )

        try:
            convocation = self.base_service.create_base(convocation, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        if parties:
            convocation.political_parties.set(parties)

        if unions:
            convocation.political_unions.set(unions)

        logger.info(f"Created convocation: {convocation.name} (ID: {convocation.id})")

        return convocation

    @transaction.atomic
    def edit_convocation(
        self,
        id: UUID,
        name: str,
        start_date: date,
        end_date: date | None,
        legislative_institution_id: UUID,
        party_ids: list[UUID] | None = None,
        union_ids: list[UUID] | None = None,
    ) -> Convocation:
        convocation = get_object_or_raise(Convocation, self.NOT_FOUND_MESSAGE, id=id)

        logger.debug(f"Editing convocation: {convocation.id}")

        parties = self._fetch_parties(party_ids)
        unions = self._fetch_unions(union_ids)

        if not parties and not unions:
            raise ApplicationError(self.NO_PARTY_OR_UNION)

        legislative_institution = get_object_or_raise(
            LegislativeInstitution, self.LEGISLATIVE_INSTITUTION_INVALID, id=legislative_institution_id
        )

        self._check_party_union_conflicts(parties, unions)
        self._check_date_constraints(parties, unions, start_date, end_date)

        convocation.name = name
        convocation.start_date = start_date
        convocation.end_date = end_date
        convocation.legislative_institution = legislative_institution

        try:
            convocation = self.base_service.edit_base(convocation, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        convocation.political_parties.set(parties)
        convocation.political_unions.set(unions)

        logger.info(f"Edited convocation: {convocation.id}")

        return convocation

    @transaction.atomic
    def delete_convocation(self, id: UUID) -> None:
        convocation = get_object_or_raise(Convocation, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_has_no_promises(convocation)

        logger.debug(f"Deleting convocation: {convocation.id}")

        self.base_service.delete_base(convocation)

        logger.info(f"Deleted convocation: {convocation.id}")
