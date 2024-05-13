from django.forms.models import model_to_dict


class ModelConverterMixin:
    def to_dict(self):
        return model_to_dict(self)

    @classmethod
    def from_dict(cls, dct):
        return cls(**dct)
