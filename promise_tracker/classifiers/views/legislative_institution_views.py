from django.conf import settings
from django.contrib import messages
from django.core.files.uploadedfile import File
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views import View

from promise_tracker.classifiers.forms.legislative_institution_forms import (
    LegislativeInstitutionEditForm,
)
from promise_tracker.classifiers.selectors.legislative_institution_selectors import (
    LegislativeInstitutionFilerSet,
    get_legislative_institution_by_id,
    get_legislative_institutions,
)
from promise_tracker.classifiers.services.legislative_institution_services import LegislativeInstitutionService
from promise_tracker.common.mixins import (
    HandleErrorsMixin,
    RoleBasedAccessMixin,
    VerifiedLoginRequiredMixin,
)
from promise_tracker.common.utils import bootstrapify_form, is_htmx_request, paginate_queryset, prepare_get_params
from promise_tracker.common.views import BaseFormView
from promise_tracker.core.roles import Administrator


class LegislativeInstitutionCreateView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "classifiers/legislative_institution/create.html"
    required_roles = [Administrator]
    success_message = _("Legislative institution has been successfully created!")
    form_class = LegislativeInstitutionEditForm

    def form_valid(self, request, form, *args, **kwargs):
        service = LegislativeInstitutionService(performed_by=request.user)

        service.create_legislative_institution(
            name=form.cleaned_data["name"],
            institution_type=form.cleaned_data["institution_type"],
            institution_level=form.cleaned_data["institution_level"],
            logo=form.cleaned_data.get("logo"),
        )

        messages.success(request, self.success_message)

        return redirect("classifiers:legislative_institutions:list")


class LegislativeInstitutionEditView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "classifiers/legislative_institution/edit.html"
    required_roles = [Administrator]
    success_message = _("Legislative institution has been successfully updated!")
    form_class = LegislativeInstitutionEditForm

    def get_instance(self, request, *args, **kwargs) -> object | None:
        return get_legislative_institution_by_id(id=kwargs["id"])

    def form_valid(self, request, form, *args, **kwargs):
        service = LegislativeInstitutionService(performed_by=request.user)

        logo = form.cleaned_data.get("logo")

        if not isinstance(logo, File):
            logo = None

        service.edit_legislative_institution(
            id=kwargs["id"],
            name=form.cleaned_data["name"],
            institution_type=form.cleaned_data["institution_type"],
            institution_level=form.cleaned_data["institution_level"],
            logo=logo,
        )

        messages.success(request, self.success_message)

        return redirect("classifiers:legislative_institutions:detail", id=kwargs["id"])


class LegislativeInstitutionDetailView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "classifiers/legislative_institution/details.html"
    required_roles = [Administrator]

    def get(self, request, *args, **kwargs):
        legislative_institution = get_legislative_institution_by_id(kwargs["id"])

        context = {"legislative_institution": legislative_institution}

        return render(request, self.template_name, context)


class LegislativeInstitutionListView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, View):
    template_name = "classifiers/legislative_institution/list.html"
    required_roles = [Administrator]

    def get(self, request, *args, **kwargs):
        legislative_institutions_qs = get_legislative_institutions(filters=request.GET)

        page_obj = paginate_queryset(request, legislative_institutions_qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])
        filter_form = bootstrapify_form(LegislativeInstitutionFilerSet(request.GET).form)

        context = {"page_obj": page_obj, "querystring": querystring}

        if is_htmx_request(request):
            return render(request, "classifiers/legislative_institution/_legislative_institutions_table.html", context)

        context.update({"filter_form": filter_form})
        return render(request, self.template_name, context)


class LegislativeInstitutionDeleteView(VerifiedLoginRequiredMixin, RoleBasedAccessMixin, View):
    required_roles = [Administrator]
    success_message = _("Legislative institution has been successfully deleted!")

    def post(self, request, *args, **kwargs):
        legislative_institution_id = kwargs.get("id")

        service = LegislativeInstitutionService(performed_by=request.user)
        service.delete_legislative_institution(legislative_institution_id)

        messages.success(request, self.success_message)

        return redirect("classifiers:legislative_institutions:list")
