from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from core.models import User


class SignUpForm(UserCreationForm):
    model=User
    email = forms.EmailField(
        max_length=254, 
        required=True, 
        help_text='Required. Enter a valid email address.',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    
    mobile_number = forms.CharField(
        max_length=15, 
        required=True, 
        help_text='Required. Enter your mobile number.',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'})
    )
    
    is_rider = forms.BooleanField(
        required=False, 
        help_text='Check if you want to register as a rider.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_vehicle_provider = forms.BooleanField(
        required=False, 
        help_text='Check if you want to register as a vehicle provider.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User  # Reference to your custom User model
        fields = ('username', 'email', 'mobile_number', 'password1', 'password2', 'is_rider', 'is_vehicle_provider')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'profile_image']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }