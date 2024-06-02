# Django imports
from django import forms

# Local imports
from apps.main.cases.models import Case


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = "__all__"


class CaseCreateForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = [
            "title",
            "case_type",
            "start_date",
            "end_date",
            "category",
            "description",
        ]
