from typing import Type

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import BaseForm
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View
from rolepermissions.checkers import has_role

from promise_tracker.authentication.services import AuthService
from promise_tracker.common.mixins import (
    HandleErrorsMixin,
    RoleBasedAccessMixin,
    VerifiedLoginRequiredMixin,
)
from promise_tracker.common.utils import bootstrapify_form, is_htmx_request, paginate_queryset, prepare_get_params
from promise_tracker.common.views import BaseFormView
from promise_tracker.core.exceptions import ApplicationError
from promise_tracker.core.roles import Administrator, RegisteredUser
from promise_tracker.users.enums import ModerationAction
from promise_tracker.users.forms import (
    UserCreateAdminForm,
    UserCreateForm,
    UserEditAdminForm,
    UserEditForm,
    UserVerifyForm,
)
from promise_tracker.users.selectors import UserFilterSet, UserSelectors
from promise_tracker.users.services import UserService


def _get_create_form(request) -> Type[BaseForm]:
    if request.user.is_authenticated and has_role(request.user, Administrator):
        return UserCreateAdminForm
    return UserCreateForm


def _get_edit_form(request) -> Type[BaseForm]:
    if has_role(request.user, Administrator):
        return UserEditAdminForm
    return UserEditForm


class UserCreateView(RoleBasedAccessMixin, BaseFormView):
    template_name = "users/user_create.html"
    required_roles = [Administrator]
    allow_guests = True
    success_message = _("User has been successfully created!")

    def get_form_class(self, request, *args, **kwargs) -> Type[BaseForm]:
        return _get_create_form(request)

    def get_extra_context(self, request, form, *args, **kwargs) -> dict:
        return {"registration": not request.user.is_authenticated}

    def form_valid(self, request, form, *args, **kwargs):
        user_service = UserService(performed_by=request.user if request.user.is_authenticated else None)

        user_service.create_user(
            name=form.cleaned_data["name"],
            surname=form.cleaned_data["surname"],
            email=form.cleaned_data["email"],
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
            another_password=form.cleaned_data["another_password"],
            is_admin=form.cleaned_data.get("is_admin", False),
        )

        messages.success(request, self.success_message)

        if not has_role(request.user, Administrator):
            return redirect("authentication:login")

        return redirect("users:list")


class UserEditView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "users/user_edit.html"
    required_roles = [Administrator, RegisteredUser]
    success_message = _("User has been successfully updated!")

    def _has_changed_email(self, old: str, new: str) -> bool:
        return old.lower() != new.lower()

    def get_form_class(self, request, *args, **kwargs):
        return _get_edit_form(request)

    def get_instance(self, request, *args, **kwargs) -> object | None:
        user_selectors = UserSelectors(performed_by=request.user)

        return user_selectors.get_user_by_id(kwargs["id"])

    def form_valid(self, request, form, *args, **kwargs):
        user_service = UserService(performed_by=request.user)
        user_selectors = UserSelectors(performed_by=request.user)

        user = user_selectors.get_user_by_id(kwargs.get("id"))

        old_email = user.email
        new_email = form.cleaned_data.get("email")

        user = user_service.edit_user(
            id=kwargs.get("id"),
            name=form.cleaned_data.get("name"),
            surname=form.cleaned_data.get("surname"),
            email=form.cleaned_data.get("email"),
            username=form.cleaned_data.get("username"),
            password=form.cleaned_data.get("password"),
            another_password=form.cleaned_data.get("another_password"),
            is_admin=form.cleaned_data.get("is_admin", False),
        )

        update_session_auth_hash(request, user)

        messages.success(request, self.success_message)

        if self._has_changed_email(old_email, new_email) and (
            not has_role(request.user, Administrator) or request.user.id == user.id
        ):
            messages.info(request, _("Please verify your new email address!"))
            return redirect("users:verify")

        return redirect("users:detail", id=kwargs.get("id"))


class UserDetailView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "users/user_detail.html"
    required_roles = [Administrator, RegisteredUser]

    def get(self, request, *args, **kwargs):
        requested_user_id = kwargs.get("id")

        user_selectors = UserSelectors(performed_by=request.user)
        user = user_selectors.get_user_by_id(requested_user_id)

        return render(request, self.template_name, {"user": user})


class UserListView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "users/user_list.html"
    required_roles = [Administrator]

    def get(self, request, *args, **kwargs):
        user_selectors = UserSelectors(performed_by=request.user)
        users_qs = user_selectors.get_users(filters=request.GET)

        page_obj = paginate_queryset(request, users_qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])
        filter_form = bootstrapify_form(UserFilterSet(request.GET).form)

        context = {"page_obj": page_obj, "querystring": querystring}

        if is_htmx_request(request):
            return render(request, "users/_users_table.html", context)

        context.update({"filter_form": filter_form})
        return render(request, self.template_name, context)


class UserDeleteView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator, RegisteredUser]
    success_message = _("User has been successfully deleted!")

    def post(self, request, *args, **kwargs):
        requested_user_id = kwargs.get("id")

        current_user_id = request.user.id

        user_service = UserService(performed_by=request.user)
        user_service.delete_user(requested_user_id)

        messages.success(request, self.success_message)

        if has_role(request.user, Administrator):
            return redirect("users:list")

        if current_user_id == requested_user_id:
            auth_service = AuthService(request=request)
            auth_service.logout()

        return redirect("home:index")


class UserVerifyView(RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "users/user_verify.html"
    required_roles = [RegisteredUser, Administrator]
    allow_unverified = True
    success_message = _("User has been successfully verified!")

    def get(self, request, *args, **kwargs):
        form = bootstrapify_form(UserVerifyForm())
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = UserVerifyForm(request.POST)

        if form.is_valid():
            verification_code = form.cleaned_data["verification_code"]

            user_service = UserService(performed_by=request.user)

            try:
                user_service.verify_user_email(
                    id=request.user.id,
                    verification_code=verification_code,
                )

                messages.success(request, self.success_message)

                return redirect("home:index")

            except ApplicationError as e:
                form.add_error(None, e.message)

        form = bootstrapify_form(form)
        return render(request, self.template_name, {"form": form})


class UserResendVerificationView(LoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [RegisteredUser, Administrator]
    allow_unverified = True
    success_message = _("Verification code has been resent!")

    def post(self, request, *args, **kwargs):
        user_service = UserService(performed_by=request.user)

        try:
            user_service.send_verification_email(id=request.user.id)
            messages.success(request, self.success_message)
        except ApplicationError as e:
            messages.error(request, e.message)

        return redirect("users:verify")


class UserBlockView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator]

    def post(self, request, *args, **kwargs):
        requested_user_id = kwargs.get("id")

        user_service = UserService(performed_by=request.user)
        user_service.moderate_user(requested_user_id, ModerationAction.BAN)

        messages.success(request, _("User has been successfully blocked."))

        return redirect("users:detail", id=requested_user_id)


class UserUnblockView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator]

    def post(self, request, *args, **kwargs):
        requested_user_id = kwargs.get("id")

        user_service = UserService(performed_by=request.user)
        user_service.moderate_user(requested_user_id, ModerationAction.UNBAN)

        messages.success(request, _("User has been successfully unblocked."))

        return redirect("users:detail", id=requested_user_id)
