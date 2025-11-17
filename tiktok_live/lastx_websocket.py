import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging

logger = logging.getLogger(__name__)

class LastXWebSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f"lastx_{self.user_id}"
        
        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Last X WebSocket connected for user {self.user_id}")
    
    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"Last X WebSocket disconnected for user {self.user_id}")
    
    async def lastx_update(self, event):
        """Send Last X update to WebSocket"""
        await self.send(text_data=json.dumps(event['data']))