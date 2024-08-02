# fluke_data/routing.py
from django.urls import path
from .consumers import DataConsumer

websocket_urlpatterns = [
    path('ws/data/<int:thermohygrometer_id>/', DataConsumer.as_asgi()),
]
