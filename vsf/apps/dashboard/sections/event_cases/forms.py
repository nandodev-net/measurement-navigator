# Django imports
from django import forms
from django.contrib.auth import get_user_model
from django.forms           import ModelForm

# Local imports
from apps.main.cases.models import Case


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = '__all__'




    