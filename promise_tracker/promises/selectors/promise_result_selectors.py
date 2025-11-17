from uuid import UUID

import django_filters
from django.db.models import Q, QuerySet
from django.forms.widgets import CheckboxInput
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet
from rolepermissions.checkers import has_role

from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.core.exceptions import ApplicationError, PermissionViolationError
from promise_tracker.core.roles import Administrator, RegisteredUser
from promise_tracker.promises.models import Promise, PromiseResult
from promise_tracker.users.models import BaseUser


class PromiseResultFilterSet(FilterSet):
    is_mine = django_filters.BooleanFilter(
        method="filter_is_mine",
        label=_("Is Mine"),
        help_text=_("Filter results created by the current user"),
    )
    is_unreviewed = django_filters.BooleanFilter(
        field_name="review_status",
        method="filter_unreviewed",
        label=_("Is Unreviewed"),
        help_text=_("Filter to only unreviewed promise results"),
        widget=CheckboxInput(),
    )

    def __init__(self, *args, **kwargs):
        self.performed_by = kwargs.pop("performed_by", None)
        super().__init__(*args, **kwargs)

    def filter_is_mine(self, queryset: QuerySet[PromiseResult], name: str, value: bool) -> QuerySet[PromiseResult]:
        if value:
            return queryset.filter(created_by=self.performed_by)
        return queryset

    def filter_unreviewed(self, queryset: QuerySet[PromiseResult], name: str, value: bool) -> QuerySet[PromiseResult]:
        if value:
            return queryset.filter(Q(review_status=PromiseResult.ReviewStatus.PENDING))
        return queryset

    class Meta:
        model = PromiseResult
        fields = []


class PromiseResultSelectors:
    def __init__(self, performed_by: BaseUser) -> None:
        self.performed_by = performed_by

    REGISTERED_USER_ONLY_OWN_ERROR = _("Registered users can only view their own promise results!")
    NOT_FOUND_ERROR = _("Promise not found.")

    def _ensure_registered_users_access_only_their_own(self, filters: dict) -> None:
        if has_role(self.performed_by, Administrator):
            return

        if has_role(self.performed_by, RegisteredUser) and not filters.get("is_mine"):
            raise ApplicationError(self.REGISTERED_USER_ONLY_OWN_ERROR)

    def _ensure_unreviewed_only_for_admin(self, filters: dict) -> None:
        if filters.get("is_unreviewed") and not has_role(self.performed_by, Administrator):
            raise PermissionViolationError()

    def _ensure_can_view(self, result: PromiseResult) -> None:
        if has_role(self.performed_by, Administrator):
            return
        if result.review_status == PromiseResult.ReviewStatus.APPROVED:
            return
        if result.created_by is None or self.performed_by.id != result.created_by.id:
            raise PermissionViolationError()

    def _get_queryset_for_promise(self, promise: Promise) -> QuerySet[PromiseResult]:
        qs = PromiseResult.objects.filter(promise=promise)

        # Guests
        if not (has_role(self.performed_by, RegisteredUser) or has_role(self.performed_by, Administrator)):
            return qs.filter(review_status=PromiseResult.ReviewStatus.APPROVED)

        # Admins
        if has_role(self.performed_by, Administrator):
            return qs

        # Registered users
        return qs.filter(Q(review_status=PromiseResult.ReviewStatus.APPROVED) | Q(created_by=self.performed_by))

    def _get_all_promise_results(self, filters: dict) -> QuerySet[PromiseResult]:
        # Guests
        if not (has_role(self.performed_by, RegisteredUser) or has_role(self.performed_by, Administrator)):
            raise PermissionViolationError()

        # Admins
        if has_role(self.performed_by, Administrator):
            return PromiseResult.objects.all()

        # Registered users
        return PromiseResult.objects.filter(created_by=self.performed_by)

    def get_promise_results_by_promise_id(self, promise_id: UUID) -> QuerySet[PromiseResult]:
        result = get_object_or_raise(Promise, self.NOT_FOUND_ERROR, id=promise_id)

        qs = self._get_queryset_for_promise(result)

        return qs.order_by("date")

    def get_promise_results_by_id(self, id: UUID) -> PromiseResult:
        result = get_object_or_raise(PromiseResult, self.NOT_FOUND_ERROR, id=id)

        self._ensure_can_view(result)

        return result

    def get_results(self, filters: dict | None = None) -> QuerySet[PromiseResult]:
        filters = filters or {}

        self._ensure_registered_users_access_only_their_own(filters)
        self._ensure_unreviewed_only_for_admin(filters)

        qs = self._get_all_promise_results(filters)

        return PromiseResultFilterSet(filters, queryset=qs, performed_by=self.performed_by).qs.order_by("-date")
