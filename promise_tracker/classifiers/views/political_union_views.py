from django.conf import settings
from django.contrib import messages
from django.core.files.uploadedfile import File
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views import View

from promise_tracker.classifiers.forms.political_union_forms import PoliticalUnionEditForm
from promise_tracker.classifiers.selectors.political_union_selectors import (
    PoliticalUnionFitlerSet,
    get_political_union_by_id,
    get_political_unions,
)
from promise_tracker.classifiers.services.political_union_services import PoliticalUnionService
from promise_tracker.common.mixins import (
    HandleErrorsMixin,
    RoleBasedAccessMixin,
    VerifiedLoginRequiredMixin,
)
from promise_tracker.common.utils import bootstrapify_form, is_htmx_request, paginate_queryset, prepare_get_params
from promise_tracker.common.views import BaseFormView
from promise_tracker.core.roles import Administrator


class PoliticalUnionCreateView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "classifiers/political_union/create.html"
    required_roles = [Administrator]
    success_message = _("Political union has been successfully created!")
    form_class = PoliticalUnionEditForm

    def form_valid(self, request, form, *args, **kwargs):
        service = PoliticalUnionService(performed_by=request.user)

        service.create_political_union(
            name=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
            party_ids=[p.id for p in form.cleaned_data["parties"]],
            established_date=form.cleaned_data["established_date"],
            liquidated_date=form.cleaned_data.get("liquidated_date"),
            ideologies=form.cleaned_data.get("ideologies"),
            logo=form.cleaned_data.get("logo"),
        )

        messages.success(request, self.success_message)

        return redirect("classifiers:political_unions:list")


class PoliticalUnionEditView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "classifiers/political_union/edit.html"
    required_roles = [Administrator]
    success_message = _("Political union has been successfully updated!")
    form_class = PoliticalUnionEditForm

    def get_instance(self, request, *args, **kwargs) -> object | None:
        return get_political_union_by_id(kwargs["id"])

    def form_valid(self, request, form, *args, **kwargs):
        service = PoliticalUnionService(performed_by=request.user)

        logo = form.cleaned_data.get("logo")
        if not isinstance(logo, File):
            logo = None

        service.edit_political_union(
            id=kwargs["id"],
            name=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
            party_ids=[p.id for p in form.cleaned_data["parties"]],
            established_date=form.cleaned_data["established_date"],
            liquidated_date=form.cleaned_data.get("liquidated_date"),
            ideologies=form.cleaned_data.get("ideologies"),
            logo=logo,
        )

        messages.success(request, self.success_message)

        return redirect("classifiers:political_unions:detail", id=kwargs["id"])


class PoliticalUnionDetailView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "classifiers/political_union/details.html"
    required_roles = [Administrator]

    def get(self, request, *args, **kwargs):
        political_union = get_political_union_by_id(kwargs["id"])

        context = {"political_union": political_union}

        return render(request, self.template_name, context)


class PoliticalUnionListView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, View):
    template_name = "classifiers/political_union/list.html"
    required_roles = [Administrator]

    def get(self, request, *args, **kwargs):
        political_unions_qs = get_political_unions(filters=request.GET)

        page_obj = paginate_queryset(request, political_unions_qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])
        filter_form = bootstrapify_form(PoliticalUnionFitlerSet(request.GET).form)

        context = {"page_obj": page_obj, "querystring": querystring}

        if is_htmx_request(request):
            return render(request, "classifiers/political_union/_political_unions_table.html", context)

        context.update({"filter_form": filter_form})
        return render(request, self.template_name, context)


class PoliticalUnionDeleteView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, View):
    required_roles = [Administrator]
    success_message = _("Political union has been successfully deleted!")

    def post(self, request, *args, **kwargs):
        political_union_id = kwargs.get("id")

        service = PoliticalUnionService(performed_by=request.user)
        service.delete_political_union(political_union_id)

        messages.success(request, self.success_message)

        return redirect("classifiers:political_unions:list")
