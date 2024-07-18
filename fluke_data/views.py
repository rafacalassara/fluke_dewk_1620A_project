# fluke_data/views.py
from django.shortcuts import render
from django.http import JsonResponse
from .visa_communication import Instrument

def index(request):
    return render(request, 'fluke_data/index.html')
