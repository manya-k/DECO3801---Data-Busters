# memory_sim/asgi.py
"""
ASGI entrypoint for MemorySim.
- Serves normal Django HTTP via get_asgi_application()
- Serves WebSockets for the single-room storyline via Channels
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

# IMPORTANT: point to your settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "memory_sim.settings")

# Standard Django ASGI application (HTTP)
django_asgi_app = get_asgi_application()

# WebSocket consumer (you'll create api/consumers.py as discussed)
from api.consumers import StoryConsumer  # noqa: E402  (import after DJANGO_SETTINGS_MODULE)

application = ProtocolTypeRouter({
    # HTTP is handled by Django as usual
    "http": django_asgi_app,

    # WebSocket routes handled by Channels
    "websocket": URLRouter([
        # Single-room realtime endpoint (anonymous players)
        path("ws/storyline/", StoryConsumer.as_asgi()),
    ]),
})
