from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.utils.translation import gettext as _

from promise_tracker.common.utils import get_object_or_raise
from promise_tracker.promises.models import Comment, Promise

NOT_FOUND_ERROR = _("Promise not found.")


@dataclass
class CommentTreeNode:
    id: UUID
    text: str
    is_deleted: bool
    created_at: datetime
    username: str
    replies: list[CommentTreeNode]


def get_comments_tree_for_promise(promise_id: UUID) -> list[CommentTreeNode]:
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

    return roots
