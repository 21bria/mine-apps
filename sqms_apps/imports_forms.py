# forms.py
# forms.py
from django import forms
from django.apps import apps

class ImportForm(forms.Form):
    all_models = list(apps.get_app_config('sqms_apps').get_models())
    model_choices = [(model._meta.label, model._meta.verbose_name) for model in all_models]

    table_choice = forms.ChoiceField(choices=model_choices)
    columns = forms.MultipleChoiceField(choices=[], widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super(ImportForm, self).__init__(*args, **kwargs)
        if 'table_choice' in self.data:
            model_label = self.data['table_choice']
            app_label, model_name = model_label.split('.')
            model = apps.get_model(app_label, model_name)
            self.fields['columns'].choices = [(field.name, field.verbose_name) for field in self.get_fields(model)]
        else:
            self.fields['columns'].choices = []

    def get_fields(self, model):
        return model._meta.fields if model else []