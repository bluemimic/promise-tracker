from dataclasses import dataclass
from enum import Enum
from uuid import UUID

import django_filters
from django.db.models import Count, Q, QuerySet
from django.utils.translation import gettext as _

from promise_tracker.classifiers.models import PoliticalParty, PoliticalUnion
from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.core.exceptions import ApplicationError
from promise_tracker.promises.models import Promise, PromiseResult


class AnalyticsRecordType(Enum):
    PARTY = "Party"
    UNION = "Union"


@dataclass
class AnalyticsRecord:
    type: AnalyticsRecordType
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
    union = django_filters.ModelChoiceFilter(
        queryset=PoliticalUnion.objects.all(),
        required=False,
        label=_("Political Union"),
        help_text=_("Filter results by political union."),
        field_name="promise__union",
        method="filter_by_union",
    )

    def filter_by_party(
        self, queryset: QuerySet[PromiseResult], name: str, value: PoliticalParty
    ) -> QuerySet[PromiseResult]:
        if value:
            return queryset.filter(promise__party=value)
        return queryset

    def filter_by_union(
        self, queryset: QuerySet[PromiseResult], name: str, value: PoliticalUnion
    ) -> QuerySet[PromiseResult]:
        if value:
            return queryset.filter(promise__union=value)
        return queryset

    class Meta:
        model = PromiseResult
        fields = []


class AnalyticsSelectors:
    FIELD_INVALID = _("Field {field} is invalid!")
    ONLY_ONE_OF_PARTY_OR_UNION = _("Analytics can be generated for either a party or a union only!")
    PARTY_NOT_FOUND = _("Party does not exist!")
    UNION_NOT_FOUND = _("Union does not exist!")

    def _ensure_party_xor_union(self, party_id: UUID | None, union_id: UUID | None) -> None:
        if party_id is not None and union_id is not None and party_id != "" and union_id != "":
            raise ApplicationError(self.ONLY_ONE_OF_PARTY_OR_UNION)

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
                type=AnalyticsRecordType.PARTY,
                name=party.name,
                id=party.id,
                completed_count=party_agg.get("completed") or 0,
                uncompleted_count=party_agg.get("uncompleted") or 0,
            )
        )

        unions = PoliticalUnion.objects.filter(
            parties=party,
            promises__results__is_final=True,
            promises__results__review_status=PromiseResult.ReviewStatus.APPROVED,
            promises__review_status=Promise.ReviewStatus.APPROVED,
        ).distinct()

        for union in unions:
            analytics.extend(self._generate_analytics_for_union(union, qs))

        return analytics

    def _generate_analytics_for_union(
        self, union: PoliticalUnion, qs: QuerySet[PromiseResult]
    ) -> list[AnalyticsRecord]:
        analytics: list[AnalyticsRecord] = []

        if qs.count() == 0:
            return analytics

        union_agg = qs.aggregate(
            completed=Count("id", filter=Q(status=PromiseResult.CompletionStatus.COMPLETED)),
            uncompleted=Count("id", filter=Q(status=PromiseResult.CompletionStatus.ABANDONED)),
        )

        analytics.append(
            AnalyticsRecord(
                type=AnalyticsRecordType.UNION,
                name=union.name,
                id=union.id,
                completed_count=union_agg.get("completed") or 0,
                uncompleted_count=union_agg.get("uncompleted") or 0,
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
                    type=AnalyticsRecordType.PARTY,
                    name=group["promise__party__name"],
                    id=group["promise__party__id"],
                    completed_count=group.get("completed") or 0,
                    uncompleted_count=group.get("uncompleted") or 0,
                )
            )

        union_groups = (
            qs.filter(promise__union__isnull=False)
            .values("promise__union__id", "promise__union__name")
            .annotate(
                completed=Count("id", filter=Q(status=PromiseResult.CompletionStatus.COMPLETED)),
                uncompleted=Count("id", filter=Q(status=PromiseResult.CompletionStatus.ABANDONED)),
            )
        )

        for group in union_groups:
            analytics.append(
                AnalyticsRecord(
                    type=AnalyticsRecordType.UNION,
                    name=group["promise__union__name"],
                    id=group["promise__union__id"],
                    completed_count=group.get("completed") or 0,
                    uncompleted_count=group.get("uncompleted") or 0,
                )
            )

        return analytics

    def get_analytics(self, filters: dict) -> list[AnalyticsRecord]:
        party_id = filters.get("party")
        union_id = filters.get("union")

        self._ensure_party_xor_union(party_id, union_id)

        promises_qs = self._get_all_final_approved_results()
        promises_qs = AnalyticsFilterSet(filters, queryset=promises_qs).qs

        if party_id is not None and party_id != "":
            party = get_object_or_raise(PoliticalParty, self.PARTY_NOT_FOUND, id=party_id)
            return self._generate_analytics_for_party(party, promises_qs)

        if union_id is not None and union_id != "":
            union = get_object_or_raise(PoliticalUnion, self.UNION_NOT_FOUND, id=union_id)
            return self._generate_analytics_for_union(union, promises_qs)

        return self._generate_general_analytics(promises_qs)
