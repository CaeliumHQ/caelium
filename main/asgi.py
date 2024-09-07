import os
import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

django.setup()
from chats import routing

# Ensure the DJANGO_SETTINGS_MODULE environment variable is set
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")

# Initialize Django ASGI application early to ensure the settings are loaded

# Get the ASGI application
django_asgi_app = get_asgi_application()

# Define the application protocol type router
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(routing.websocket_urlpatterns)
        ),
    }
)