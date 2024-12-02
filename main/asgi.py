import os
import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Ensure the DJANGO_SETTINGS_MODULE environment variable is set
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")

# Initialize Django ASGI application early to ensure the settings are loaded
django.setup()

# Import routing after Django setup
from chats import routing as chats_routing
from base import routing as base_routing

# Combine websocket_urlpatterns from both apps
websocket_urlpatterns = base_routing.websocket_urlpatterns + chats_routing.websocket_urlpatterns

# Get the ASGI application
django_asgi_app = get_asgi_application()

# Define the application protocol type router
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
