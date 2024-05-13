from typing import Tuple

from crispy_forms.helper import FormHelper
from django import forms
from django.core import validators
from django.forms import Field


class ManualTaskForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ManualTaskForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()


class UserTaskForm(forms.Form):
    @staticmethod
    def create_field(field_type, prop_data, **field_kwargs) -> forms.Field:
        if field_type == "string":
            field = UserTaskForm.create_string_field(prop_data, field_kwargs)
        elif field_type == "number":
            field = forms.DecimalField(**field_kwargs)
        elif field_type == "boolean":
            field = UserTaskForm.create_boolean_field(prop_data, field_kwargs)
        elif field_type == "integer":
            field = forms.IntegerField(**field_kwargs)
        elif field_type == "date":
            field = forms.DateField(**field_kwargs)
        elif field_type == "datetime":
            field = forms.DateTimeField(**field_kwargs)
        elif field_type == "decimal":
            field = forms.DecimalField(**field_kwargs)
        elif field_type == "duration":
            field = forms.DurationField(**field_kwargs)
        else:
            field = forms.CharField(**field_kwargs)

        return field

    @staticmethod
    def create_boolean_field(prop_data, field_kwargs) -> Field:
        # Check if it's a boolean field with "oneOf" property
        if "oneOf" in prop_data:
            choices = [
                (option["const"], option["title"]) for option in prop_data["oneOf"]
            ]
            field = forms.NullBooleanField(
                widget=forms.RadioSelect(choices=choices), **field_kwargs
            )
        else:
            field = forms.BooleanField(**field_kwargs)
        return field

    @staticmethod
    def create_string_field(prop_data, field_kwargs) -> Field:
        if "enum" in prop_data:  # Check if enum property exists
            choices = [(option, option) for option in prop_data["enum"]]
            field = forms.ChoiceField(choices=choices, **field_kwargs)
        elif "format" in prop_data:
            if prop_data["format"] == "email":
                field = forms.EmailField(**field_kwargs)
            elif prop_data["format"] == "uri":
                field = forms.URLField(**field_kwargs)
            elif prop_data["format"] == "date":
                # field = forms.DateField(
                #     widget=forms.DateInput(attrs={"type": "date"}), **field_kwargs
                # )
                field = forms.DateField(
                    widget=forms.DateInput(
                        attrs={"type": "date", "class": "date-widget"}
                    ),
                    **field_kwargs
                )
            elif prop_data["format"] == "date-time":
                field = forms.DateTimeField(
                    widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
                    **field_kwargs
                )
            elif prop_data["format"] == "time":
                # field = forms.TimeField(
                #     widget=forms.TimeInput(
                #         attrs={"type": "time", "class": "time-widget"}
                #     ),
                #     **field_kwargs
                # )
                field = forms.CharField(
                    widget=forms.TextInput(
                        attrs={
                            "type": "time",
                            "class": "time-widget",
                            "inputmode": "numeric",
                        }
                    ),
                    **field_kwargs
                )
            else:
                field = forms.CharField(**field_kwargs)
        else:
            field = forms.CharField(**field_kwargs)
        return field

    @staticmethod
    def get_field_arguments(prop_name, prop_data) -> Tuple[str, dict]:
        field_type = prop_data["type"]
        field_kwargs = {
            "label": prop_data.get("title", prop_name),
            # "placeholder": prop_data.get("placeholder"),
            "disabled": prop_data.get("disabled", False),
            "label_suffix": prop_data.get("labelSuffix"),
            "help_text": prop_data.get("helpText"),
        }
        return (field_type, field_kwargs)

    @staticmethod
    def set_additional_props(field, prop_data) -> forms.Field:
        if "default" in prop_data:
            field.initial = prop_data["default"]
        if "minimum" in prop_data:
            field.validators.append(validators.MinValueValidator(prop_data["minimum"]))
        if "maximum" in prop_data:
            field.validators.append(validators.MaxValueValidator(prop_data["maximum"]))
        if "minLength" in prop_data:
            field.validators.append(
                validators.MinLengthValidator(prop_data["minLength"])
            )
        if "pattern" in prop_data:
            field.validators.append(
                validators.RegexValidator(
                    prop_data["pattern"],
                    message=prop_data.get("validationErrorMessage"),
                )
            )
        if isinstance(field, forms.DecimalField):
            if "maxDigits" in prop_data and "decimalPlaces" in prop_data:
                field.validators.append(
                    validators.DecimalValidator(
                        max_digits=prop_data["maxDigits"],
                        decimal_places=prop_data["decimalPlaces"],
                    )
                )
        return field

    def __init__(self, task, *args, **kwargs):
        super(UserTaskForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        schema = task.schema
        if schema is None:
            return

        for prop_name, prop_data in schema["properties"].items():
            field_type, field_kwargs = self.get_field_arguments(prop_name, prop_data)
            field = self.create_field(field_type, prop_data, **field_kwargs)
            # Set additional properties based on JSON
            field = self.set_additional_props(field, prop_data)

            self.fields[prop_name] = field

        # Set required fields
        for required_field in schema.get("required", []):
            self.fields[required_field].required = True
