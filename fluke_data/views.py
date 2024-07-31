# fluke_data/views.py
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import ThermohygrometerModel

def index(request):
    return render(request, 'fluke_data/index.html')

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
        instrument_name = data.get('instrument_name')
        pn = data.get('pn')
        sn = data.get('sn')
        if instrument_name and pn and sn:
            ThermohygrometerModel.objects.create(instrument_name=instrument_name, pn=pn, sn=sn)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Missing fields'})

@csrf_exempt
def delete_thermohygrometer(request, id):
    if request.method == 'DELETE':
        try:
            thermo = ThermohygrometerModel.objects.get(id=id)
            thermo.delete()
            return JsonResponse({'success': True})
        except ThermohygrometerModel.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Thermohygrometer not found'})

