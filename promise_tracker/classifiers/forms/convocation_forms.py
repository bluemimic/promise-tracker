from django import forms

from promise_tracker.classifiers.models import Convocation, PoliticalParty
from promise_tracker.common.utils import generate_model_form_errors
from promise_tracker.common.widgets import BootstrapCheckboxSelectMultiple


class ConvocationEditForm(forms.ModelForm):
    political_parties = forms.ModelMultipleChoiceField(
        queryset=PoliticalParty.objects.all(),
        required=True,
        widget=BootstrapCheckboxSelectMultiple(),
        label="Political parties",
    )

    class Meta:
        model = Convocation
        fields = [
            "name",
            "start_date",
            "end_date",
            "political_parties",
        ]
        error_messages = generate_model_form_errors(fields)

        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }
