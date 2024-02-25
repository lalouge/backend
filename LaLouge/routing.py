from django.urls import re_path, path

from utilities.websockets.device import DeviceConsumer
from utilities.websockets.errors import ErrorDisplayConsumer


websocket_urlpatterns = [
    path('ws/device_tokens/<str:user_query_id>/', DeviceConsumer.as_asgi()),
    path('ws/errors/<str:user_query_id>/', ErrorDisplayConsumer.as_asgi()),
]