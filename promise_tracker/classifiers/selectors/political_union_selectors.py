from uuid import UUID

from django.db.models import QuerySet
from django.utils.translation import gettext as _
from django_filters import FilterSet

from promise_tracker.classifiers.models import PoliticalUnion
from promise_tracker.common.utils import get_object_or_none
from promise_tracker.core.exceptions import NotFoundError

NOT_FOUND_MESSAGE = _("Political union not found.")


class PoliticalUnionFitlerSet(FilterSet):
    class Meta:
        model = PoliticalUnion
        fields = {
            "name": ["iexact", "icontains"],
            "parties": ["in"],
            "is_active": ["exact"],
            "ideologies": ["icontains"],
        }


def get_political_unions(filters: dict | None = None) -> QuerySet[PoliticalUnion]:
    filters = filters or {}

    qs = PoliticalUnion.objects.all()

    return PoliticalUnionFitlerSet(filters, queryset=qs).qs


def get_political_union_by_id(id: UUID) -> PoliticalUnion:
    political_union = get_object_or_none(PoliticalUnion, id=id)

    if political_union is None:
        raise NotFoundError(NOT_FOUND_MESSAGE)

    return political_union
