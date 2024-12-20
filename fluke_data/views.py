# fluke_data/views.py
import json, csv
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Min, Max, Avg
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password

from .forms import *
from .models import *
from .visa_communication import Instrument

User = get_user_model()
# Check if the user is a manager

def is_manager(user):
    return user.is_manager

@login_required
@user_passes_test(is_manager)
def real_time_data(request):
    return render(request, 'fluke_data/real_time_data.html')

def get_thermohygrometers(request):
    thermohygrometers = ThermohygrometerModel.objects.all().order_by('instrument_name')
    data = [
        {
            'id': thermo.id,
            'pn': thermo.pn,
            'sn': thermo.sn,
            'instrument_name': thermo.instrument_name,
            'group_name': thermo.group_name,
        }
    for thermo in thermohygrometers]
    return JsonResponse(data, safe=False)

def get_connected_thermohygrometers(request):
    thermohygrometers = ThermohygrometerModel.objects.all().filter(is_connected=True).order_by('instrument_name')
    data = [
        {
            'id': thermo.id,
            'pn': thermo.pn,
            'sn': thermo.sn,
            'instrument_name': thermo.instrument_name,
            'group_name': thermo.group_name,
        }
    for thermo in thermohygrometers]
    return JsonResponse(data, safe=False)

@login_required
@user_passes_test(is_manager)
def manage_thermohygrometers(request):
    thermohygrometers = ThermohygrometerModel.objects.all().order_by('instrument_name')
    return render(request, 'fluke_data/manage_thermohygrometers.html', {'thermohygrometers': thermohygrometers})

@login_required
@user_passes_test(is_manager)
def update_thermohygrometer(request, pk):
    thermohygrometer = get_object_or_404(ThermohygrometerModel, pk=pk)
    if request.method == 'POST':
        form = ThermohygrometerForm(request.POST, instance=thermohygrometer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thermohygrometer updated successfully.')
            return redirect('manage_thermohygrometers')
    else:
        form = ThermohygrometerForm(instance=thermohygrometer)
    return render(request, 'fluke_data/thermohygrometer/update_thermohygrometer.html', {'form': form, 'thermohygrometer': thermohygrometer})

@login_required
@user_passes_test(is_manager)
@csrf_exempt
def add_thermohygrometer(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        instrument_ip = data.get('instrument_ip')
        try:
            instrument = Instrument(ip_address=instrument_ip)
            instrument.connect()
        except:
            return JsonResponse({'success': False, 'error': 'Instrument not found on given IP address.'})
        
        name = instrument.INSTRUMENT_NAME
        pn = instrument.PN
        sn = instrument.SN
        group_name = f"thermo_{pn}_{sn}"  # Generate group_name based on pn and sn

        try:
            if instrument_ip and pn and sn:
                ThermohygrometerModel.objects.create(
                    ip_address=instrument_ip,
                    instrument_name=name,
                    pn=pn,
                    sn=sn,
                    group_name=group_name  # Save the group_name
                )
                return JsonResponse({'success': True})
        except:
            return JsonResponse({'success': False, 'error': 'Error adding to database.'})

        instrument.disconnect()

@login_required
@user_passes_test(is_manager)    
@csrf_exempt
def delete_thermohygrometer(request, id):
    if request.method == 'DELETE':
        try:
            thermo = ThermohygrometerModel.objects.get(id=id)
            thermo.delete()
            return JsonResponse({'success': True})
        except ThermohygrometerModel.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Thermohygrometer not found'})
        
def data_visualization(request):
    thermohygrometers = ThermohygrometerModel.objects.all().order_by('instrument_name')
    data = []
    selected_instrument = None
    stats = None
    
    if request.method == 'POST':
        instrument_id = request.POST.get('instrument')
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')
        end_date = request.POST.get('end_date')
        end_time = request.POST.get('end_time')

        if instrument_id and start_date and start_time and end_date and end_time:
            selected_instrument = ThermohygrometerModel.objects.get(id=instrument_id)
             # Combine date and time into datetime objects
            try:
                start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
                end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

                data = MeasuresModel.objects.filter(
                    instrument=selected_instrument,
                    date__range=[start_datetime, end_datetime]
                ).order_by('-date')

                try:
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
                except:
                    stats = data.aggregate(
                        min_temperature=Min('temperature'),
                        corrected_min_temperature='No Calibration Certificate',
                        max_temperature=Max('temperature'),
                        corrected_max_temperature='No Calibration Certificate',
                        avg_temperature=Avg('temperature'),
                        corrected_avg_temperature='No Calibration Certificate',
                        min_humidity=Min('humidity'),
                        corrected_min_humidity='No Calibration Certificate',
                        max_humidity=Max('humidity'),
                        corrected_max_humidity='No Calibration Certificate',
                        avg_humidity=Avg('humidity'),
                        corrected_avg_humidity='No Calibration Certificate',
                    )
            except ValueError:
                # Handle invalid date format
                return render(request, 'fluke_data/data_visualization.html', {
                    'thermohygrometers': thermohygrometers,
                    'error': 'Invalid date or time format.',
                })
            
        context = {
            'thermohygrometers': thermohygrometers,
            'data': data,
            'selected_instrument': selected_instrument,
            'start_date': start_date,
            'start_time': start_time,
            'end_date': end_date,
            'end_time': end_time,
            'stats': stats,
        }
        return render(request, 'fluke_data/data_visualization.html', context)

    context = {
        'thermohygrometers': thermohygrometers,
    }
    return render(request, 'fluke_data/data_visualization.html', context)

def export_to_csv(request):
    instrument_id = request.POST.get('instrument_id')
    start_date = request.POST.get('start_date')
    start_time = request.POST.get('start_time')
    end_date = request.POST.get('end_date')
    end_time = request.POST.get('end_time')

    if instrument_id and start_date and start_time and end_date and end_time:
        selected_instrument = ThermohygrometerModel.objects.get(id=instrument_id)
        start_datetime = f"{start_date} {start_time}"
        end_datetime = f"{end_date} {end_time}"

        data = MeasuresModel.objects.filter(
            instrument=selected_instrument,
            date__range=[start_datetime, end_datetime]
        ).order_by('-date')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="measured_data_{selected_instrument.instrument_name}_{start_date}_{end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Temperature (°C)','Corrected Temperature (°C)', 'Humidity (%)', 'Corrected Humidity (%)' ])

        for measure in data:
            writer.writerow([measure.date.strftime("%d/%m/%Y %H:%M"), measure.temperature, measure.corrected_temperature, measure.humidity, measure.corrected_humidity])

        return response

    return HttpResponse("No data to export")

def display_measures(request):
    thermohygrometers = ThermohygrometerModel.objects.all().order_by('instrument_name')
    thermohygrometer_data = [
        {
            'id': thermo.id,
            'pn': thermo.pn,
            'sn': thermo.sn,
            'instrument_name': thermo.instrument_name,
            'group_name': thermo.group_name,  # Ensure the group_name is passed
        }
        for thermo in thermohygrometers
    ]
    return render(request, 'fluke_data/display_measures.html', {'thermohygrometers': thermohygrometers})

@login_required
@user_passes_test(is_manager)
def manage_users(request):
    users = User.objects.all()
    return render(request, 'fluke_data/user/manage_users.html', {'users': users})

@login_required
@user_passes_test(is_manager)
def create_user(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_users')  # Redirect after successful creation
    else:
        form = CreateUserForm()
    return render(request, 'fluke_data/user/create_user.html', {'form': form})

@login_required
@user_passes_test(is_manager)
def update_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UpdateUserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            new_password = form.cleaned_data.get('new_password1')
            if new_password:
                user.password = make_password(new_password)
            user.save()
            messages.success(request, 'User updated successfully.')
            return redirect('manage_users')
        else:
            messages.error(request, 'Failed to update user. Please correct the errors below.')
    else:
        form = UpdateUserForm(instance=user)
    return render(request, 'fluke_data/user/update_user.html', {'form': form})

@login_required
@user_passes_test(is_manager)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('manage_users')  # Redirect after successful deletion
    return render(request, 'fluke_data/user/delete_user.html', {'user': user})

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('real_time_data')  # Redirect to any view after successful login
    else:
        form = CustomLoginForm()

    return render(request, 'fluke_data/login.html', {'form': form})
