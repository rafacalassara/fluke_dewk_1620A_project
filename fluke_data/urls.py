# fluke_data/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_thermohygrometers/', views.get_thermohygrometers, name='get_thermohygrometers'),
    path('manage_thermohygrometers/', views.manage_thermohygrometers, name='manage_thermohygrometers'),
    path('api/add_thermohygrometer/', views.add_thermohygrometer, name='add_thermohygrometer'),
    path('api/delete_thermohygrometer/<int:id>/', views.delete_thermohygrometer, name='delete_thermohygrometer'),
]
