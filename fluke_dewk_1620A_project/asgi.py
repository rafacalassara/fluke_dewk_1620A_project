# fluke_dewk_1620A_project/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import fluke_data.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluke_dewk_1620A_project.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            fluke_data.routing.websocket_urlpatterns
        )
    ),
})
