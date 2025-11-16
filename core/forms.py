# core/forms.py - All forms in one place (corrected & complete)
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth import get_user_model
from .models import Review  # Only import what you need (no circular import with User)

User = get_user_model()  # This gets your CustomUser automatically


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com'
        })
    )
    mobile_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '10-digit mobile number (e.g. 9876543210)'
        })
    )
    is_rider = forms.BooleanField(required=False, initial=False)
    is_vehicle_provider = forms.BooleanField(required=False, initial=False)

    class Meta:
        model = User
        fields = ("username", "email", "mobile_number", "password1", "password2", "is_rider", "is_vehicle_provider")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })

    def clean(self):
        cleaned_data = super().clean()
        is_rider = cleaned_data.get("is_rider")
        is_vehicle_provider = cleaned_data.get("is_vehicle_provider")

        if is_rider and is_vehicle_provider:
            raise forms.ValidationError("You can select only one role: Rider or Vehicle Provider.")
        if not is_rider and not is_vehicle_provider:
            raise forms.ValidationError("You must select one role: Rider or Vehicle Provider.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        
        if commit:
            user.save()
            # Save extra fields to Profile (avoids circular import by local import)
            from .models import Profile
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    'mobile_number': self.cleaned_data["mobile_number"],
                    'is_rider': self.cleaned_data["is_rider"],
                    'is_vehicle_provider': self.cleaned_data["is_vehicle_provider"],
                }
            )
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'mobile_number', 'profile_image']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'Email Address'


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['name', 'rating', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name',
                'required': True
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience...',
                'required': True
            })
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is not None and (rating < 1 or rating > 5):
            raise forms.ValidationError("Rating must be between 1 and 5")
        return rating


class PasswordResetConfirmForm(forms.Form):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password'
        })
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password'
        })
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2