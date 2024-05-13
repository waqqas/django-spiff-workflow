# Create your tests here.
import unittest

from django import forms

from django_spiff_workflow.forms import UserTaskForm


class UserTaskFormtest(unittest.TestCase):
    def test_create_field_string(self):
        prop_data = {"type": "string"}
        field = UserTaskForm.create_field("string", prop_data)
        self.assertIsInstance(field, forms.CharField)

    def test_create_field_number(self):
        prop_data = {"type": "number"}
        field = UserTaskForm.create_field("number", prop_data)
        self.assertIsInstance(field, forms.DecimalField)

    def test_create_field_boolean(self):
        prop_data = {"type": "boolean"}
        field = UserTaskForm.create_field("boolean", prop_data)
        self.assertIsInstance(field, forms.BooleanField)

    def test_create_field_integer(self):
        prop_data = {"type": "integer"}
        field = UserTaskForm.create_field("integer", prop_data)
        self.assertIsInstance(field, forms.IntegerField)

    def test_create_field_unknown(self):
        prop_data = {"type": "unknown"}
        field = UserTaskForm.create_field("unknown", prop_data)
        self.assertIsInstance(field, forms.CharField)
