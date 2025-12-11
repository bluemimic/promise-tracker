from django import forms
from django.forms import Field
from django.utils.translation import gettext_lazy as _

from promise_tracker.classifiers.models import Convocation, PoliticalParty
from promise_tracker.common.fields import CommaSeparatedFormField
from promise_tracker.common.forms import FIELD_INVALID, FIELD_REQUIRED
from promise_tracker.common.utils import generate_model_form_errors
from promise_tracker.common.validators import CommaSeparatedStringValidator
from promise_tracker.common.widgets import MultiTextInput
from promise_tracker.promises.models import Promise


class PromiseEditForm(forms.ModelForm):
    sources = CommaSeparatedFormField(
        required=True,
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
        validators=[
            CommaSeparatedStringValidator(
                max_item_length=1000,
            )
        ],
        error_messages={
            "required": FIELD_REQUIRED.format(field=_("Sources")),
            "invalid": FIELD_INVALID.format(field=_("Sources")),
            "empty_item_not_allowed": FIELD_INVALID.format(field=_("Sources")),
            "max_items_exceeded": FIELD_INVALID.format(field=_("Sources")),
            "max_item_length_exceeded": FIELD_INVALID.format(field=_("Sources")),
            "min_items_not_met": FIELD_INVALID.format(field=_("Sources")),
            "invalid_list": FIELD_INVALID.format(field=_("Sources")),
            "max_length": FIELD_INVALID.format(field=_("Sources")),
        },
    )
    convocation: Field = forms.ModelChoiceField(
        queryset=Convocation.objects.all(),
        required=True,
        label=_("Convocation"),
        help_text=_("Select the convocation for the promise"),
        error_messages={
            "required": FIELD_REQUIRED.format(field=_("Convocation")),
            "invalid": FIELD_INVALID.format(field=_("Convocation")),
            "invalid_choice": FIELD_INVALID.format(field=_("Convocation")),
        },
    )
    party: Field = forms.ModelChoiceField(
        queryset=PoliticalParty.objects.all(),
        required=True,
        label=_("Party"),
        help_text=_("Select party who made the promise"),
        error_messages={
            "required": FIELD_REQUIRED.format(field=_("Party")),
            "invalid": FIELD_INVALID.format(field=_("Party")),
            "invalid_choice": FIELD_INVALID.format(field=_("Party")),
        },
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
        fields = ["name", "description", "sources", "date", "party", "convocation"]
        error_messages = generate_model_form_errors(fields, Promise)

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "date": forms.DateInput(attrs={"type": "date"}),
        }
