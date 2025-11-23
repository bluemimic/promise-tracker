from django.conf import settings
from django.contrib import messages
from django.core.files.uploadedfile import File
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View

from promise_tracker.classifiers.forms.political_party_forms import (
    PoliticalPartyEditForm,
)
from promise_tracker.classifiers.selectors.political_party_selectors import (
    PoliticalPartyFilerSet,
    get_political_parties,
    get_political_party_by_id,
)
from promise_tracker.classifiers.services.political_party_services import PoliticalPartyService
from promise_tracker.common.mixins import (
    HandleErrorsMixin,
    RoleBasedAccessMixin,
    VerifiedLoginRequiredMixin,
)
from promise_tracker.common.utils import bootstrapify_form, is_htmx_request, paginate_queryset, prepare_get_params
from promise_tracker.common.views import BaseFormView
from promise_tracker.core.roles import Administrator


class PoliticalPartyCreateView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "classifiers/political_party/create.html"
    required_roles = [Administrator]
    success_message = _("Political party has been successfully created!")
    form_class = PoliticalPartyEditForm

    def form_valid(self, request, form, *args, **kwargs):
        service = PoliticalPartyService(performed_by=request.user)

        service.create_political_party(
            name=form.cleaned_data["name"],
            established_date=form.cleaned_data["established_date"],
            liquidated_date=form.cleaned_data.get("liquidated_date"),
        )

        messages.success(request, self.success_message)

        return redirect("classifiers:political_parties:list")


class PoliticalPartyEditView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "classifiers/political_party/edit.html"
    required_roles = [Administrator]
    success_message = _("Political party has been successfully updated!")
    form_class = PoliticalPartyEditForm

    def get_instance(self, request, *args, **kwargs) -> object | None:
        return get_political_party_by_id(kwargs["id"])

    def form_valid(self, request, form, *args, **kwargs):
        service = PoliticalPartyService(performed_by=request.user)

        logo = form.cleaned_data.get("logo")

        if not isinstance(logo, File):
            logo = None

        service.edit_political_party(
            id=kwargs["id"],
            name=form.cleaned_data["name"],
            established_date=form.cleaned_data["established_date"],
            liquidated_date=form.cleaned_data.get("liquidated_date"),
        )

        messages.success(request, self.success_message)

        return redirect("classifiers:political_parties:detail", id=kwargs["id"])


class PoliticalPartyDetailView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "classifiers/political_party/details.html"
    required_roles = [Administrator]

    def get(self, request, *args, **kwargs):
        political_party = get_political_party_by_id(kwargs["id"])

        context = {"political_party": political_party}

        return render(request, self.template_name, context)


class PoliticalPartyListView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "classifiers/political_party/list.html"
    required_roles = [Administrator]

    def get(self, request, *args, **kwargs):
        political_parties_qs = get_political_parties(filters=request.GET)

        page_obj = paginate_queryset(request, political_parties_qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])
        filter_form = bootstrapify_form(PoliticalPartyFilerSet(request.GET).form)

        context = {"page_obj": page_obj, "querystring": querystring}

        if is_htmx_request(request):
            return render(request, "classifiers/political_party/_political_parties_table.html", context)

        context.update({"filter_form": filter_form})
        return render(request, self.template_name, context)


class PoliticalPartyDeleteView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator]
    success_message = _("Political party has been successfully deleted!")

    def post(self, request, *args, **kwargs):
        political_party_id = kwargs.get("id")

        service = PoliticalPartyService(performed_by=request.user)
        service.delete_political_party(political_party_id)

        messages.success(request, self.success_message)

        return redirect("classifiers:political_parties:list")
