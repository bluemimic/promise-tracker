from django import forms
from django.forms import Field
from django.utils.translation import gettext as _

from promise_tracker.classifiers.models import Convocation, PoliticalParty, PoliticalUnion
from promise_tracker.common.fields import CommaSeparatedFormField
from promise_tracker.common.utils import generate_model_form_errors
from promise_tracker.common.widgets import MultiTextInput
from promise_tracker.promises.models import Promise


class PromiseEditForm(forms.ModelForm):
    sources = CommaSeparatedFormField(
        label=_("Sources"),
        help_text=_("Add sources; use the + button to add rows."),
        widget=MultiTextInput(
            attrs={
                "container_id": "my-sources",
                "row_class": "my-source-row",
                "remove_button_class": "remove-source",
                "add_button_id": "add-source",
                "row_id_prefix": "source-row",
            }
        ),
    )
    convocation: Field = forms.ModelChoiceField(
        queryset=Convocation.objects.all(),
        required=True,
        label=_("Convocation"),
        help_text=_("Select the convocation for the promise"),
    )
    party: Field = forms.ModelChoiceField(
        queryset=PoliticalParty.objects.all(),
        required=False,
        label=_("Parties"),
        help_text=_("Select parties who made the promise"),
    )
    union = forms.ModelChoiceField(
        queryset=PoliticalUnion.objects.all(),
        required=False,
        label=_("Political Union"),
        help_text=_("Select the political union who made the promise"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and getattr(self.instance, "sources", None):
            self.initial.setdefault("sources", self.instance.sources)

    def clean_sources(self):
        data = self.cleaned_data.get("sources")

        if not data:
            return []

        cleaned = [s.strip() for s in data if s and str(s).strip()]

        return cleaned

    class Meta:
        model = Promise
        fields = ["name", "description", "sources", "date", "party", "union", "convocation"]
        error_messages = generate_model_form_errors(fields)

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "date": forms.DateInput(attrs={"type": "date"}),
        }
