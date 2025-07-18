from django import forms
from core.models import EBike, VehicleRegistration

class EBikeForm(forms.ModelForm):
    class Meta:
        model = EBike
        fields = ['name', 'description', 'price_per_day', 'price_per_week', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter E-bike name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe the E-bike', 'rows': 4}),
            'price_per_day': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price per day'}),
            'price_per_week': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price per week'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }
        
    def clean_price_per_day(self):
        price = self.cleaned_data.get('price_per_day')
        if price <= 0:
            raise forms.ValidationError("Price per day must be greater than zero.")
        return price

    def clean_price_per_week(self):
        price = self.cleaned_data.get('price_per_week')
        if price <= 0:
            raise forms.ValidationError("Price per week must be greater than zero.")
        return price

class VehicleRegistrationForm(forms.ModelForm):
    class Meta:
        model = VehicleRegistration
        fields = ['vehicle_number', 'rc_document']

