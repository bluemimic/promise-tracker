from django import forms

from promise_tracker.common.utils import generate_model_form_errors
from promise_tracker.promises.models import Comment


class CommentEditForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        error_messages = generate_model_form_errors(fields)

        widgets = {
            "content": forms.Textarea(attrs={"rows": 4, "maxlength": 2000}),
        }
