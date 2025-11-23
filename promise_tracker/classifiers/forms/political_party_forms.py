from django import forms

from promise_tracker.classifiers.models import PoliticalParty
from promise_tracker.common.utils import generate_model_form_errors
from promise_tracker.common.validators import FileSizeValidator, ImageValidator
from promise_tracker.common.widgets import BootstrapCheckboxSelectMultiple, BootstrapFileInput


class PoliticalPartyEditForm(forms.ModelForm):
    logo = forms.FileField(
        required=False,
        widget=BootstrapFileInput(),
        validators=[
            ImageValidator(),
            FileSizeValidator(),
        ],
    )

    class Meta:
        model = PoliticalParty
        fields = ["name", "email", "established_date", "liquidated_date", "ideologies", "logo"]
        error_messages = generate_model_form_errors(fields)

        widgets = {
            "logo": BootstrapFileInput(),
            "established_date": forms.DateInput(attrs={"type": "date"}),
            "liquidated_date": forms.DateInput(attrs={"type": "date"}),
            "ideologies": BootstrapCheckboxSelectMultiple(),
        }
