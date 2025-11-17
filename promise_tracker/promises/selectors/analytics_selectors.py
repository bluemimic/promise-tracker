from dataclasses import dataclass
from uuid import UUID

import django_filters
from django.db.models import Count, Q, QuerySet
from django.utils.translation import gettext_lazy as _

from promise_tracker.classifiers.models import PoliticalParty
from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.promises.models import Promise, PromiseResult


@dataclass
class AnalyticsRecord:
    name: str
    id: UUID
    completed_count: int
    uncompleted_count: int


class AnalyticsFilterSet(django_filters.FilterSet):
    party = django_filters.ModelChoiceFilter(
        queryset=PoliticalParty.objects.all(),
        required=False,
        label=_("Political Party"),
        help_text=_("Filter results by political party."),
        method="filter_by_party",
    )

    def filter_by_party(
        self, queryset: QuerySet[PromiseResult], name: str, value: PoliticalParty
    ) -> QuerySet[PromiseResult]:
        if value:
            return queryset.filter(promise__party=value)
        return queryset

    class Meta:
        model = PromiseResult
        fields = []


class AnalyticsSelectors:
    FIELD_INVALID = _("Field {field} is invalid!")
    PARTY_NOT_FOUND = _("Party does not exist!")

    def _get_all_final_approved_results(self) -> QuerySet[PromiseResult]:
        return PromiseResult.objects.filter(
            is_final=True,
            review_status=PromiseResult.ReviewStatus.APPROVED,
            promise__review_status=Promise.ReviewStatus.APPROVED,
        )

    def _generate_analytics_for_party(
        self, party: PoliticalParty, qs: QuerySet[PromiseResult]
    ) -> list[AnalyticsRecord]:
        analytics: list[AnalyticsRecord] = []

        if qs.count() == 0:
            return analytics

        party_agg = qs.aggregate(
            completed=Count("id", filter=Q(status=PromiseResult.CompletionStatus.COMPLETED)),
            uncompleted=Count("id", filter=Q(status=PromiseResult.CompletionStatus.ABANDONED)),
        )

        analytics.append(
            AnalyticsRecord(
                name=party.name,
                id=party.id,
                completed_count=party_agg.get("completed") or 0,
                uncompleted_count=party_agg.get("uncompleted") or 0,
            )
        )

        return analytics

    def _generate_general_analytics(self, qs: QuerySet[PromiseResult]) -> list[AnalyticsRecord]:
        analytics: list[AnalyticsRecord] = []

        party_groups = (
            qs.filter(promise__party__isnull=False)
            .values("promise__party__id", "promise__party__name")
            .annotate(
                completed=Count("id", filter=Q(status=PromiseResult.CompletionStatus.COMPLETED)),
                uncompleted=Count("id", filter=Q(status=PromiseResult.CompletionStatus.ABANDONED)),
            )
        )

        for group in party_groups:
            analytics.append(
                AnalyticsRecord(
                    name=group["promise__party__name"],
                    id=group["promise__party__id"],
                    completed_count=group.get("completed") or 0,
                    uncompleted_count=group.get("uncompleted") or 0,
                )
            )

        return analytics

    def get_analytics(self, filters: dict) -> list[AnalyticsRecord]:
        party_id = filters.get("party")

        promises_qs = self._get_all_final_approved_results()
        promises_qs = AnalyticsFilterSet(filters, queryset=promises_qs).qs

        if party_id is not None and party_id != "":
            party = get_object_or_raise(PoliticalParty, self.PARTY_NOT_FOUND, id=party_id)
            return self._generate_analytics_for_party(party, promises_qs)

        return self._generate_general_analytics(promises_qs)
