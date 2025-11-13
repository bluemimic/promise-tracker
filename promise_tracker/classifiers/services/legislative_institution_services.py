from uuid import UUID

from django.core.files import File
from django.db import IntegrityError, transaction
from django.utils.translation import gettext as _
from loguru import logger

from promise_tracker.classifiers.models import LegislativeInstitution
from promise_tracker.common.services import BaseService
from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.core.exceptions import ApplicationError
from promise_tracker.users.models import BaseUser


class LegislativeInstitutionService:
    def __init__(
        self,
        performed_by: BaseUser,
        base_service: BaseService[LegislativeInstitution] | None = None,
    ) -> None:
        self.performed_by = performed_by
        self.base_service: BaseService[LegislativeInstitution] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("Legislative institution not found.")
    UNIQUE_CONSTRAINT_MESSAGE = _("A legislative institution {name} already exists.")
    CANNOT_DELETE_BECAUSE_CONVOCATIONS_EXIST = _(
        "Cannot delete legislative institution because it has associated convocations!"
    )

    def _ensure_have_no_convocations(self, legislative_institution: LegislativeInstitution) -> None:
        if legislative_institution.convocations.exists():
            raise ApplicationError(self.CANNOT_DELETE_BECAUSE_CONVOCATIONS_EXIST)

    @transaction.atomic
    def create_legislative_institution(
        self,
        name: str,
        institution_type: LegislativeInstitution.Type,
        institution_level: LegislativeInstitution.Level,
        logo: File | None = None,
    ) -> LegislativeInstitution:
        logger.debug(f"Creating legislative institution with name: {name}")

        legislative_institution = LegislativeInstitution(
            name=name,
            institution_type=institution_type,
            institution_level=institution_level,
        )

        if logo is not None:
            legislative_institution.logo = logo

        try:
            legislative_institution = self.base_service.create_base(legislative_institution, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        logger.info(
            f"Created legislative institution: {legislative_institution.name} (ID: {legislative_institution.id})"
        )

        return legislative_institution

    @transaction.atomic
    def edit_legislative_institution(
        self,
        id: UUID,
        name: str,
        institution_type: LegislativeInstitution.Type,
        institution_level: LegislativeInstitution.Level,
        logo: File | None = None,
    ) -> LegislativeInstitution:
        legislative_institution = get_object_or_raise(LegislativeInstitution, self.NOT_FOUND_MESSAGE, id=id)

        logger.debug(f"Editing legislative institution: {legislative_institution.id}")

        legislative_institution.name = name
        legislative_institution.institution_type = institution_type
        legislative_institution.institution_level = institution_level

        if logo is not None:
            legislative_institution.logo = logo

        try:
            legislative_institution = self.base_service.edit_base(legislative_institution, self.performed_by)
        except IntegrityError:
            raise ApplicationError(self.UNIQUE_CONSTRAINT_MESSAGE.format(name=name))

        logger.info(f"Edited legislative institution: {legislative_institution.id}")

        return legislative_institution

    @transaction.atomic
    def delete_legislative_institution(self, id: UUID) -> None:
        legislative_institution = get_object_or_raise(LegislativeInstitution, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_have_no_convocations(legislative_institution)

        logger.debug(f"Deleting legislative institution: {legislative_institution.id}")

        self.base_service.delete_base(legislative_institution)

        logger.info(f"Deleted legislative institution: {legislative_institution.id}")
