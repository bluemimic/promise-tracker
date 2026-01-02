from django import forms
from django.utils.translation import gettext_lazy as _

from promise_tracker.common.fields import CommaSeparatedFormField
from promise_tracker.common.utils import generate_model_form_errors
from promise_tracker.common.validators import CommaSeparatedStringValidator
from promise_tracker.common.widgets import MultiTextInput
from promise_tracker.promises.models import PromiseResult


class PromiseResultEditForm(forms.ModelForm):
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
            "required": _("Sources list is empty!"),
            "empty_item_not_allowed": _("Sources list is invalid!"),
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
        model = PromiseResult
        fields = ["name", "description", "sources", "is_final", "date", "status"]
        error_messages = generate_model_form_errors(fields, PromiseResult)

        error_messages["NON_FIELD_ERRORS"] = {
            "unique_together": str(_("A promise result with this name already exists.")),
        }

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "date": forms.DateInput(attrs={"type": "date"}),
        }
