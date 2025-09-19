from django import forms
from core.models import EBike, VehicleRegistration, ProviderDocument


class EBikeForm(forms.ModelForm):
    class Meta:
        model = EBike
        fields = ['name', 'description', 'price_per_day', 'price_per_week', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ebike name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter description'}),
            'price_per_day': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'price_per_week': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_price_per_day(self):
        price = self.cleaned_data.get('price_per_day')
        if price and price <= 0:
            raise forms.ValidationError("Price must be greater than 0")
        return price

    def clean_price_per_week(self):
        price = self.cleaned_data.get('price_per_week')
        if price and price <= 0:
            raise forms.ValidationError("Price must be greater than 0")
        return price


class VehicleRegistrationForm(forms.ModelForm):
    class Meta:
        model = VehicleRegistration
        fields = ['vehicle_number', 'rc_document']


class ProviderDocumentForm(forms.ModelForm):
    class Meta:
        model = ProviderDocument
        fields = ['document_type', 'document_file', 'document_number']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'document_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter document number (optional)'}),
        }

    def clean_document_file(self):
        file = self.cleaned_data.get('document_file')
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 5MB")
            
            # Check file extension
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
            file_extension = '.' + file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError("Only PDF, JPG, PNG, DOC, and DOCX files are allowed")
        
        return file


class DocumentVerificationForm(forms.ModelForm):
    class Meta:
        model = ProviderDocument
        fields = ['status', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter verification notes (optional)'}),
        }