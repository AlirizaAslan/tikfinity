from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, DisconnectEvent
import asyncio
import logging
import os
import hashlib
from django.conf import settings
from .models import TTSSettings, TTSLog
from .piper_tts import piper_tts

logger = logging.getLogger(__name__)

class TTSLiveConnector:
    def __init__(self, username, user):
        self.username = username.replace('@', '').strip()
        self.user = user
        self.client = TikTokLiveClient(unique_id=self.username)
        self.is_connected = False
        self.websocket_callback = None
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.client.on(ConnectEvent)
        async def on_connect(event):
            self.is_connected = True
            logger.info(f"TTS Connected to @{self.username}")
            if self.websocket_callback:
                await self.websocket_callback({
                    'type': 'connection',
                    'status': 'tiktok_connected',
                    'username': self.username,
                    'message': f'Connected to @{self.username}'
                })
        
        @self.client.on(DisconnectEvent)
        async def on_disconnect(event):
            self.is_connected = False
            logger.info(f"TTS Disconnected from @{self.username}")
            if self.websocket_callback:
                await self.websocket_callback({
                    'type': 'connection',
                    'status': 'disconnected',
                    'username': self.username
                })
        
        @self.client.on(CommentEvent)
        async def on_comment(event):
            try:
                # Handle different attribute names for username
                username = 'Unknown'
                if hasattr(event.user, 'nickname'):
                    username = event.user.nickname
                elif hasattr(event.user, 'nick_name'):
                    username = event.user.nick_name
                elif hasattr(event.user, 'display_name'):
                    username = event.user.display_name
                
                logger.info(f"TTS Comment: @{username}: {event.comment}")
                await self.process_tts_comment(username, event.comment)
            except Exception as e:
                logger.error(f"TTS comment processing error: {e}")
                # Continue processing even if user info fails
                try:
                    await self.process_tts_comment('Unknown', event.comment)
                except:
                    pass
    
    async def process_tts_comment(self, username, comment):
        try:
            # Get TTS settings for this user
            tts_settings = await TTSSettings.objects.aget(user=self.user)
            if not tts_settings.is_enabled:
                return
            
            # Check comment type filters
            if tts_settings.comment_type == 'dot' and not comment.startswith('.'):
                return
            elif tts_settings.comment_type == 'slash' and not comment.startswith('/'):
                return
            elif tts_settings.comment_type == 'command' and not comment.startswith(tts_settings.special_command):
                return
            
            # Filter unwanted content
            if tts_settings.filter_mentions and '@' in comment:
                return
            if tts_settings.filter_commands and comment.startswith('!'):
                return
            
            # Check length limit
            if len(comment) > tts_settings.max_comment_length:
                comment = comment[:tts_settings.max_comment_length]
            
            # Generate TTS
            media_dir = os.path.join(settings.BASE_DIR, 'media', 'tts')
            os.makedirs(media_dir, exist_ok=True)
            
            text_hash = hashlib.md5(comment.encode()).hexdigest()[:8]
            audio_filename = f"tts_{self.user.id}_{text_hash}.wav"
            audio_path = os.path.join(media_dir, audio_filename)
            
            if not os.path.exists(audio_path):
                success = piper_tts.text_to_speech(comment, audio_path, "default", tts_settings.language)
                if not success:
                    logger.error(f"TTS generation failed for: {comment}")
                    return
            
            # Log TTS usage
            await TTSLog.objects.acreate(
                user=self.user,
                tiktok_username=username,
                message=comment
            )
            
            # Send TTS event
            audio_url = f"/media/tts/{audio_filename}"
            if self.websocket_callback:
                await self.websocket_callback({
                    'type': 'tts',
                    'username': username,
                    'text': comment,
                    'audio_url': audio_url
                })
            
        except Exception as e:
            logger.error(f"TTS processing error: {e}")
    
    async def start(self):
        try:
            await self.client.connect()
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    async def stop(self):
        try:
            if self.is_connected:
                await self.client.disconnect()
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
    
    def set_websocket_callback(self, callback):
        self.websocket_callback = callback

# Global TTS connections
tts_connections = {}

async def get_tts_connection(username, user):
    key = f"{user.id}_{username}"
    if key not in tts_connections:
        tts_connections[key] = TTSLiveConnector(username, user)
    return tts_connections[key]

async def stop_tts_connection(username, user):
    key = f"{user.id}_{username}"
    if key in tts_connections:
        await tts_connections[key].stop()
        del tts_connections[key]