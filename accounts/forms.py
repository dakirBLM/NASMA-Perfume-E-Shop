# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True, label=_('Full name'))
    age = forms.IntegerField(required=False, label=_('Age'))
    phone = forms.CharField(max_length=20, required=False, label=_('Phone'))
    email = forms.EmailField(required=True, label=_('Email'))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'full_name', 'age', 'phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to form fields with translatable placeholders
        self.fields['username'].widget.attrs.update({'class': 'form-input', 'placeholder': _('Choose a username')})
        self.fields['email'].widget.attrs.update({'class': 'form-input', 'placeholder': _('Enter your email')})
        self.fields['password1'].widget.attrs.update({'class': 'form-input', 'placeholder': _('Enter password')})
        self.fields['password2'].widget.attrs.update({'class': 'form-input', 'placeholder': _('Confirm password')})
        self.fields['full_name'].widget.attrs.update({'class': 'form-input', 'placeholder': _('Enter your full name')})
        self.fields['age'].widget.attrs.update({'class': 'form-input', 'placeholder': _('Your age')})
        self.fields['phone'].widget.attrs.update({'class': 'form-input', 'placeholder': _('Phone number')})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("This email address is already registered."))
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_("This username is already taken."))
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Handle age conversion - empty string to None
            age = self.cleaned_data['age']
            age_value = age if age else None
            
            # Create UserProfile with all data
            UserProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                age=age_value,
                phone=self.cleaned_data['phone'],
            )
        
        return user