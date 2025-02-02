"""
ASGI config for alpha project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import sqms_apps.routing  # Pastikan aplikasi dan routing sudah terimpor dengan benar

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alpha.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            sqms_apps.routing.websocket_urlpatterns
        )
    ),
})
