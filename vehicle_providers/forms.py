from django import forms
from core.models import EBike, VehicleRegistration, ProviderDocument, Withdrawal,Booking
from django.db.models import Sum


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


class WithdrawalForm(forms.ModelForm):
    TRANSFER_TYPE_CHOICES = [
        ('bank', 'Bank Transfer'),
        ('upi', 'UPI Transfer'),
    ]
    
    transfer_type = forms.ChoiceField(
        choices=TRANSFER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='bank'
    )
    
    class Meta:
        model = Withdrawal
        fields = ['amount', 'account_holder_name', 'account_number', 'ifsc_code', 'bank_name', 'upi_id']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'min': '1'}),
            'account_holder_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter account holder name'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter account number'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'IFSC code', 'style': 'text-transform: uppercase;'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank name'}),
            'upi_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UPI ID (e.g., name@paytm)'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.provider = kwargs.pop('provider', None)
        super().__init__(*args, **kwargs)

        # ALL optional by default (we control validation in clean())
        for field in ['account_holder_name', 'account_number', 'ifsc_code', 'bank_name', 'upi_id']:
            self.fields[field].required = False
        
        if self.provider:
            from decimal import Decimal
            bookings = Booking.objects.filter(ebike__provider=self.provider, is_approved=True)
            total_earnings = sum(float(b.total_price) for b in bookings)
            platform_charges = total_earnings * 0.1
            self.available_balance = Decimal(str(total_earnings - platform_charges))
            
            completed_withdrawals = Withdrawal.objects.filter(
                provider=self.provider,
                status__in=['approved', 'completed']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.0')
            
            self.available_balance -= completed_withdrawals
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")
        
        if self.provider and hasattr(self, 'available_balance'):
            if amount > self.available_balance:
                raise forms.ValidationError(f"Insufficient balance. Available: ₹{self.available_balance:.2f}")
        
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        transfer_type = self.data.get('transfer_type', 'bank')

        # BANK MODE VALIDATION
        if transfer_type == 'bank':
            bank_required = ['account_holder_name', 'account_number', 'ifsc_code', 'bank_name']
            for field in bank_required:
                if not cleaned_data.get(field):
                    self.add_error(field, "This field is required for bank transfer.")

        # UPI MODE VALIDATION
        elif transfer_type == 'upi':
            if not cleaned_data.get('upi_id'):
                self.add_error('upi_id', "UPI ID is required for UPI transfer.")

            # Make sure bank fields are NOT treated as required
            cleaned_data['account_holder_name'] = cleaned_data.get('account_holder_name', '')
            cleaned_data['account_number'] = cleaned_data.get('account_number', '')
            cleaned_data['ifsc_code'] = cleaned_data.get('ifsc_code', '')
            cleaned_data['bank_name'] = cleaned_data.get('bank_name', '')

        else:
            raise forms.ValidationError("Invalid transfer type selected.")

        return cleaned_data
