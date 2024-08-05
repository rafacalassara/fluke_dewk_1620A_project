# fluke_data/views.py
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pyvisa import errors

from .models import ThermohygrometerModel
from .visa_communication import Instrument

def real_time_data(request):
    return render(request, 'fluke_data/real_time_data.html')

def get_thermohygrometers(request):
    thermohygrometers = ThermohygrometerModel.objects.all()
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
    thermohygrometers = ThermohygrometerModel.objects.all()
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

