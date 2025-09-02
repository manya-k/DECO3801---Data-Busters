# api/consumers.py
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .game_state import get_state, submit_choice

class StoryConsumer(AsyncJsonWebsocketConsumer):
    """
    Single-room, anonymous consumer.
    Frontend should send:
      {action:"ready"}                # optional, you can ignore for now
      {action:"choose", choice:"yes"} # records a choice
    On every message (or join), we send current state.
    """

    group_name = "story_MUSEUM"  # single room

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        # Sync this client
        await self.send_json({**get_state(), "type": "state"})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        if action == "choose":
            # anonymous client id = channel name (good enough)
            choice = str(content.get("choice", "")).lower()
            if choice:
                # Default to 2 players; you can pass players:1 from client later if needed
                submit_choice(client_id=self.channel_name, choice=choice, connected_players_hint=2)
        # After any action, broadcast updated state to everyone
        await self.channel_layer.group_send(self.group_name, {"type": "rebroadcast"})

    async def rebroadcast(self, event):
        await self.send_json({**get_state(), "type": "state"})
