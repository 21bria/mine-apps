from django import forms
from django.apps import apps
from ..models.sample_type_model import SampleType
from ..models.sample_type_details_model import SampleTypeDetails


class SampleTypeForm(forms.ModelForm):
    class Meta:
        model = SampleType
        fields = ['id','type_sample', 'keterangan', 'status']
    
    def clean_type_sample(self):
        type_sample = self.cleaned_data['type_sample']
        if SampleType.objects.filter(type_sample=type_sample).exists():
            raise forms.ValidationError("Type sample already exists.")
        return type_sample

class SampleTypeDetailsForm(forms.ModelForm):
    class Meta:
        model  = SampleTypeDetails
        fields = ['id_method']

