from django.urls import re_path
from . import consumers
from .tts_websocket import TTSWebSocketConsumer
from .lastx_websocket import LastXWebSocketConsumer

websocket_urlpatterns = [
    # Updated regex to support dots, underscores, hyphens in username
    re_path(r'ws/live/(?P<username>[\w.-]+)/$', consumers.LiveStreamConsumer.as_asgi()),
    re_path(r'ws/tts/(?P<username>[\w.-]+)/$', TTSWebSocketConsumer.as_asgi()),
    re_path(r'ws/lastx/(?P<user_id>\d+)/$', LastXWebSocketConsumer.as_asgi()),
]
