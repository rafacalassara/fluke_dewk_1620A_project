# fluke_data/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.display_measures, name='display_measures'),
    path('get_thermohygrometers/', views.get_thermohygrometers, name='get_thermohygrometers'),
    path('get_connected_thermohygrometers/', views.get_connected_thermohygrometers, name='get_connected_thermohygrometers'),
    path('manage_thermohygrometers/', views.manage_thermohygrometers, name='manage_thermohygrometers'),
    path('api/add_thermohygrometer/', views.add_thermohygrometer, name='add_thermohygrometer'),
    path('api/delete_thermohygrometer/<int:id>/', views.delete_thermohygrometer, name='delete_thermohygrometer'),
    path('data_visualization/', views.data_visualization, name='data_visualization'),
    path('export-to-csv/', views.export_to_csv, name='export_to_csv'),
    path('real_time_data/', views.real_time_data, name='real_time_data'),
]
