from django.forms.widgets import CheckboxSelectMultiple, Widget


class BootstrapCheckboxSelectMultiple(CheckboxSelectMultiple):
    option_template_name = "core/widgets/bootstrap_checkbox_option.html"


class MultiTextInput(Widget):
    template_name = "core/widgets/multi_text_input.html"

    def get_context(self, name, value, attrs):
        if value is None:
            values = []

        elif isinstance(value, str):
            values = [v.strip() for v in value.split(",") if v.strip()]

        else:
            values = list(value)

        values = [v for v in values if v and str(v).strip()]
        values.append("")

        attrs = dict(attrs or {})

        container_id = attrs.pop("container_id", f"{name}-list")
        row_class = attrs.pop("row_class", "source-row")
        input_class = attrs.pop("input_class", "form-control")
        remove_button_class = attrs.pop("remove_button_class", "remove-source btn btn-outline-danger")

        add_button_id = attrs.pop("add_button_id", f"add-{name}")
        add_button_class = attrs.pop("add_button_class", "add-source btn btn-outline-primary")
        row_id_prefix = attrs.pop("row_id_prefix", f"{name}-row")

        context = super().get_context(name, value, attrs)
        context["widget"].update(
            {
                "values": values,
                "name": name,
                "container_id": container_id,
                "row_class": row_class,
                "input_class": input_class,
                "remove_button_class": remove_button_class,
                "add_button_id": add_button_id,
                "add_button_class": add_button_class,
                "row_id_prefix": row_id_prefix,
            }
        )
        return context

    def value_from_datadict(self, data, files, name):
        return data.getlist(name)
