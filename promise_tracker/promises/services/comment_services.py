from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet
from django.utils.translation import gettext as _
from loguru import logger
from rolepermissions.checkers import has_role

from promise_tracker.common.services import BaseService
from promise_tracker.common.utils import get_object_or_none, get_object_or_raise
from promise_tracker.core.exceptions import ApplicationError, PermissionViolationError
from promise_tracker.core.roles import Administrator
from promise_tracker.promises.models import Comment, Promise
from promise_tracker.users.models import BaseUser


class CommentService:
    def __init__(self, performed_by: BaseUser, base_service: BaseService[Comment] | None = None) -> None:
        self.performed_by = performed_by
        self.base_service: BaseService[Comment] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("Comment not found.")
    PROMISE_NOT_FOUND = _("Promise does not exist!")
    PARENT_COMMENT_NOT_FOUND = _("Parent comment does not exist!")
    COMMENT_IS_ALREADY_DELETED = _("Comment is already deleted!")

    def _ensure_promise_is_reviewed(self, promise: Promise) -> None:
        if not promise.is_reviewed:
            raise ApplicationError(self.PROMISE_NOT_FOUND)

    def _get_promise_comments_queryset(self, promise: Promise) -> QuerySet[Comment]:
        return Comment.objects.filter(promise=promise)

    def _ensure_have_comment_parent(self, promise_comments_qs: QuerySet[Comment], parent_comment_id: UUID) -> None:
        if not promise_comments_qs.filter(id=parent_comment_id).exists():
            raise ApplicationError(self.PARENT_COMMENT_NOT_FOUND)

    def _ensure_is_owner_or_admin(self, comment: Comment) -> None:
        if not has_role(self.performed_by, Administrator):
            if not comment.created_by or self.performed_by.id != comment.created_by.id:
                raise PermissionViolationError()

    def _ensure_is_not_deleted(self, comment: Comment) -> None:
        if comment.is_deleted:
            raise PermissionViolationError()

    @transaction.atomic
    def create_comment(self, text: str, promise_id: UUID, parent_comment_id: UUID | None = None) -> Comment:
        promise = get_object_or_raise(Promise, self.PROMISE_NOT_FOUND, id=promise_id)

        self._ensure_promise_is_reviewed(promise)

        promise_comments_qs = self._get_promise_comments_queryset(promise)
        parent = None

        if parent_comment_id is not None:
            self._ensure_have_comment_parent(promise_comments_qs, parent_comment_id)
            parent = get_object_or_none(Comment, id=parent_comment_id)

        comment = Comment(
            content=text,
            promise=promise,
            response_to=parent,
        )

        comment = self.base_service.create_base(comment, self.performed_by)

        logger.info(f"Created comment: {comment.id}")

        return comment

    @transaction.atomic
    def edit_comment(self, id: UUID, text: str) -> Comment:
        comment = get_object_or_raise(Comment, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_is_owner_or_admin(comment)
        self._ensure_is_not_deleted(comment)

        comment.content = text

        comment = self.base_service.edit_base(comment, self.performed_by)

        logger.info(f"Edited comment: {comment.id}")

        return comment

    @transaction.atomic
    def delete_comment(self, id: UUID) -> None:
        comment = get_object_or_raise(Comment, self.NOT_FOUND_MESSAGE, id=id)

        self._ensure_is_owner_or_admin(comment)

        if comment.is_deleted:
            raise ApplicationError(self.COMMENT_IS_ALREADY_DELETED)

        comment.is_deleted = True

        self.base_service.edit_base(comment, self.performed_by)

        logger.info(f"Deleted (soft) comment: {comment.id}")
