# fluke_data/views.py
import json
import csv
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Min, Max, Avg
from django.utils.dateparse import parse_datetime

from .models import *
from .visa_communication import Instrument

def real_time_data(request):
    return render(request, 'fluke_data/real_time_data.html')

def get_thermohygrometers(request):
    thermohygrometers = ThermohygrometerModel.objects.all().order_by('instrument_name')
    data = [
        {
            'id': thermo.id,
            'pn': thermo.pn,
            'sn': thermo.sn,
            'instrument_name': thermo.instrument_name
        }
    for thermo in thermohygrometers]
    return JsonResponse(data, safe=False)

def manage_thermohygrometers(request):
    thermohygrometers = ThermohygrometerModel.objects.all().order_by('instrument_name')
    return render(request, 'fluke_data/manage_thermohygrometers.html', {'thermohygrometers': thermohygrometers})


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

        try:
            if instrument_ip and pn and sn:
                ThermohygrometerModel.objects.create(
                    ip_address = instrument_ip,
                    instrument_name=name,
                    pn=pn,
                    sn=sn
                )
                return JsonResponse({'success': True})
        except:
            return JsonResponse({'success': False, 'error': 'Error adding on database.'})

        instrument.disconnect()
    
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
            start_datetime = f"{start_date} {start_time}"
            end_datetime = f"{end_date} {end_time}"

            data = MeasuresModel.objects.filter(
                instrument=selected_instrument,
                date__range=[start_datetime, end_datetime]
            ).order_by('-date')

            stats = data.aggregate(
                min_temperature=Min('temperature'),
                max_temperature=Max('temperature'),
                avg_temperature=Avg('temperature'),
                min_humidity=Min('humidity'),
                max_humidity=Max('humidity'),
                avg_humidity=Avg('humidity'),
            )

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
        writer.writerow(['Date', 'Temperature (°C)', 'Humidity (%)'])

        for measure in data:
            writer.writerow([measure.date.strftime("%d/%m/%Y %H:%M"), measure.temperature, measure.humidity])

        return response

    return HttpResponse("No data to export")