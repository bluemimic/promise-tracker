from uuid import UUID

from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _
from django_filters import BooleanFilter, FilterSet, ModelMultipleChoiceFilter, MultipleChoiceFilter

from promise_tracker.classifiers.models import PoliticalParty, PoliticalUnion
from promise_tracker.common.utils import get_object_or_none
from promise_tracker.common.widgets import BootstrapCheckboxSelectMultiple
from promise_tracker.core.exceptions import NotFoundError

NOT_FOUND_MESSAGE = _("Political union not found.")


class PoliticalUnionFitlerSet(FilterSet):
    is_active = BooleanFilter(method="filter_is_active", label=_("Is Active"))
    ideologies = MultipleChoiceFilter(
        choices=PoliticalUnion.Ideologies, widget=BootstrapCheckboxSelectMultiple(), method="filter_ideologies"
    )
    parties = ModelMultipleChoiceFilter(
        field_name="parties__id", queryset=PoliticalParty.objects.all(), label=_("Parties"), method="filter_parties"
    )

    class Meta:
        model = PoliticalUnion
        fields = {
            "name": ["icontains"],
        }

    def filter_is_active(self, queryset, name, value):
        if value:
            queryset = queryset.filter(Q(liquidated_date__isnull=True))
        else:
            queryset = queryset.filter(Q(liquidated_date__isnull=False) | Q(liquidated_date__lte=timezone.now()))

        return queryset

    def filter_ideologies(self, queryset, name, value):
        if not value:
            return queryset

        if isinstance(value, str):
            value = [value]

        wanted = set(value)
        ids = []

        for obj in queryset:
            if set(obj.ideologies) & wanted:
                ids.append(obj.pk)

        return queryset.filter(pk__in=ids)

    def filter_parties(self, queryset, name, value):
        if value:
            return queryset.filter(parties__in=value).distinct()
        return queryset


def get_political_unions(filters: dict | None = None) -> QuerySet[PoliticalUnion]:
    filters = filters or {}

    qs = PoliticalUnion.objects.all()

    return PoliticalUnionFitlerSet(data=filters, queryset=qs).qs


def get_political_union_by_id(id: UUID) -> PoliticalUnion:
    political_union = get_object_or_none(PoliticalUnion, id=id)

    if political_union is None:
        raise NotFoundError(NOT_FOUND_MESSAGE)

    return political_union
