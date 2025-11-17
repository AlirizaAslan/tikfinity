import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .connection_manager import connection_manager
import logging

logger = logging.getLogger(__name__)

class TTSWebSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        await self.accept()
        logger.info(f"TTS WebSocket connected for @{self.username}")
        
        # Use main connection manager for TTS
        user = self.scope['user']
        if user.is_authenticated:
            try:
                # Get or create connection through main manager
                connector = await connection_manager.get_or_create_connection(self.username, self)
                
                await self.send(text_data=json.dumps({
                    'type': 'connection',
                    'status': 'tiktok_connected',
                    'username': self.username,
                    'message': f'Connected to @{self.username} for TTS'
                }))
            except Exception as e:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Connection error: {str(e)}'
                }))
    
    async def disconnect(self, close_code):
        logger.info(f"TTS WebSocket disconnected for @{self.username}")
    
    async def send_tts_event(self, data):
        """Callback for TTS events"""
        await self.send(text_data=json.dumps(data))