# fluke_data/views.py
from django.shortcuts import render
from django.http import JsonResponse
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
