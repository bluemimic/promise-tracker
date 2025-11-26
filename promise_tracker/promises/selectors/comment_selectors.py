from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.utils.translation import gettext as _
from loguru import logger
from rolepermissions.checkers import has_role

from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.core.exceptions import PermissionViolationError
from promise_tracker.core.roles import Administrator
from promise_tracker.promises.models import Comment, Promise
from promise_tracker.users.models import BaseUser

NOT_FOUND_ERROR = _("Promise not found.")


@dataclass
class CommentTreeNode:
    id: UUID
    text: str
    is_deleted: bool
    created_at: datetime
    created_by: BaseUser
    username: str
    replies: list[CommentTreeNode]


class CommentSelectors:
    def __init__(self, performed_by: BaseUser | None = None) -> None:
        self.performed_by = performed_by

    def _ensure_is_owner_or_admin(self, comment: Comment) -> None:
        if self.performed_by is None:
            logger.error("Anonymous user attempted to edit a comment without permission.")
            raise PermissionViolationError()

        if not has_role(self.performed_by, Administrator):
            if comment.created_by is None or self.performed_by.id != comment.created_by.id:
                logger.error(f"User {self.performed_by.id} attempted to edit comment {comment.id} without permission.")
                raise PermissionViolationError()

    def get_comments_tree_for_promise(self, promise_id: UUID) -> list[CommentTreeNode]:
        promise = get_object_or_raise(Promise, NOT_FOUND_ERROR, id=promise_id)

        comments = (
            Comment.objects.filter(promise=promise).select_related("created_by", "response_to").order_by("created_at")
        )

        comment_dict: dict[UUID, CommentTreeNode] = {}
        roots: list[CommentTreeNode] = []

        for comment in comments:
            text = comment.content

            if comment.created_by:
                username = comment.created_by.username

                if comment.created_by.is_deleted or not comment.created_by.is_active:
                    username = _("[Deleted User]")
            else:
                username = _("[Deleted User]")

            if comment.is_deleted:
                text = _("[Deleted]")

            comment_dict[comment.id] = CommentTreeNode(
                id=comment.id,
                text=text,
                is_deleted=comment.is_deleted,
                created_at=comment.created_at,
                created_by=comment.created_by,
                username=username,
                replies=[],
            )

        for comment in comments:
            node = comment_dict[comment.id]
            parent = comment.response_to

            if parent:
                parent_node = comment_dict.get(parent.id)

                if parent_node:
                    parent_node.replies.append(node)
                else:
                    roots.append(node)
            else:
                roots.append(node)

        def sort_nodes(nodes: list[CommentTreeNode]) -> None:
            nodes.sort(key=lambda n: n.created_at, reverse=True)
            for n in nodes:
                if n.replies:
                    sort_nodes(n.replies)

        sort_nodes(roots)

        return roots

    def get_comment_by_id(self, comment_id: UUID) -> Comment | None:
        comment = get_object_or_raise(Comment, NOT_FOUND_ERROR, id=comment_id)

        self._ensure_is_owner_or_admin(comment)

        return comment
