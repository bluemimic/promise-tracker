from django import forms
from django.utils.translation import gettext as _

from promise_tracker.classifiers.models import PoliticalParty, PoliticalUnion
from promise_tracker.common.utils import generate_model_form_errors
from promise_tracker.common.validators import FileSizeValidator, ImageValidator
from promise_tracker.common.widgets import BootstrapCheckboxSelectMultiple, BootstrapFileInput


class PoliticalUnionEditForm(forms.ModelForm):
    parties = forms.ModelMultipleChoiceField(
        queryset=PoliticalParty.objects.all(),
        required=True,
        widget=BootstrapCheckboxSelectMultiple(),
        label=_("Parties"),
        help_text=_("Select parties for the union"),
    )

    logo = forms.FileField(
        required=False,
        widget=BootstrapFileInput(),
        validators=[ImageValidator(), FileSizeValidator()],
    )

    class Meta:
        model = PoliticalUnion
        fields = ["name", "email", "parties", "established_date", "liquidated_date", "ideologies", "logo"]
        error_messages = generate_model_form_errors(fields)

        widgets = {
            "established_date": forms.DateInput(attrs={"type": "date"}),
            "liquidated_date": forms.DateInput(attrs={"type": "date"}),
            "ideologies": BootstrapCheckboxSelectMultiple(),
        }
