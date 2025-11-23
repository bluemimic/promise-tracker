from django import forms

from promise_tracker.classifiers.models import Convocation, LegislativeInstitution, PoliticalParty, PoliticalUnion
from promise_tracker.common.utils import generate_model_form_errors
from promise_tracker.common.widgets import BootstrapCheckboxSelectMultiple


class ConvocationEditForm(forms.ModelForm):
    political_parties = forms.ModelMultipleChoiceField(
        queryset=PoliticalParty.objects.all(),
        required=False,
        widget=BootstrapCheckboxSelectMultiple(),
        label="Political parties",
    )

    political_unions = forms.ModelMultipleChoiceField(
        queryset=PoliticalUnion.objects.all(),
        required=False,
        widget=BootstrapCheckboxSelectMultiple(),
        label="Political unions",
    )

    legislative_institution = forms.ModelChoiceField(
        queryset=LegislativeInstitution.objects.all(),
        required=True,
        label="Legislative institution",
    )

    class Meta:
        model = Convocation
        fields = [
            "name",
            "start_date",
            "end_date",
            "legislative_institution",
            "political_parties",
            "political_unions",
        ]
        error_messages = generate_model_form_errors(fields)

        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }
