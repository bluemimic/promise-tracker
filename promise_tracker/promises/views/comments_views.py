from django.contrib import messages
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views import View

from promise_tracker.common.mixins import (
    HandleErrorsMixin,
    RoleBasedAccessMixin,
    VerifiedLoginRequiredMixin,
)
from promise_tracker.common.views import BaseFormView
from promise_tracker.core.roles import Administrator, RegisteredUser
from promise_tracker.promises.forms.comments_forms import CommentEditForm
from promise_tracker.promises.selectors.comment_selectors import CommentSelectors
from promise_tracker.promises.services.comment_services import CommentService


class CommentCreateView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    form_class = CommentEditForm
    template_name = "promises/comments/create_form.html"
    required_roles = [Administrator, RegisteredUser]
    success_message = _("Comment has been successfully created!")

    def form_valid(self, request, form, *args, **kwargs):
        service = CommentService(performed_by=request.user)

        comment = service.create_comment(
            promise_id=kwargs["promise_id"],
            text=form.cleaned_data["content"],
            parent_comment_id=kwargs.get("parent_comment_id"),
        )

        context = {"comment": comment, "promise": comment.promise, "is_reply": bool(kwargs.get("parent_comment_id"))}

        messages.success(request, self.success_message)

        return render(request, "promises/comments/comment_response.html", context)


class CommentEditView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    form_class = CommentEditForm
    template_name = "promises/comments/edit_form.html"
    required_roles = [Administrator, RegisteredUser]
    success_message = _("Comment has been successfully edited!")

    def get_instance(self, request, *args, **kwargs):
        selectors = CommentSelectors(performed_by=request.user)
        return selectors.get_comment_by_id(kwargs["id"])

    def form_valid(self, request, form, *args, **kwargs):
        service = CommentService(performed_by=request.user)
        comment = service.edit_comment(id=kwargs["id"], text=form.cleaned_data["content"])

        context = {"comment": comment, "promise": comment.promise}

        messages.success(request, self.success_message)

        return render(request, "promises/comments/comment_response.html", context)


class CommentNodeView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator, RegisteredUser]

    def get(self, request, *args, **kwargs):
        selectors = CommentSelectors(performed_by=request.user)
        comment = selectors.get_comment_by_id(kwargs["id"])

        return render(
            request,
            "promises/comments/comment_node.html",
            {"comment": comment, "promise": comment.promise},
        )


class CommentDeleteView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator, RegisteredUser]
    success_message = _("Comment has been successfully deleted!")

    def post(self, request, *args, **kwargs):
        service = CommentService(performed_by=request.user)
        service.delete_comment(id=kwargs["id"])

        messages.success(request, self.success_message)

        selectors = CommentSelectors(performed_by=request.user)
        comment = selectors.get_comment_by_id(kwargs["id"])

        return render(
            request,
            "promises/comments/comment_response.html",
            {"comment": comment, "promise": comment.promise},
        )
