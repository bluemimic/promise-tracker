from uuid import UUID

from django.db.models import QuerySet
from django.utils.translation import gettext as _
from django_filters import FilterSet

from promise_tracker.classifiers.models import LegislativeInstitution
from promise_tracker.common.utils import get_object_or_none
from promise_tracker.core.exceptions import NotFoundError


NOT_FOUND_MESSAGE = _("Legislative institution not found.")


class LegislativeInstitutionFilerSet(FilterSet):
    class Meta:
        model = LegislativeInstitution
        fields = {
            "name": ["iexact", "icontains"],
            "institution_type": ["exact", "in"],
            "institution_level": ["exact", "in"],
        }


def get_legislative_institutions(self, filters: dict | None = None) -> QuerySet[LegislativeInstitution]:
    filters = filters or {}

    qs = LegislativeInstitution.objects.all()

    return LegislativeInstitutionFilerSet(filters, queryset=qs).qs


def get_legislative_institution_by_id(self, id: UUID) -> LegislativeInstitution:
    legislative_institution = get_object_or_none(LegislativeInstitution, id=id)

    if legislative_institution is None:
        raise NotFoundError(NOT_FOUND_MESSAGE)

    return legislative_institution
