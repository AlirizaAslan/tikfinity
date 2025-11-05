import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .live_connector import TikTokLiveConnector
import logging

logger = logging.getLogger(__name__)

class LiveStreamConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = None
        self.connector = None
        self.room_group_name = None

    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        self.room_group_name = f'live_{self.username}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        logger.info(f"✅ WebSocket connected: @{self.username}")
        logger.info(f"📡 Room group: {self.room_group_name}")
        logger.info(f"📱 Channel name: {self.channel_name}")
        
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'status': 'websocket_connected',
            'message': 'WebSocket connected, connecting to TikTok...'
        }))

        try:
            self.connector = TikTokLiveConnector(self.username)
            
            # CRITICAL: Pass the consumer instance to connector for direct messaging
            self.connector.consumer = self
            
            await self.connector.start()
            
            logger.info(f"✅ TikTok connection successful: @{self.username}")
            await self.send(text_data=json.dumps({
                'type': 'connection',
                'status': 'tiktok_connected',
                'message': f'Successfully connected to TikTok @{self.username} live stream!',
                'username': self.username
            }))
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            error_message = str(e)
            
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': error_message,
                'details': [
                    f"Failed to connect to @{self.username}",
                    "Please check:",
                    "   1. Is the user currently live?",
                    "   2. Is the username correct?",
                    "   3. Is your internet connection active?"
                ]
            }))

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnecting: @{self.username}")
        
        if self.connector:
            await self.connector.stop()
            self.connector = None

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            command = data.get('command')

            if command == 'start_stream':
                await self.start_stream()
            elif command == 'stop_stream':
                await self.stop_stream()
            elif command == 'reconnect':
                await self.reconnect_stream()
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Command error: {str(e)}'
            }))

    async def live_event(self, event):
        """Forward live events to WebSocket client"""
        data = event.get('data', event)
        logger.info(f"live_event called - Type: {data.get('type')}, User: {data.get('username')}")
        logger.info(f"Full event data: {event}")
        
        try:
            json_data = json.dumps(data)
            logger.info(f"Sending JSON to WebSocket: {json_data}")
            await self.send(text_data=json_data)
            logger.info(f"✅ Successfully sent {data.get('type')} event to WebSocket client")
        except Exception as e:
            logger.error(f"❌ Failed to send event to WebSocket client: {e}")
            logger.exception(e)

    async def start_stream(self):
        if not self.connector:
            try:
                self.connector = TikTokLiveConnector(self.username)
                await self.connector.start()
                await self.send(text_data=json.dumps({
                    'type': 'connection',
                    'status': 'started',
                    'message': f'Stream started: @{self.username}'
                }))
            except Exception as e:
                logger.error(f"Stream start error: {e}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Failed to start stream: {str(e)}'
                }))

    async def stop_stream(self):
        if self.connector:
            await self.connector.stop()
            self.connector = None
            await self.send(text_data=json.dumps({
                'type': 'connection',
                'status': 'stopped',
                'message': 'Stream stopped'
            }))

    async def reconnect_stream(self):
        """Reconnect to TikTok Live stream"""
        if self.connector:
            await self.connector.stop()
            self.connector = None
        
        await self.start_stream()
