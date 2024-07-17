from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_real_time_data/', views.get_real_time_data, name='get_real_time_data'),
]
