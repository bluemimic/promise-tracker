from uuid import UUID

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet
from rolepermissions.checkers import has_role

from promise_tracker.common.utils import get_object_or_none
from promise_tracker.core.exceptions import NotFoundError, PermissionViolationError
from promise_tracker.core.roles import Administrator
from promise_tracker.users.models import BaseUser


class UserFilterSet(FilterSet):
    class Meta:
        model = BaseUser
        fields = {
            "name": ["icontains"],
            "surname": ["icontains"],
            "email": ["icontains"],
            "username": ["icontains"],
            "is_verified": ["exact"],
            "is_active": ["exact"],
            "is_deleted": ["exact"],
            "is_admin": ["exact"],
        }


class UserSelectors:
    def __init__(self, performed_by: BaseUser):
        self.performed_by = performed_by

    NOT_FOUND_ERROR = _("User not found.")

    def get_user_by_id(self, id: UUID) -> BaseUser:
        user = get_object_or_none(BaseUser, id=id)

        if user is None:
            raise NotFoundError(self.NOT_FOUND_ERROR)

        if not has_role(self.performed_by, Administrator):
            if self.performed_by.id != user.id or not user.is_active:
                raise PermissionViolationError()

            if user.is_deleted:
                raise NotFoundError(self.NOT_FOUND_ERROR)

        return user

    def get_users(self, filters: dict | None = None) -> QuerySet[BaseUser]:
        filters = filters or {}

        qs = BaseUser.objects.all()

        return UserFilterSet(data=filters, queryset=qs).qs.order_by("-created_at")
