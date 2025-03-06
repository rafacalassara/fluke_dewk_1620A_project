# fluke/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm
)

from .models import CalibrationCertificateModel, SensorModel, ThermohygrometerModel

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
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name', 'username', 'email',
                  'password1', 'password2', 'is_manager']
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
        fields = ['name', 'username', 'email',
                  'first_name', 'last_name', 'is_manager']
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
            self.add_error('new_password2',
                           "The two password fields didn't match.")

        return cleaned_data


class ThermohygrometerForm(forms.ModelForm):
    calibration_certificate = forms.ModelChoiceField(
        queryset=CalibrationCertificateModel.objects.all(),
        required=False,
        empty_label="No certificate",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Certificate",
        to_field_name="id"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the certificate choices to show certificate number
        self.fields['calibration_certificate'].label_from_instance = lambda obj: obj.certificate_number

    class Meta:
        model = ThermohygrometerModel
        fields = [
            'instrument_name', 'ip_address',
            'time_interval_to_save_measures',
            'pn', 'sn',
            'group_name', 'calibration_certificate',
            'min_temperature', 'max_temperature',
            'min_humidity', 'max_humidity',
        ]
        widgets = {
            'instrument_name': forms.TextInput(attrs={'class': 'form-control'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control'}),
            'time_interval_to_save_measures': forms.TextInput(attrs={'class': 'form-control'}),
            'pn': forms.TextInput(attrs={'class': 'form-control'}),
            'sn': forms.TextInput(attrs={'class': 'form-control'}),
            'group_name': forms.TextInput(attrs={'class': 'form-control'}),
            'calibration_certificate': forms.TextInput(attrs={'class': 'form-control'}),
            'min_temperature': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Temperature (°C)'}),
            'max_temperature': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max Temperature (°C)'}),
            'min_humidity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Humidity (%)'}),
            'max_humidity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max Humidity (%)'}),
        }


class CalibrationCertificateForm(forms.ModelForm):
    class Meta:
        model = CalibrationCertificateModel
        fields = [
            'certificate_number',
            'calibration_date',
            'next_calibration_date',
            'temp_indication_point_1',
            'temp_correction_1',
            'temp_indication_point_2',
            'temp_correction_2',
            'temp_indication_point_3',
            'temp_correction_3',
            'humidity_indication_point_1',
            'humidity_correction_1',
            'humidity_indication_point_2',
            'humidity_correction_2',
            'humidity_indication_point_3',
            'humidity_correction_3',
            'temp_uncertainty',
            'humidity_uncertainty',
        ]
        widgets = {
            'certificate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'calibration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'next_calibration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'temp_indication_point_1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'temp_correction_1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'temp_indication_point_2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'temp_correction_2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'temp_indication_point_3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'temp_correction_3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'humidity_indication_point_1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'humidity_correction_1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'humidity_indication_point_2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'humidity_correction_2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'humidity_indication_point_3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'humidity_correction_3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'temp_uncertainty': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'humidity_uncertainty': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
        }


class AnalysisPeriodForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date'}), label="Data inicial")
    end_date = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date'}), label="Data final")
    start_time = forms.TimeField(widget=forms.TimeInput(
        attrs={'type': 'time'}), label="Hora inicial")
    end_time = forms.TimeField(widget=forms.TimeInput(
        attrs={'type': 'time'}), label="Hora final")


class EnvironmentalAnalysisForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}),
        label='Data Inicial'
    )
    end_date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}),
        label='Data Final'
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={'type': 'time', 'class': 'form-control'}),
        initial='08:00',
        label='Horário Inicial'
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={'type': 'time', 'class': 'form-control'}),
        initial='16:00',
        label='Horário Final'
    )
    instruments = forms.ModelMultipleChoiceField(
        queryset=ThermohygrometerModel.objects.all().order_by('instrument_name'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        label='Instrumentos'
    )

    class Meta:
        field_order = ['start_date', 'end_date',
                       'start_time', 'end_time', 'instruments']


class SensorForm(forms.ModelForm):
    class Meta:
        model = SensorModel
        fields = [
            'sensor_name', 'location', 'channel',
            'sensor_pn', 'sensor_sn', 'calibration_certificate',
            'min_temperature', 'max_temperature',
            'min_humidity', 'max_humidity',
        ]
        widgets = {
            'sensor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'channel': forms.Select(attrs={'class': 'form-control'}),
            'sensor_pn': forms.TextInput(attrs={'class': 'form-control'}),
            'sensor_sn': forms.TextInput(attrs={'class': 'form-control'}),
            'calibration_certificate': forms.Select(attrs={'class': 'form-control'}),
            'min_temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'max_temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'min_humidity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'max_humidity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }
