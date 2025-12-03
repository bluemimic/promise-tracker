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
from promise_tracker.promises.forms.promise_results_forms import PromiseResultEditForm
from promise_tracker.promises.models import PromiseResult
from promise_tracker.promises.selectors.promise_result_selectors import PromiseResultFilterSet, PromiseResultSelectors
from promise_tracker.promises.services.promise_result_services import PromiseResultService


class PromiseResultCreateView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "promises/results/create.html"
    required_roles = [Administrator, RegisteredUser]
    success_message = _("Promise result has been successfully created!")
    form_class = PromiseResultEditForm

    def form_valid(self, request, form, *args, **kwargs):
        service = PromiseResultService(performed_by=request.user)

        service.create_result(
            name=form.cleaned_data["name"],
            description=form.cleaned_data["description"],
            sources=form.cleaned_data["sources"],
            is_final=form.cleaned_data["is_final"],
            date=form.cleaned_data["date"],
            promise_id=kwargs["promise_id"],
            status=form.cleaned_data["status"],
        )

        messages.success(request, self.success_message)

        return redirect("promises:promises:details", id=kwargs["promise_id"])


class PromiseResultEditView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "promises/results/edit.html"
    required_roles = [Administrator, RegisteredUser]
    success_message = _("Promise result has been successfully updated!")
    form_class = PromiseResultEditForm

    def get_instance(self, request, *args, **kwargs) -> PromiseResult | None:
        selectors = PromiseResultSelectors(performed_by=request.user)
        result = selectors.get_promise_results_by_id(kwargs["id"])
        return result

    def form_valid(self, request, form, *args, **kwargs):
        service = PromiseResultService(performed_by=request.user)

        service.edit_result(
            id=kwargs["id"],
            name=form.cleaned_data["name"],
            description=form.cleaned_data["description"],
            sources=form.cleaned_data["sources"],
            is_final=form.cleaned_data["is_final"],
            date=form.cleaned_data["date"],
            status=form.cleaned_data["status"],
            promise_id=kwargs["promise_id"],
        )

        messages.success(request, self.success_message)

        return redirect("promises:promises:details", id=kwargs["promise_id"])


class PromiseResultListView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "promises/results/list.html"
    required_roles = [Administrator]

    def get(self, request, *args, **kwargs):
        selectors = PromiseResultSelectors(performed_by=request.user)
        results_qs = selectors.get_results(filters=request.GET)

        page_obj = paginate_queryset(request, results_qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])
        filterset = PromiseResultFilterSet(request.GET, queryset=results_qs, request=request)
        filter_form = bootstrapify_form(filterset.form)

        context = {"page_obj": page_obj, "querystring": querystring, "all": True}

        if is_htmx_request(request):
            return render(request, "promises/results/_results_cards.html", context)

        context.update({"filter_form": filter_form})

        return render(request, self.template_name, context)


class PromiseResultMineListView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "promises/results/list.html"
    required_roles = [RegisteredUser]

    def get(self, request, *args, **kwargs):
        selectors = PromiseResultSelectors(performed_by=request.user)

        filters = request.GET.dict()
        filters["is_mine"] = True

        results_qs = selectors.get_results(filters=filters)

        page_obj = paginate_queryset(request, results_qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])

        context = {"page_obj": page_obj, "querystring": querystring, "mine": True}

        if is_htmx_request(request):
            return render(request, "promises/results/_results_cards.html", context)

        return render(request, self.template_name, context)


class PromiseResultDeleteView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator, RegisteredUser]
    success_message = _("Promise result has been successfully deleted!")

    def post(self, request, *args, **kwargs):
        service = PromiseResultService(performed_by=request.user)
        service.delete_result(id=kwargs["id"])

        messages.success(request, self.success_message)

        return redirect("promises:promises:details", id=kwargs["promise_id"])


class PromiseResultApproveView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator]
    success_message = _("Promise result has been successfully approved!")

    def post(self, request, *args, **kwargs):
        service = PromiseResultService(performed_by=request.user)
        service.evaluate_result(id=kwargs["id"], new_status=PromiseResult.ReviewStatus.APPROVED)

        messages.success(request, self.success_message)

        return redirect("promises:promises:details", id=kwargs["promise_id"])


class PromiseResultRejectView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator]
    success_message = _("Promise result has been successfully rejected!")

    def post(self, request, *args, **kwargs):
        service = PromiseResultService(performed_by=request.user)
        service.evaluate_result(id=kwargs["id"], new_status=PromiseResult.ReviewStatus.REJECTED)

        messages.success(request, self.success_message)

        return redirect("promises:promises:details", id=kwargs["promise_id"])
