# thermohygrometer_app/views.py

from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime
from .thermohygrometer import Thermohygrometer

def index(request):
    return render(request, 'thermohygrometer_app/index.html')

def get_real_time_data(request):
    ip_address = request.GET.get('ip')
    channel = request.GET.get('channel')
    delay = float(request.GET.get('delay', 1))

    device = Thermohygrometer(ip_address)
    response = device.connect()
    if not response:
        return JsonResponse({'error': 'Failed to connect to the device.'})

    data = device.read_real_time_data(channel, delay)
    device.disconnect()

    if data:
        return JsonResponse({'data': data})
    else:
        return JsonResponse({'error': 'Failed to read data from the device.'})
