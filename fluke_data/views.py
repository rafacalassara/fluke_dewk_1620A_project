# fluke_data/views.py
from django.shortcuts import render
from .models import Thermohygrometer

def index(request):
    instruments = Thermohygrometer.objects.all()
    return render(request, 'fluke_data/index.html', {'instruments': instruments})
