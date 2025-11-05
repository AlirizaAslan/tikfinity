from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Updated regex to support dots, underscores, hyphens in username
    re_path(r'ws/live/(?P<username>[\w.-]+)/$', consumers.LiveStreamConsumer.as_asgi()),
]
