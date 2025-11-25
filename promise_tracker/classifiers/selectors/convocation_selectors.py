from uuid import UUID

from django.db.models import QuerySet
from django.utils.translation import gettext as _
from django_filters import FilterSet, ModelMultipleChoiceFilter

from promise_tracker.classifiers.models import Convocation, PoliticalParty, PoliticalUnion
from promise_tracker.common.utils import get_object_or_none
from promise_tracker.core.exceptions import NotFoundError

NOT_FOUND_MESSAGE = _("Convocation not found.")


class ConvocationFilterSet(FilterSet):
    parties = ModelMultipleChoiceFilter(
        field_name="political_parties__id",
        queryset=PoliticalParty.objects.all(),
        label=_("Parties"),
        method="filter_parties",
    )
    unions = ModelMultipleChoiceFilter(
        field_name="political_unions__id",
        queryset=PoliticalUnion.objects.all(),
        label=_("Unions"),
        method="filter_unions",
    )

    def filter_parties(self, queryset, name, value):
        if value:
            return queryset.filter(political_parties__in=value).distinct()
        return queryset

    def filter_unions(self, queryset, name, value):
        if value:
            return queryset.filter(political_unions__in=value).distinct()
        return queryset

    class Meta:
        model = Convocation
        fields = {
            "name": ["icontains"],
            "legislative_institution": ["exact"],
        }


def get_convocations(filters: dict | None = None) -> QuerySet[Convocation]:
    filters = filters or {}

    qs = Convocation.objects.all()

    return ConvocationFilterSet(filters, queryset=qs).qs.order_by("-created_at")


def get_convocation_by_id(id: UUID) -> Convocation:
    convocation = get_object_or_none(Convocation, id=id)

    if convocation is None:
        raise NotFoundError(NOT_FOUND_MESSAGE)

    return convocation
