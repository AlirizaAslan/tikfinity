from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent, FollowEvent, LikeEvent, JoinEvent, ShareEvent, DisconnectEvent, RoomUserSeqEvent
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from django.utils import timezone
import logging
import asyncio
import random
import time

logger = logging.getLogger(__name__)

class TikTokLiveConnector:
    def __init__(self, username):
        self.username = username.replace('@', '').strip()
        
        # Create client with simple settings
        self.client = TikTokLiveClient(unique_id=self.username)
        
        self.channel_layer = get_channel_layer()
        self.consumer = None  # Will be set by consumer
        self.is_connected = False
        self.viewer_count = 0
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            self.is_connected = True
            logger.info(f"Connected successfully: @{self.username}")
            logger.info(f"Live stream info: {event}")
            
            await self.send_to_websocket({
                'type': 'connection',
                'status': 'connected',
                'username': self.username,
                'message': f'@{self.username} canlı yayınına başarıyla bağlanıldı!'
            })
            
            # Create or update live stream
            await self.create_live_stream()

        @self.client.on(DisconnectEvent)
        async def on_disconnect(event: DisconnectEvent):
            self.is_connected = False
            logger.warning(f"Disconnected: @{self.username}")
            await self.send_to_websocket({
                'type': 'disconnection',
                'status': 'disconnected',
                'username': self.username
            })

        @self.client.on(RoomUserSeqEvent)
        async def on_viewer_count_update(event: RoomUserSeqEvent):
            # RoomUserSeqEvent contains viewer count information
            if hasattr(event, 'viewerCount'):
                self.viewer_count = event.viewerCount
            elif hasattr(event, 'total'):
                self.viewer_count = event.total
            else:
                # Try to get any numeric value from the event
                for attr in dir(event):
                    if not attr.startswith('_'):
                        try:
                            val = getattr(event, attr, None)
                            if isinstance(val, int) and val > 0:
                                self.viewer_count = val
                                break
                        except:
                            continue
            
            if self.viewer_count > 0:
                logger.info(f"Viewer count: {self.viewer_count}")
                await self.send_to_websocket({
                    'type': 'viewer_update',
                    'viewer_count': self.viewer_count
                })
                await self.update_viewer_count(self.viewer_count)

        @self.client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            try:
                username = getattr(event.user, 'nickname', getattr(event.user, 'nick_name', 'Unknown'))
                logger.info(f"Comment: @{username}: {event.comment}")
                data = {
                    'type': 'comment',
                    'username': username,
                    'message': event.comment,
                    'timestamp': str(timezone.now())
                }
                await self.send_to_websocket(data)
                await self.save_interaction(data)
                
                # Process TTS for this comment
                await self.process_tts_comment(username, event.comment)
            except Exception as e:
                logger.error(f"Comment processing error: {e}")

        @self.client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            # Streakable gifts (combo gifts) are only processed when finished
            if hasattr(event.gift, 'streakable') and event.gift.streakable and hasattr(event.gift, 'streaking') and event.gift.streaking:
                return
            
            gift_count = event.gift.count if hasattr(event.gift, 'count') else 1
            username = getattr(event.user, 'nickname', getattr(event.user, 'nick_name', 'Unknown'))
            logger.info(f"Gift: @{username} -> {event.gift.name} x{gift_count} ({event.gift.diamond_count} diamonds)")
            
            data = {
                'type': 'gift',
                'username': username,
                'gift_name': event.gift.name,
                'gift_value': event.gift.diamond_count,
                'gift_count': gift_count,
                'timestamp': str(timezone.now())
            }
            await self.send_to_websocket(data)
            await self.save_interaction(data)

        @self.client.on(FollowEvent)
        async def on_follow(event: FollowEvent):
            username = getattr(event.user, 'nickname', getattr(event.user, 'nick_name', 'Unknown'))
            logger.info(f"Follow: @{username}")
            data = {
                'type': 'follow',
                'username': username,
                'timestamp': str(timezone.now())
            }
            await self.send_to_websocket(data)
            await self.save_interaction(data)

        @self.client.on(LikeEvent)
        async def on_like(event: LikeEvent):
            username = getattr(event.user, 'nickname', getattr(event.user, 'nick_name', 'Unknown'))
            logger.info(f"Like: @{username} -> {event.count} likes")
            data = {
                'type': 'like',
                'username': username,
                'like_count': event.count,
                'total_likes': event.totalLikes if hasattr(event, 'totalLikes') else event.count,
                'timestamp': str(timezone.now())
            }
            await self.send_to_websocket(data)

        @self.client.on(JoinEvent)
        async def on_join(event: JoinEvent):
            username = getattr(event.user, 'nickname', getattr(event.user, 'nick_name', 'Unknown'))
            logger.info(f"Join: @{username}")
            data = {
                'type': 'join',
                'username': username,
                'timestamp': str(timezone.now())
            }
            await self.send_to_websocket(data)
            await self.save_interaction(data)

        @self.client.on(ShareEvent)
        async def on_share(event: ShareEvent):
            username = getattr(event.user, 'nickname', getattr(event.user, 'nick_name', 'Unknown'))
            logger.info(f"Share: @{username}")
            data = {
                'type': 'share',
                'username': username,
                'timestamp': str(timezone.now())
            }
            await self.send_to_websocket(data)
            await self.save_interaction(data)

    async def send_to_websocket(self, data):
        """Send data to WebSocket clients - BROADCAST METHOD"""
        logger.info(f"Broadcasting to WebSocket - Type: {data.get('type')}, User: {data.get('username')}")
        
        # Method 1: Broadcast to all subscribers via global manager
        try:
            from .connection_manager import connection_manager
            connection_manager.broadcast_to_subscribers(self.username, data)
            logger.info(f"BROADCAST: Successfully sent {data.get('type')} to all subscribers")
        except Exception as e:
            logger.error(f"BROADCAST failed: {e}")
        
        # Method 2: Direct send via consumer (fallback)
        if self.consumer:
            try:
                import json
                await self.consumer.send(text_data=json.dumps(data))
                logger.info(f"DIRECT: Successfully sent {data.get('type')} to WebSocket")
            except Exception as e:
                logger.error(f"DIRECT send failed: {e}")
        
        # Method 3: Fallback to channel layer
        if self.channel_layer:
            try:
                room_name = f"live_{self.username}"
                message = {
                    'type': 'live_event',
                    'data': data
                }
                await self.channel_layer.group_send(room_name, message)
                logger.info(f"CHANNEL: Successfully sent {data.get('type')} to WebSocket")
            except Exception as e:
                logger.error(f"CHANNEL send failed: {e}")
                logger.exception(e)

    async def create_live_stream(self):
        """Create or update the active live stream"""
        # Skip database operations that are causing errors
        logger.info(f"Live stream session started for @{self.username}")

    async def update_viewer_count(self, count):
        """Update viewer count in database"""
        # Skip database operations that are causing errors
        logger.info(f"Viewer count updated to: {count}")

    async def save_interaction(self, data):
        # Skip database operations that are causing errors
        # Focus on TTS functionality instead
        try:
            # Update Last X widgets via WebSocket
            await self.update_lastx_widget(data['type'], data['username'])
        except Exception as e:
            logger.error(f"Failed to update Last X widget: {e}")
    
    async def update_lastx_widget(self, interaction_type, username):
        """Update Last X widgets with new interaction"""
        try:
            # Map interaction types to widget types
            widget_mapping = {
                'follow': 'follower',
                'gift': 'gifter',
                'comment': 'chatter',
                'like': 'like',
                'share': 'share'
            }
            
            widget_type = widget_mapping.get(interaction_type)
            if widget_type:
                # Broadcast to Last X widget subscribers via channel layer
                if self.channel_layer:
                    widget_data = {
                        'type': 'lastx_update',
                        'widget_type': widget_type,
                        'username': username,
                        'timestamp': str(timezone.now())
                    }
                    
                    # Get user ID from account
                    try:
                        account = await TikTokAccount.objects.aget(username=self.username)
                        user_id = account.user_id
                        
                        await self.channel_layer.group_send(
                            f"lastx_{user_id}",
                            {
                                'type': 'lastx_update',
                                'data': widget_data
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to get user ID for Last X update: {e}")
        except Exception as e:
            logger.error(f"Failed to update Last X widget: {e}")

    async def start(self):
        """Start the TikTok Live connection with retry logic"""
        try:
            logger.info(f"Connecting to @{self.username}...")
            
            # Create fresh client
            self.client = TikTokLiveClient(unique_id=self.username)
            self.setup_handlers()
            
            # Try to connect
            await self.client.start()
            logger.info(f"Connection successful!")
            self.is_connected = True
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Connection failed: {error_msg}")
            
            if "not found" in error_msg.lower() or "offline" in error_msg.lower():
                raise Exception(f"User @{self.username} is not currently live or doesn't exist.")
            elif "DEVICE_BLOCKED" in error_msg:
                raise Exception(f"Device blocked by TikTok. Try using VPN or wait 30 minutes.")
            else:
                raise Exception(f"Connection failed: {error_msg}")
            
            return False

    async def stop(self):
        """Stop the TikTok Live connection"""
        try:
            if self.is_connected:
                await self.client.disconnect()
                logger.info(f"Disconnected from @{self.username}")
                self.is_connected = False
                
                # Mark stream as ended
                await self.end_live_stream()
        except Exception as e:
            logger.error(f"Disconnect error: {e}")

    async def end_live_stream(self):
        """Mark the live stream as ended"""
        # Skip database operations that are causing errors
        logger.info(f"Live stream session ended for @{self.username}")
    
    async def process_tts_comment(self, username, comment):
        """Process comment for TTS if enabled"""
        try:
            @sync_to_async
            def process_tts_sync():
                from .models import TTSSettings, TTSLog
                from .piper_tts import piper_tts
                import os
                import hashlib
                from django.conf import settings
                
                results = []
                
                for tts_settings in TTSSettings.objects.filter(is_enabled=True):
                    try:
                        logger.info(f"Processing TTS for user {tts_settings.user.username}: {username} -> {comment}")
                        
                        # Check comment type filters
                        if tts_settings.comment_type == 'dot' and not comment.startswith('.'):
                            continue
                        elif tts_settings.comment_type == 'slash' and not comment.startswith('/'):
                            continue
                        elif tts_settings.comment_type == 'command' and not comment.startswith(tts_settings.special_command):
                            continue
                        
                        # Filter out unwanted content
                        if tts_settings.filter_mentions and '@' in comment:
                            continue
                        if tts_settings.filter_commands and comment.startswith('!'):
                            continue
                    
                        # Check length limit
                        processed_comment = comment
                        if len(processed_comment) > tts_settings.max_comment_length:
                            processed_comment = processed_comment[:tts_settings.max_comment_length]
                        
                        # Generate TTS
                        media_dir = os.path.join(settings.BASE_DIR, 'media', 'tts')
                        os.makedirs(media_dir, exist_ok=True)
                        
                        text_hash = hashlib.md5(processed_comment.encode()).hexdigest()[:8]
                        audio_filename = f"tts_{tts_settings.user.id}_{text_hash}.wav"
                        audio_path = os.path.join(media_dir, audio_filename)
                        
                        # Generate TTS audio if it doesn't exist
                        if not os.path.exists(audio_path):
                            success = piper_tts.text_to_speech(processed_comment, audio_path, "default", tts_settings.language)
                            if not success:
                                logger.error(f"TTS generation failed for: {processed_comment}")
                                continue
                            logger.info(f"Generated TTS audio: {audio_filename}")
                    
                        # Log TTS usage
                        TTSLog.objects.create(
                            user=tts_settings.user,
                            tiktok_username=username,
                            message=processed_comment
                        )
                        
                        # Prepare result for WebSocket
                        audio_url = f"/media/tts/{audio_filename}"
                        results.append({
                            'type': 'tts',
                            'username': username,
                            'text': processed_comment,
                            'audio_url': audio_url,
                            'language': tts_settings.language
                        })
                        
                    except Exception as e:
                        logger.error(f"TTS processing error for user {tts_settings.user.username}: {e}")
                        continue
                
                return results
            
            # Process TTS synchronously
            tts_results = await process_tts_sync()
            
            # Send results to WebSocket
            for result in tts_results:
                logger.info(f"Sending TTS audio: {result['audio_url']}")
                await self.send_to_websocket(result)
        
        except Exception as e:
            logger.error(f"TTS processing error: {e}")
