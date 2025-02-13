# fluke_data/routing.py
from django.urls import path

from .consumers import DataConsumer, ListenerConsumer

websocket_urlpatterns = [
    path('ws/data/<int:thermohygrometer_id>/', DataConsumer.as_asgi()),
    path('ws/listener/<int:thermohygrometer_id>/', ListenerConsumer.as_asgi()),
]
