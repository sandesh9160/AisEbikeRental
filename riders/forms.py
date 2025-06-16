from django import forms
from core.models import Booking
from django.forms import DateInput

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['start_date', 'end_date']

    start_date = forms.DateField(
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )