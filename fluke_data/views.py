# fluke_data/views.py
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Max, Min
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView,
    ListView, TemplateView,
    UpdateView
)

from .forms import *
from .models import *

User = get_user_model()
# Check if the user is a manager


def is_manager(user):
    return user.is_manager


class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_manager


class RealTimeDataView(LoginRequiredMixin, ManagerRequiredMixin, TemplateView):
    template_name = 'fluke_data/real_time_data.html'


class ManageThermohygrometersView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = ThermohygrometerModel
    template_name = 'fluke_data/manage_thermohygrometers.html'
    context_object_name = 'thermohygrometers'
    ordering = ['instrument_name']


class UpdateThermohygrometerView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = ThermohygrometerModel
    form_class = ThermohygrometerForm
    template_name = 'fluke_data/thermohygrometer/update_thermohygrometer.html'
    success_url = reverse_lazy('manage_thermohygrometers')

    def form_valid(self, form):
        messages.success(
            self.request, 'Thermohygrometer updated successfully.')
        return super().form_valid(form)


class DataVisualizationView(TemplateView):
    template_name = 'fluke_data/data_visualization.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thermohygrometers = ThermohygrometerModel.objects.all().order_by('instrument_name')
        context['thermohygrometers'] = thermohygrometers
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        instrument_id = request.POST.get('instrument')
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')
        end_date = request.POST.get('end_date')
        end_time = request.POST.get('end_time')

        if all([instrument_id, start_date, start_time, end_date, end_time]):
            selected_instrument = ThermohygrometerModel.objects.get(
                id=instrument_id)
            try:
                start_datetime = datetime.strptime(
                    f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
                end_datetime = datetime.strptime(
                    f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

                data = MeasuresModel.objects.filter(
                    instrument=selected_instrument,
                    date__range=[start_datetime, end_datetime]
                ).order_by('-date')

                stats = data.aggregate(
                    min_temperature=Min('temperature'),
                    corrected_min_temperature=Min('corrected_temperature'),
                    max_temperature=Max('temperature'),
                    corrected_max_temperature=Max('corrected_temperature'),
                    avg_temperature=Avg('temperature'),
                    corrected_avg_temperature=Avg('corrected_temperature'),
                    min_humidity=Min('humidity'),
                    corrected_min_humidity=Min('corrected_humidity'),
                    max_humidity=Max('humidity'),
                    corrected_max_humidity=Max('corrected_humidity'),
                    avg_humidity=Avg('humidity'),
                    corrected_avg_humidity=Avg('corrected_humidity'),
                )

                context.update({
                    'data': data,
                    'selected_instrument': selected_instrument,
                    'start_date': start_date,
                    'start_time': start_time,
                    'end_date': end_date,
                    'end_time': end_time,
                    'stats': stats,
                })
            except ValueError:
                context['error'] = 'Invalid date or time format.'

        return self.render_to_response(context)


class DisplayMeasuresView(TemplateView):
    template_name = 'fluke_data/display_measures.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thermohygrometers = ThermohygrometerModel.objects.all().order_by('instrument_name')
        context['thermohygrometers'] = thermohygrometers
        return context


class ManageUsersView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = User
    template_name = 'fluke_data/user/manage_users.html'
    context_object_name = 'users'


class CreateUserView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = User
    form_class = CreateUserForm
    template_name = 'fluke_data/user/create_user.html'
    success_url = reverse_lazy('manage_users')


class UpdateUserView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = User
    form_class = UpdateUserForm
    template_name = 'fluke_data/user/update_user.html'
    success_url = reverse_lazy('manage_users')

    def form_valid(self, form):
        user = form.save(commit=False)
        new_password = form.cleaned_data.get('new_password1')
        if new_password:
            user.password = make_password(new_password)
        user.save()
        messages.success(self.request, 'User updated successfully.')
        return super().form_valid(form)


class DeleteUserView(LoginRequiredMixin, ManagerRequiredMixin, DeleteView):
    model = User
    template_name = 'fluke_data/user/delete_user.html'
    success_url = reverse_lazy('manage_users')


class LoginView(TemplateView):
    template_name = 'fluke_data/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CustomLoginForm()
        return context

    def post(self, request, *args, **kwargs):
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('real_time_data')
        return self.render_to_response({'form': form})


class ManageCertificatesView(LoginRequiredMixin, ManagerRequiredMixin, TemplateView):
    template_name = 'fluke_data/certificate/manage_all_certificates.html'


class IntelligenceView(LoginRequiredMixin, ManagerRequiredMixin, TemplateView):
    template_name = 'fluke_data/intelligence.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = EnvironmentalAnalysisForm(self.request.GET or None)
        return context


class CreateCertificateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = CalibrationCertificateModel
    form_class = CalibrationCertificateForm
    template_name = 'fluke_data/certificate/create_certificate.html'
    success_url = reverse_lazy('manage_all_certificates')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Certificate created successfully.')
        return response
