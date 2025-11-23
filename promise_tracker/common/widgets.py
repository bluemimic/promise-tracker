from django.forms.widgets import CheckboxSelectMultiple, ClearableFileInput


class BootstrapCheckboxSelectMultiple(CheckboxSelectMultiple):
    option_template_name = "core/widgets/bootstrap_checkbox_option.html"


class BootstrapFileInput(ClearableFileInput):
    template_name = "core/widgets/bootstrap_fileinput.html"
