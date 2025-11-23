from django import forms

from promise_tracker.classifiers.models import LegislativeInstitution
from promise_tracker.common.utils import generate_model_form_errors
from promise_tracker.common.validators import FileSizeValidator, ImageValidator
from promise_tracker.common.widgets import BootstrapFileInput


class LegislativeInstitutionEditForm(forms.ModelForm):
    logo = forms.FileField(
        required=False,
        widget=BootstrapFileInput(),
        validators=[
            ImageValidator(),
            FileSizeValidator(),
        ],
    )

    class Meta:
        model = LegislativeInstitution
        fields = ["name", "institution_type", "institution_level", "logo"]
        error_messages = generate_model_form_errors(fields)

        widgets = {
            "logo": BootstrapFileInput(),
        }
