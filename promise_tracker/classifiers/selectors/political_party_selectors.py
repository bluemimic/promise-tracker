from uuid import UUID

from django.db.models import QuerySet
from django.utils.translation import gettext as _
from django_filters import FilterSet

from promise_tracker.classifiers.models import PoliticalParty
from promise_tracker.common.utils import get_object_or_none
from promise_tracker.core.exceptions import NotFoundError


NOT_FOUND_MESSAGE = _("Political party not found.")


class PoliticalPartyFilerSet(FilterSet):
    class Meta:
        model = PoliticalParty
        fields = {
            "name": ["iexact", "icontains"],

            "is_active": ["exact"],
            "ideologies": ["icontains"],
        }


def get_political_parties(self, filters: dict | None = None) -> QuerySet[PoliticalParty]:
    filters = filters or {}

    qs = PoliticalParty.objects.all()

    return PoliticalPartyFilerSet(filters, queryset=qs).qs


def get_political_party_by_id(self, id: UUID) -> PoliticalParty:
    political_party = get_object_or_none(PoliticalParty, id=id)

    if political_party is None:
        raise NotFoundError(NOT_FOUND_MESSAGE)

    return political_party
