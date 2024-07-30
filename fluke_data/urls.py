# fluke_data/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_thermohygrometers/', views.get_thermohygrometers, name='get_thermohygrometers'),
]
