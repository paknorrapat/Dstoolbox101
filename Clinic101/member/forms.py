from django import forms
from base.models import *

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['treatment','dentist','date','time_slot']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time_slot': forms.TimeInput(attrs={'type': 'time'}),
        }