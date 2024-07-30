# fluke_data/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/data/(?P<thermohygrometer_id>\d+)/$', consumers.DataConsumer.as_asgi()),
]
