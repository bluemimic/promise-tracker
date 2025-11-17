from uuid import UUID

import django_filters
from django.db.models import Q, QuerySet
from django.utils.translation import gettext as _
from django_filters import FilterSet
from rolepermissions.checkers import has_role

from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.core.exceptions import ApplicationError, PermissionViolationError
from promise_tracker.core.roles import Administrator, RegisteredUser
from promise_tracker.promises.models import Promise
from promise_tracker.users.models import BaseUser


class PromiseFilterSet(FilterSet):
    is_mine = django_filters.BooleanFilter()

    class Meta:
        model = Promise
        fields = {
            "name": ["iexact", "icontains"],
            "party": ["exact"],
            "union": ["exact"],
            "convocation": ["exact"],
            "is_unreviewed": ["exact"],
        }


class PromiseSelectors:
    def __init__(self, performed_by: BaseUser) -> None:
        self.performed_by = performed_by

    USER_IS_NOT_REGISTERED_ERROR = _("User is not registered!")
    NOT_FOUND_ERROR = _("Promise not found.")

    def _ensure_mine_not_for_guests(self, filters: dict) -> None:
        if filters.get("is_mine") and not has_role(self.performed_by, (RegisteredUser, Administrator)):
            raise ApplicationError(self.USER_IS_NOT_REGISTERED_ERROR)

    def _ensure_unreviewed_only_for_admin(self, filters: dict) -> None:
        if filters.get("is_unreviewed") and not has_role(self.performed_by, Administrator):
            raise PermissionViolationError()

    def _ensure_can_view(self, promise: Promise) -> None:
        if has_role(self.performed_by, Administrator):
            return
        if promise.review_status == Promise.ReviewStatus.APPROVED:
            return
        if promise.created_by is None or self.performed_by.id != promise.created_by.id:
            raise PermissionViolationError()

    def _get_queryset(self, filters: dict) -> QuerySet[Promise]:
        # Guests can only see approved promises
        if not has_role(self.performed_by, (RegisteredUser, Administrator)):
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

    def get_promises(self, filters: dict | None = None) -> QuerySet[Promise]:
        filters = filters or {}

        self._ensure_mine_not_for_guests(filters)
        self._ensure_unreviewed_only_for_admin(filters)

        qs = self._get_queryset(filters)

        return PromiseFilterSet(filters, queryset=qs).qs

    def get_promise_by_id(self, id: UUID) -> Promise:
        promise = get_object_or_raise(Promise, self.NOT_FOUND_ERROR, id=id)

        self._ensure_can_view(promise)

        return promise
