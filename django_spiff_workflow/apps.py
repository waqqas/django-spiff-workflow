from django.apps import AppConfig


class DjangoSpiffWorkflowConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_spiff_workflow"

    def ready(self):
        from . import signals
