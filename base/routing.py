from django.urls import re_path
from .consumers import BaseConsumer

websocket_urlpatterns = [
    re_path(r"ws/base/(?P<token>[^/]+)/$", BaseConsumer.as_asgi()),
]
