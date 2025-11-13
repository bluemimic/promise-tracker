from uuid import UUID

from django.db.models import QuerySet
from django.utils.translation import gettext as _
from django_filters import FilterSet

from promise_tracker.classifiers.models import Convocation
from promise_tracker.common.utils import get_object_or_none
from promise_tracker.core.exceptions import NotFoundError

NOT_FOUND_MESSAGE = _("Convocation not found.")


class ConvocationFilterSet(FilterSet):
    class Meta:
        model = Convocation
        fields = {
            "name": ["iexact", "icontains"],
            "political_parties": ["in"],
            "political_unions": ["in"],
            "legislative_institution": ["exact"],
        }


def get_convocations(filters: dict | None = None) -> QuerySet[Convocation]:
    filters = filters or {}

    qs = Convocation.objects.all()

    return ConvocationFilterSet(filters, queryset=qs).qs


def get_convocation_by_id(id: UUID) -> Convocation:
    convocation = get_object_or_none(Convocation, id=id)

    if convocation is None:
        raise NotFoundError(NOT_FOUND_MESSAGE)

    return convocation
