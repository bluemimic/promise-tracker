from uuid import UUID

from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _
from django_filters import BooleanFilter, FilterSet, MultipleChoiceFilter

from promise_tracker.classifiers.models import PoliticalParty
from promise_tracker.common.utils import get_object_or_none
from promise_tracker.common.widgets import (
    BootstrapCheckboxSelectMultiple,
)
from promise_tracker.core.exceptions import NotFoundError

NOT_FOUND_MESSAGE = _("Political party not found.")


class PoliticalPartyFilerSet(FilterSet):
    is_active = BooleanFilter(method="filter_is_active", label=_("Is Active"))
    ideologies = MultipleChoiceFilter(
        choices=PoliticalParty.Ideologies, widget=BootstrapCheckboxSelectMultiple(), method="filter_ideologies"
    )

    class Meta:
        model = PoliticalParty
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


def get_political_parties(filters: dict | None = None) -> QuerySet[PoliticalParty]:
    filters = filters or {}

    qs = PoliticalParty.objects.all()

    return PoliticalPartyFilerSet(data=filters, queryset=qs).qs


def get_political_party_by_id(id: UUID) -> PoliticalParty:
    political_party = get_object_or_none(PoliticalParty, id=id)

    if political_party is None:
        raise NotFoundError(NOT_FOUND_MESSAGE)

    return political_party
