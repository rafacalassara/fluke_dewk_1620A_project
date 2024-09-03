# fluke/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm, PasswordChangeForm
from .models import ThermohygrometerModel

User = get_user_model()

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'name', 'email', 'is_manager', 'password']
        widgets = {
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_manager': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'username': None,
            'name': None,
            'email': None,
            'password': None,
            'is_manager': None,
        }

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name', 'username', 'email', 'password1', 'password2', 'is_manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            'is_manager': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class UpdateUserForm(UserChangeForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['name', 'username', 'email', 'first_name', 'last_name', 'is_manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'is_manager': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password1 != new_password2:
            self.add_error('new_password2', "The two password fields didn't match.")
        
        return cleaned_data

class ThermohygrometerForm(forms.ModelForm):
    class Meta:
        model = ThermohygrometerModel
        fields = ['instrument_name', 'ip_address', 'pn', 'sn', 'sensor_sn', 'sensor_pn', 'group_name']
        widgets = {
            'instrument_name': forms.TextInput(attrs={'class': 'form-control'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control'}),
            'pn': forms.TextInput(attrs={'class': 'form-control'}),
            'sn': forms.TextInput(attrs={'class': 'form-control'}),
            'sensor_sn': forms.TextInput(attrs={'class': 'form-control'}),
            'sensor_pn': forms.TextInput(attrs={'class': 'form-control'}),
            'group_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
