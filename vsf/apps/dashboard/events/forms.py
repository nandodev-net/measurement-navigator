# Django imports
from django import forms
from django.contrib.auth import get_user_model
from django.forms           import ModelForm

# Local imports
from apps.main.events.models import Event


class EventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['identification'].disabled = True
        self.fields['issue_type'].disabled = True
        self.fields['domain'].disabled = True
        self.fields['asn'].disabled = True
        self.fields['end_date'].disabled = True

    class Meta:
        
        model = Event
        fields = [
            'identification',
            'confirmed',
            'end_date',
            'public_evidence',
            'private_evidence',
            'issue_type',
            'domain',
            'asn',
        ]
        widgets = {
          'public_evidence': forms.Textarea(attrs={'rows':3}),
          'private_evidence': forms.Textarea(attrs={'rows':3}),
        }
