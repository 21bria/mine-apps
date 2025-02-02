# forms.py
from django import forms

# forms.py di dalam app_b
from django import forms

class UserDatabaseConfigForm(forms.Form):
    client_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={
        'class': 'form-input peer w-full rounded-lg bg-slate-150 px-3 py-2 pl-9 ring-primary/50 placeholder:text-slate-400 hover:bg-slate-200 focus:ring dark:bg-navy-900/90 dark:ring-accent/50 dark:placeholder:text-navy-300 dark:hover:bg-navy-900 dark:focus:bg-navy-900',
        'placeholder': 'Client Name'
    }))
    db_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={
        'class': 'form-input peer w-full rounded-lg bg-slate-150 px-3 py-2 pl-9 ring-primary/50 placeholder:text-slate-400 hover:bg-slate-200 focus:ring dark:bg-navy-900/90 dark:ring-accent/50 dark:placeholder:text-navy-300 dark:hover:bg-navy-900 dark:focus:bg-navy-900',
        'placeholder': 'Database'
    }))
    db_user = forms.CharField(max_length=255, widget=forms.TextInput(attrs={
        'class': 'form-input peer w-full rounded-lg bg-slate-150 px-3 py-2 pl-9 ring-primary/50 placeholder:text-slate-400 hover:bg-slate-200 focus:ring dark:bg-navy-900/90 dark:ring-accent/50 dark:placeholder:text-navy-300 dark:hover:bg-navy-900 dark:focus:bg-navy-900',
        'placeholder': 'User'
    }))
    db_password = forms.CharField(required=False,widget=forms.PasswordInput(attrs={
        'class': 'form-input peer w-full rounded-lg bg-slate-150 px-3 py-2 pl-9 ring-primary/50 placeholder:text-slate-400 hover:bg-slate-200 focus:ring dark:bg-navy-900/90 dark:ring-accent/50 dark:placeholder:text-navy-300 dark:hover:bg-navy-900 dark:focus:bg-navy-900',
        'placeholder': 'Password'
    }))
    db_host = forms.CharField(max_length=255, widget=forms.TextInput(attrs={
        'class': 'form-input peer w-full rounded-lg bg-slate-150 px-3 py-2 pl-9 ring-primary/50 placeholder:text-slate-400 hover:bg-slate-200 focus:ring dark:bg-navy-900/90 dark:ring-accent/50 dark:placeholder:text-navy-300 dark:hover:bg-navy-900 dark:focus:bg-navy-900',
        'placeholder': 'Host'
    }))
    db_port = forms.CharField(max_length=255, widget=forms.TextInput(attrs={
        'class': 'form-input peer w-full rounded-lg bg-slate-150 px-3 py-2 pl-9 ring-primary/50 placeholder:text-slate-400 hover:bg-slate-200 focus:ring dark:bg-navy-900/90 dark:ring-accent/50 dark:placeholder:text-navy-300 dark:hover:bg-navy-900 dark:focus:bg-navy-900',
        'placeholder': 'Port'
    }))


