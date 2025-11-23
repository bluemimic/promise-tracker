from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View

from promise_tracker.classifiers.forms.convocation_forms import ConvocationEditForm
from promise_tracker.classifiers.selectors.convocation_selectors import (
    ConvocationFilterSet,
    get_convocation_by_id,
    get_convocations,
)
from promise_tracker.classifiers.services.convocation_services import ConvocationService
from promise_tracker.common.mixins import (
    HandleErrorsMixin,
    RoleBasedAccessMixin,
    VerifiedLoginRequiredMixin,
)
from promise_tracker.common.utils import bootstrapify_form, is_htmx_request, paginate_queryset, prepare_get_params
from promise_tracker.common.views import BaseFormView
from promise_tracker.core.roles import Administrator


class ConvocationCreateView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "classifiers/convocation/create.html"
    required_roles = [Administrator]
    success_message = _("Convocation has been successfully created!")
    form_class = ConvocationEditForm

    def form_valid(self, request, form, *args, **kwargs):
        service = ConvocationService(performed_by=request.user)

        service.create_convocation(
            name=form.cleaned_data["name"],
            start_date=form.cleaned_data["start_date"],
            end_date=form.cleaned_data.get("end_date"),
            party_ids=[p.id for p in form.cleaned_data.get("political_parties")],
        )

        messages.success(request, self.success_message)

        return redirect("classifiers:convocations:list")


class ConvocationEditView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "classifiers/convocation/edit.html"
    required_roles = [Administrator]
    success_message = _("Convocation has been successfully updated!")
    form_class = ConvocationEditForm

    def get_instance(self, request, *args, **kwargs) -> object | None:
        return get_convocation_by_id(kwargs["id"])

    def form_valid(self, request, form, *args, **kwargs):
        service = ConvocationService(performed_by=request.user)

        service.edit_convocation(
            id=kwargs["id"],
            name=form.cleaned_data["name"],
            start_date=form.cleaned_data["start_date"],
            end_date=form.cleaned_data.get("end_date"),
            party_ids=[p.id for p in form.cleaned_data.get("political_parties")],
        )

        messages.success(request, self.success_message)

        return redirect("classifiers:convocations:detail", id=kwargs["id"])


class ConvocationDetailView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "classifiers/convocation/details.html"
    required_roles = [Administrator]

    def get(self, request, *args, **kwargs):
        convocation = get_convocation_by_id(kwargs["id"])

        context = {"convocation": convocation}

        return render(request, self.template_name, context)


class ConvocationListView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "classifiers/convocation/list.html"
    required_roles = [Administrator]

    def get(self, request, *args, **kwargs):
        convocations_qs = get_convocations(filters=request.GET)

        page_obj = paginate_queryset(request, convocations_qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])
        filter_form = bootstrapify_form(ConvocationFilterSet(request.GET).form)

        context = {"page_obj": page_obj, "querystring": querystring}

        if is_htmx_request(request):
            return render(request, "classifiers/convocation/_convocations_table.html", context)

        context.update({"filter_form": filter_form})
        return render(request, self.template_name, context)


class ConvocationDeleteView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator]
    success_message = _("Convocation has been successfully deleted!")

    def post(self, request, *args, **kwargs):
        convocation_id = kwargs.get("id")

        service = ConvocationService(performed_by=request.user)
        service.delete_convocation(convocation_id)

        messages.success(request, self.success_message)

        return redirect("classifiers:convocations:list")
