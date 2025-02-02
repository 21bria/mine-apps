from django import forms
from django.contrib.auth.models import Group
from ..models.task_model import taskList
from django.core.exceptions import ValidationError

class TaskListForm(forms.ModelForm):
    allowed_groups = forms.ModelMultipleChoiceField(
        queryset = Group.objects.all(),
        widget   = forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'}),
        required = False,
        label    = "Allowed Groups"
    )

    class Meta:
        model   = taskList
        fields  = ['type_table', 'status', 'allowed_groups']
        widgets = {
            'type_table' : forms.TextInput(attrs={'class': 'form-input flex-1', 'placeholder': 'Enter table'})
        }

    def clean(self):
        cleaned_data = super().clean()
        # order_slug   = cleaned_data.get('order_slug')
        type_table   = cleaned_data.get('type_table')

        # Validasi untuk kedua field
        # if not order_slug or not type_table:
        if not type_table:
            print("Type Table tidak boleh kosong.")  # Debugging
            raise forms.ValidationError("Type Table tidak boleh kosong.")

        # Validasi: Duplikat
        existing_task = taskList.objects.filter(type_table=type_table).exclude(id=self.instance.id).first()
        if existing_task:
            self.add_error('type_table', ValidationError("Type Table sudah ada."))

        return cleaned_data
