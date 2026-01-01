from django import forms
from django.utils.translation import gettext_lazy as _

from promise_tracker.classifiers.models import PoliticalParty
from promise_tracker.common.utils import generate_model_form_errors
from promise_tracker.core.exceptions import ApplicationError


class PoliticalPartyEditForm(forms.ModelForm):
    def clean_name(self):
        name = self.cleaned_data["name"]
        if PoliticalParty.objects.filter(name=name).exists():
            raise ApplicationError(_("A political party %(value)s already exists.") % {"value": name})
        return name

    class Meta:
        model = PoliticalParty
        fields = ["name", "established_date", "liquidated_date"]
        error_messages = generate_model_form_errors(fields, PoliticalParty)

        widgets = {
            "established_date": forms.DateInput(attrs={"type": "date"}),
            "liquidated_date": forms.DateInput(attrs={"type": "date"}),
        }
