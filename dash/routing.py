from django.urls import re_path
from .consumers import BaseConsumer

websocket_urlpatterns = [
    re_path(r"ws/dash/(?P<token>[^/]+)/$", BaseConsumer.as_asgi()),
]
