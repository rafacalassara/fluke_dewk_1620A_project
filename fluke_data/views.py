# fluke_data/views.py
from collections import defaultdict
import json
import csv
from datetime import datetime, time, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Min, Max, Avg, F, Q
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.utils.timezone import make_aware

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
    thermohygrometers = ThermohygrometerModel.objects.all().filter(
        is_connected=True).order_by('instrument_name')
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
        # Generate group_name based on pn and sn
        group_name = f"thermo_{pn}_{sn}"

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
            selected_instrument = ThermohygrometerModel.objects.get(
                id=instrument_id)
            # Combine date and time into datetime objects
            try:
                start_datetime = datetime.strptime(
                    f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
                end_datetime = datetime.strptime(
                    f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

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
        selected_instrument = ThermohygrometerModel.objects.get(
            id=instrument_id)
        start_datetime = f"{start_date} {start_time}"
        end_datetime = f"{end_date} {end_time}"

        data = MeasuresModel.objects.filter(
            instrument=selected_instrument,
            date__range=[start_datetime, end_datetime]
        ).order_by('-date')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="measured_data_{selected_instrument.instrument_name}_{start_date}_{end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Temperature (°C)', 'Corrected Temperature (°C)',
                        'Humidity (%)', 'Corrected Humidity (%)'])

        for measure in data:
            writer.writerow([measure.date.strftime("%d/%m/%Y %H:%M"), measure.temperature,
                            measure.corrected_temperature, measure.humidity, measure.corrected_humidity])

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
            # Redirect after successful creation
            return redirect('manage_users')
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
            messages.error(
                request, 'Failed to update user. Please correct the errors below.')
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
            # Redirect to any view after successful login
            return redirect('real_time_data')
    else:
        form = CustomLoginForm()

    return render(request, 'fluke_data/login.html', {'form': form})


def intelligence2(request):
    # Buscar dados
    measures = MeasuresModel.objects.all().values(
        'id', 'temperature', 'humidity', 'date',
        'instrument_id', 'corrected_temperature',
        'corrected_humidity'
    )

    instruments = ThermohygrometerModel.objects.all().values(
        'id', 'instrument_name', 'group_name'
    )

    # Converter para JSON
    measures_json = json.dumps(list(measures), default=str)

    return render(request, 'fluke_data/intelligence2.html', {
        'measures': measures_json,
        'instruments': instruments,
    })


def out_of_limits_chart(request):
    form = AnalysisPeriodForm(request.GET or None)
    data = []
    total_time_available = 0
    analysis_period = ""
    # Armazena dados de temperatura por instrumento
    temperature_data = defaultdict(list)
    # Armazena dados de umidade por instrumento
    humidity_data = defaultdict(list)
    timestamps = set()                   # Conjunto para armazenar timestamps únicos

    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        start_time = form.cleaned_data['start_time']
        end_time = form.cleaned_data['end_time']

        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)

        analysis_period = f"{start_date.strftime('%d/%m/%Y')} {start_time.strftime('%H:%M')} - {end_date.strftime('%d/%m/%Y')} {end_time.strftime('%H:%M')}"

        delta_days = (end_date - start_date).days + 1
        weekdays = [
            start_date + timedelta(days=i) for i in range(delta_days)
            # Segunda a sexta-feira
            if (start_date + timedelta(days=i)).weekday() < 5
        ]
        total_time_available = len(
            weekdays) * ((end_time.hour - start_time.hour) + (end_time.minute - start_time.minute) / 60)

        instruments = ThermohygrometerModel.objects.all()

        for instrument in instruments:
            measures = MeasuresModel.objects.filter(
                instrument=instrument,
                date__range=(start_datetime, end_datetime),
                date__week_day__gte=2,  # Segunda (Django usa 2)
                date__week_day__lte=6,  # Sexta
                date__time__gte=start_time,
                date__time__lte=end_time
            ).order_by('date')

            temp_out = measures.filter(
                corrected_temperature__isnull=False
            ).filter(
                Q(corrected_temperature__lt=instrument.min_temperature) |
                Q(corrected_temperature__gt=instrument.max_temperature)
            ).count()

            humidity_out = measures.filter(
                corrected_humidity__isnull=False
            ).filter(
                Q(corrected_humidity__lt=instrument.min_humidity) |
                Q(corrected_humidity__gt=instrument.max_humidity)
            ).count()

            total_time_out = ((temp_out + humidity_out) *
                              instrument.time_interval_to_save_measures) / 60
            percent_out_of_limits = (
                total_time_out / total_time_available) * 100 if total_time_available > 0 else 0

            data.append({
                'instrument_name': instrument.instrument_name,
                'percent_out_of_limits': percent_out_of_limits,
            })

            # Organizar dados para gráficos de linha
            for measure in measures:
                timestamp = measure.date.strftime('%Y-%m-%d %H:%M')
                # Adiciona timestamp à lista
                timestamps.add(timestamp)

                # Adiciona temperatura apenas se não for nula
                if measure.corrected_temperature is not None:
                    temperature_data[instrument.instrument_name].append({
                        'timestamp': timestamp,
                        'value': measure.corrected_temperature
                    })

                # Adiciona umidade apenas se não for nula
                if measure.corrected_humidity is not None:
                    humidity_data[instrument.instrument_name].append({
                        'timestamp': timestamp,
                        'value': measure.corrected_humidity
                    })

    context = {
        'form': form,
        'data': data,
        'total_time_available': total_time_available,
        'analysis_period': analysis_period,
        'temperature_data': dict(temperature_data),
        'humidity_data': dict(humidity_data),
        'timestamps': sorted(timestamps)  # Lista de timestamps ordenados
    }
    return render(request, 'fluke_data/intelligence.html', context)


@login_required
@user_passes_test(is_manager)
def delete_certificate(request, cert_pk):
    certificate = get_object_or_404(CalibrationCertificateModel, pk=cert_pk)
    thermohygrometer = ThermohygrometerModel.objects.filter(
        calibration_certificate=certificate).first()

    if thermohygrometer:
        thermohygrometer.calibration_certificate = None
        thermohygrometer.save()

    certificate.delete()
    messages.success(request, 'Certificate deleted successfully.')
    return redirect('manage_thermohygrometers')


@login_required
@user_passes_test(is_manager)
def manage_all_certificates(request):
    certificates = CalibrationCertificateModel.objects.all().order_by('-calibration_date')

    if request.method == 'POST':
        form = CalibrationCertificateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Certificate added successfully.')
            return redirect('manage_all_certificates')
    else:
        form = CalibrationCertificateForm()

    return render(request, 'fluke_data/certificate/manage_all_certificates.html', {
        'certificates': certificates,
        'form': form
    })


@login_required
@user_passes_test(is_manager)
def create_certificate(request):
    if request.method == 'POST':
        form = CalibrationCertificateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Certificate created successfully.')
            return redirect('manage_all_certificates')
    else:
        form = CalibrationCertificateForm()

    return render(request, 'fluke_data/certificate/create_certificate.html', {
        'form': form
    })


def carrega_pagina_inteligencia(request):
    pass  # TODO: Implementar a lógica para carregar a página de inteligência
    # fazer chamada para o LLM


def fazer_chamada_para_llm(request):
    pass  # TODO: Implementar a lógica para fazer a chamada para o LLM


def ai_analysis(request):
    form = AnalysisRequestForm()
    results = None
    error = None

    if request.method == 'POST':
        form = AnalysisRequestForm(request.POST)
        if form.is_valid():
            try:
                start = form.cleaned_data['start_datetime']
                end = form.cleaned_data['end_datetime']
                instruments = form.cleaned_data['instruments']

                # Filter measures for workdays (Monday-Friday)
                measures = MeasuresModel.objects.filter(
                    instrument__in=instruments,
                    date__range=(start, end),
                    # Monday(2) to Friday(6)
                    date__week_day__in=[2, 3, 4, 5, 6],
                    corrected_temperature__isnull=False,
                    corrected_humidity__isnull=False
                ).order_by('date')

                # Prepare data for AI analysis
                analysis_data = [{
                    'timestamp': m.date.isoformat(),
                    'temperature': m.corrected_temperature,
                    'humidity': m.corrected_humidity,
                    'instrument': m.instrument.instrument_name
                } for m in measures]

                # Store data in session for AI processing
                request.session['analysis_data'] = analysis_data
                return redirect('analyze_with_ai')

            except Exception as e:
                error = f"Erro ao recuperar dados: {str(e)}"

    return render(request, 'fluke_data/ai_analysis.html', {
        'form': form,
        'error': error
    })


@csrf_exempt
def analyze_with_ai(request):
    if request.method == 'POST':
        try:
            data = request.session.get('analysis_data', [])

            if not data:
                return JsonResponse({'error': 'No data to analyze'}, status=400)

            # TODO: Implement OpenAI API call
            # Example structure:
            """
            openai.api_key = "SUA_CHAVE_API"
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{
                    "role": "user",
                    "content": f"Analise estes dados de termohigrômetros: {json.dumps(data)}. Forneça insights sobre tendências, anomalias e recomendações."
                }]
            )
            
            analysis = response.choices[0].message.content
            """

            # Temporary mock response
            analysis = "Análise simulada:\n- Padrões estáveis de temperatura\n- Pico de umidade detectado em 2023-05-15"

            return JsonResponse({'analysis': analysis})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'fluke_data/ai_analysis_results.html')


json={
    'titulo':'',
    'resumo':'',
    'analise':'',
    'sugestoes':'',
    'conclusao':''
}