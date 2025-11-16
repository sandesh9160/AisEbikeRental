from django import forms
from core.models import Booking
from django.forms import DateInput

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['start_date', 'start_time', 'end_date', 'end_time']

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text="Pickup time"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text="Return time"
    )
