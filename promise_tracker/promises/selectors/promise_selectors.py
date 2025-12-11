from uuid import UUID

import django_filters
from django.db.models import Q, QuerySet
from django.forms.widgets import CheckboxInput
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet, ModelChoiceFilter
from rolepermissions.checkers import has_role

from promise_tracker.classifiers.models import Convocation, PoliticalParty
from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.core.exceptions import ApplicationError, PermissionViolationError
from promise_tracker.core.roles import Administrator, RegisteredUser
from promise_tracker.promises.models import Promise, PromiseResult
from promise_tracker.users.models import BaseUser


class PromiseFilterSet(FilterSet):
    name = django_filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        label=_("Name"),
        help_text=_("Filter by name"),
    )
    convocation = ModelChoiceFilter(
        field_name="convocation__id",
        queryset=Convocation.objects.all(),
        label=_("Convocation"),
        help_text=_("Filter by convocation"),
        method="filter_convocation",
    )
    party = ModelChoiceFilter(
        field_name="party__id",
        queryset=PoliticalParty.objects.all(),
        label=_("Party"),
        help_text=_("Filter by party"),
        method="filter_party",
    )
    result_status = django_filters.ChoiceFilter(
        field_name="results__status",
        choices=PromiseResult.CompletionStatus.choices,
        label=_("Result Status"),
        help_text=_("Filter by promise result status"),
        method="filter_result_status",
    )

    def filter_convocation(self, queryset: QuerySet[Promise], name: str, value: Convocation) -> QuerySet[Promise]:
        if value:
            return queryset.filter(convocation=value)
        return queryset

    def filter_party(self, queryset: QuerySet[Promise], name: str, value: PoliticalParty) -> QuerySet[Promise]:
        if value:
            return queryset.filter(party=value)
        return queryset

    def filter_result_status(self, queryset: QuerySet[Promise], name: str, value: str) -> QuerySet[Promise]:
        if value:
            return queryset.filter(
                results__is_final=True, results__review_status=Promise.ReviewStatus.APPROVED, results__status=value
            )
        return queryset

    class Meta:
        model = Promise
        fields = {}


class PromiseRegisteredUserFilterSet(PromiseFilterSet):
    is_mine = django_filters.BooleanFilter(
        label=_("Is Mine"),
        help_text=_("Filter to only promises created by the logged-in user"),
        method="filter_is_mine",
        widget=CheckboxInput(),
    )

    def filter_is_mine(self, queryset: QuerySet[Promise], name: str, value: bool) -> QuerySet[Promise]:
        if value:
            return queryset.filter(created_by=self.request.user)
        return queryset


class PromiseAdminFilterSet(PromiseRegisteredUserFilterSet):
    is_unreviewed = django_filters.BooleanFilter(
        field_name="review_status",
        method="filter_unreviewed",
        label=_("Is Unreviewed"),
        help_text=_("Filter to only unreviewed promises"),
        widget=CheckboxInput(),
    )

    def filter_unreviewed(self, queryset: QuerySet[Promise], name: str, value: bool) -> QuerySet[Promise]:
        if value:
            return queryset.filter(Q(review_status=Promise.ReviewStatus.PENDING))
        return queryset


class PromiseSelectors:
    def __init__(self, request: HttpRequest, performed_by: BaseUser | None = None) -> None:
        self.performed_by = performed_by
        self.request = request

    USER_IS_NOT_REGISTERED_ERROR = _("User is not registered!")
    NOT_FOUND_ERROR = _("Promise not found.")

    def _ensure_mine_not_for_guests(self, filters: dict) -> None:
        if filters.get("is_mine") and not (
            has_role(self.performed_by, RegisteredUser) or has_role(self.performed_by, Administrator)
        ):
            raise ApplicationError(self.USER_IS_NOT_REGISTERED_ERROR)

    def _ensure_unreviewed_only_for_admin(self, filters: dict) -> None:
        if filters.get("is_unreviewed") and not has_role(self.performed_by, Administrator):
            raise PermissionViolationError()

    def _ensure_can_view(self, promise: Promise) -> None:
        if self.performed_by is None:
            if promise.review_status == Promise.ReviewStatus.APPROVED:
                return
            else:
                raise PermissionViolationError()

        if has_role(self.performed_by, Administrator):
            return
        elif promise.review_status == Promise.ReviewStatus.APPROVED:
            return
        elif promise.created_by is None or self.performed_by.id != promise.created_by.id:
            raise PermissionViolationError()

    def _get_queryset(self, filters: dict) -> QuerySet[Promise]:
        # Guests can only see approved promises
        if not (has_role(self.performed_by, RegisteredUser) or has_role(self.performed_by, Administrator)):
            return Promise.objects.filter(review_status=Promise.ReviewStatus.APPROVED)

        # Administrators can see all promises
        if has_role(self.performed_by, Administrator):
            return Promise.objects.all()

        # Registered users can see their own promises and approved promises
        if filters.get("is_mine"):
            return Promise.objects.filter(created_by=self.performed_by)
        else:
            return Promise.objects.filter(
                Q(review_status=Promise.ReviewStatus.APPROVED) | Q(created_by=self.performed_by)
            ).distinct()

    def get_filterset_class(self) -> type[FilterSet]:
        if has_role(self.performed_by, Administrator):
            return PromiseAdminFilterSet
        elif has_role(self.performed_by, RegisteredUser):
            return PromiseRegisteredUserFilterSet
        else:
            return PromiseFilterSet

    def get_promises(self, filters: dict | None = None) -> QuerySet[Promise]:
        filters = filters or {}

        self._ensure_mine_not_for_guests(filters)
        self._ensure_unreviewed_only_for_admin(filters)

        qs = self._get_queryset(filters)
        filterset_class = self.get_filterset_class()

        return filterset_class(filters, request=self.request, queryset=qs).qs.distinct().order_by("date")

    def get_promise_by_id(self, id: UUID) -> Promise:
        promise = get_object_or_raise(Promise, self.NOT_FOUND_ERROR, id=id)

        self._ensure_can_view(promise)

        return promise
