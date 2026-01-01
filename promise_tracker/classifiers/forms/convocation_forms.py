from django import forms
from django.utils.translation import gettext_lazy as _

from promise_tracker.classifiers.models import Convocation, PoliticalParty
from promise_tracker.common.forms import FIELD_INVALID, FIELD_REQUIRED
from promise_tracker.common.utils import generate_model_form_errors
from promise_tracker.common.widgets import BootstrapCheckboxSelectMultiple
from promise_tracker.core.exceptions import ApplicationError


class ConvocationEditForm(forms.ModelForm):
    political_parties = forms.ModelMultipleChoiceField(
        queryset=PoliticalParty.objects.all(),
        required=True,
        widget=BootstrapCheckboxSelectMultiple(),
        label=_("Political parties"),
        error_messages={
            "required": FIELD_REQUIRED.format(field=_("Political parties")),
            "invalid_pk_value": FIELD_INVALID.format(field=_("Political parties")),
            "invalid_choice": FIELD_INVALID.format(field=_("Political parties")),
            "invalid_list": FIELD_INVALID.format(field=_("Political parties")),
        },
    )

    def clean_name(self):
        name = self.cleaned_data["name"]
        if Convocation.objects.filter(name=name).exists():
            raise ApplicationError(_("A convocation %(value)s already exists.") % {"value": name})
        return name

    class Meta:
        model = Convocation
        fields = [
            "name",
            "start_date",
            "end_date",
            "political_parties",
        ]
        error_messages = generate_model_form_errors(fields, Convocation)

        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }
