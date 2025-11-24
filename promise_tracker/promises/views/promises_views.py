from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View

from promise_tracker.common.mixins import (
    HandleErrorsMixin,
    RoleBasedAccessMixin,
    VerifiedLoginRequiredMixin,
)
from promise_tracker.common.utils import bootstrapify_form, is_htmx_request, paginate_queryset, prepare_get_params
from promise_tracker.common.views import BaseFormView
from promise_tracker.core.roles import Administrator, RegisteredUser
from promise_tracker.promises.forms.promises_forms import PromiseEditForm
from promise_tracker.promises.models import Promise
from promise_tracker.promises.selectors.promise_result_selectors import PromiseResultSelectors
from promise_tracker.promises.selectors.promise_selectors import PromiseSelectors
from promise_tracker.promises.services.promise_services import PromiseService


class PromiseCreateView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "promises/promises/create.html"
    required_roles = [Administrator, RegisteredUser]
    success_message = _("Promise has been successfully created!")
    form_class = PromiseEditForm

    def form_valid(self, request, form, *args, **kwargs):
        service = PromiseService(performed_by=request.user)

        promise = service.create_promise(
            name=form.cleaned_data["name"],
            description=form.cleaned_data["description"],
            sources=form.cleaned_data["sources"],
            date=form.cleaned_data["date"],
            party_id=form.cleaned_data["party"].id,
            convocation_id=form.cleaned_data["convocation"].id,
        )

        messages.success(request, self.success_message)

        return redirect("promises:promises:details", id=promise.id)


class PromiseEditView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "promises/promises/edit.html"
    required_roles = [Administrator, RegisteredUser]
    success_message = _("Promise has been successfully updated!")
    form_class = PromiseEditForm

    def get_instance(self, request, *args, **kwargs) -> Promise | None:
        selectors = PromiseSelectors(request=request, performed_by=request.user)
        promise = selectors.get_promise_by_id(kwargs["id"])
        return promise

    def form_valid(self, request, form, *args, **kwargs):
        service = PromiseService(performed_by=request.user)

        promise = service.edit_promise(
            id=kwargs["id"],
            name=form.cleaned_data["name"],
            description=form.cleaned_data["description"],
            sources=form.cleaned_data["sources"],
            date=form.cleaned_data["date"],
            party_id=form.cleaned_data["party"].id,
            convocation_id=form.cleaned_data["convocation"].id,
        )

        messages.success(request, self.success_message)

        return redirect("promises:promises:details", id=promise.id)


class PromiseDetailView(RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "promises/promises/details.html"
    required_roles = [Administrator, RegisteredUser]

    allow_guests = True

    def get(self, request, *args, **kwargs):
        promise_selectors = PromiseSelectors(
            request=request, performed_by=(request.user if request.user.is_authenticated else None)
        )
        result_selectors = PromiseResultSelectors(
            performed_by=(request.user if request.user.is_authenticated else None)
        )
        promise = promise_selectors.get_promise_by_id(kwargs["id"])
        results_qs = result_selectors.get_promise_results_by_promise_id(kwargs["id"])

        results = paginate_queryset(request, results_qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])

        context = {"promise": promise, "results": results, "querystring": querystring}

        if is_htmx_request(request):
            context["page_obj"] = results
            return render(request, "promises/results/_results_cards.html", context)

        return render(request, self.template_name, context)


class PromiseListView(HandleErrorsMixin, View):
    template_name = "promises/promises/list.html"

    def get(self, request, *args, **kwargs):
        selectors = PromiseSelectors(
            request=request, performed_by=(request.user if request.user.is_authenticated else None)
        )
        promises_qs = selectors.get_promises(filters=request.GET)

        page_obj = paginate_queryset(request, promises_qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])

        filterset_cls = selectors.get_filterset_class()
        filterset = filterset_cls(request.GET, queryset=promises_qs, request=request)

        filter_form = bootstrapify_form(filterset.form)

        context = {"page_obj": page_obj, "querystring": querystring}

        if is_htmx_request(request):
            return render(request, "promises/promises/_promises_cards.html", context)

        context.update({"filter_form": filter_form})

        return render(request, self.template_name, context)


class PromiseDeleteView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator, RegisteredUser]
    success_message = _("Promise has been successfully deleted!")

    def post(self, request, *args, **kwargs):
        service = PromiseService(performed_by=request.user)
        service.delete_promise(id=kwargs["id"])

        messages.success(request, self.success_message)

        return redirect("promises:promises:list")


class PromiseApproveView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator]
    success_message = _("Promise has been successfully approved!")

    def post(self, request, *args, **kwargs):
        service = PromiseService(performed_by=request.user)
        service.evaluate_promise(id=kwargs["id"], new_status=Promise.ReviewStatus.APPROVED)

        messages.success(request, self.success_message)

        return redirect("promises:promises:details", id=kwargs["id"])


class PromiseRejectView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator]
    success_message = _("Promise has been successfully rejected!")

    def post(self, request, *args, **kwargs):
        service = PromiseService(performed_by=request.user)
        service.evaluate_promise(id=kwargs["id"], new_status=Promise.ReviewStatus.REJECTED)

        messages.success(request, self.success_message)

        return redirect("promises:promises:details", id=kwargs["id"])
