from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent, FollowEvent, LikeEvent, JoinEvent, ShareEvent, DisconnectEvent, RoomUserSeqEvent
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
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
            logger.info(f"Comment: @{event.user.nickname}: {event.comment}")
            data = {
                'type': 'comment',
                'username': event.user.nickname,
                'message': event.comment,
                'timestamp': str(timezone.now())
            }
            await self.send_to_websocket(data)
            await self.save_interaction(data)

        @self.client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            # Streakable gifts (combo gifts) are only processed when finished
            if hasattr(event.gift, 'streakable') and event.gift.streakable and not event.gift.streaking:
                return
            
            gift_count = event.gift.count if hasattr(event.gift, 'count') else 1
            logger.info(f"Gift: @{event.user.nickname} -> {event.gift.name} x{gift_count} ({event.gift.diamond_count} diamonds)")
            
            data = {
                'type': 'gift',
                'username': event.user.nickname,
                'gift_name': event.gift.name,
                'gift_value': event.gift.diamond_count,
                'gift_count': gift_count,
                'timestamp': str(timezone.now())
            }
            await self.send_to_websocket(data)
            await self.save_interaction(data)

        @self.client.on(FollowEvent)
        async def on_follow(event: FollowEvent):
            logger.info(f"Follow: @{event.user.nickname}")
            data = {
                'type': 'follow',
                'username': event.user.nickname,
                'timestamp': str(timezone.now())
            }
            await self.send_to_websocket(data)
            await self.save_interaction(data)

        @self.client.on(LikeEvent)
        async def on_like(event: LikeEvent):
            logger.info(f"Like: @{event.user.nickname} -> {event.count} likes")
            data = {
                'type': 'like',
                'username': event.user.nickname,
                'like_count': event.count,
                'total_likes': event.totalLikes if hasattr(event, 'totalLikes') else event.count,
                'timestamp': str(timezone.now())
            }
            await self.send_to_websocket(data)

        @self.client.on(JoinEvent)
        async def on_join(event: JoinEvent):
            logger.info(f"Join: @{event.user.nickname}")
            data = {
                'type': 'join',
                'username': event.user.nickname,
                'timestamp': str(timezone.now())
            }
            await self.send_to_websocket(data)
            await self.save_interaction(data)

        @self.client.on(ShareEvent)
        async def on_share(event: ShareEvent):
            logger.info(f"Share: @{event.user.nickname}")
            data = {
                'type': 'share',
                'username': event.user.nickname,
                'timestamp': str(timezone.now())
            }
            await self.send_to_websocket(data)
            await self.save_interaction(data)

    async def send_to_websocket(self, data):
        """Send data to WebSocket clients - DIRECT METHOD"""
        logger.info(f"📤 Sending to WebSocket - Type: {data.get('type')}, User: {data.get('username')}")
        
        # Method 1: Direct send via consumer (FASTEST)
        if self.consumer:
            try:
                import json
                await self.consumer.send(text_data=json.dumps(data))
                logger.info(f"✅ DIRECT: Successfully sent {data.get('type')} to WebSocket")
                return
            except Exception as e:
                logger.error(f"❌ DIRECT send failed: {e}")
        
        # Method 2: Fallback to channel layer
        if self.channel_layer:
            try:
                room_name = f"live_{self.username}"
                message = {
                    'type': 'live_event',
                    'data': data
                }
                await self.channel_layer.group_send(room_name, message)
                logger.info(f"✅ CHANNEL: Successfully sent {data.get('type')} to WebSocket")
            except Exception as e:
                logger.error(f"❌ CHANNEL send failed: {e}")
                logger.exception(e)
        else:
            logger.error("❌ No consumer or channel layer available!")

    async def create_live_stream(self):
        """Create or update the active live stream"""
        from .models import LiveStream, TikTokAccount
        from django.utils import timezone
        
        try:
            account = await TikTokAccount.objects.aget(username=self.username)
            stream, created = await LiveStream.objects.aget_or_create(
                account=account,
                is_active=True,
                defaults={'stream_id': f"{self.username}_{timezone.now().timestamp()}"}
            )
            if created:
                logger.info(f"New live stream created: {stream.stream_id}")
            else:
                logger.info(f"Using existing live stream: {stream.stream_id}")
        except Exception as e:
            logger.error(f"Failed to create live stream: {e}")

    async def update_viewer_count(self, count):
        """Update viewer count in database"""
        from .models import LiveStream, TikTokAccount
        
        try:
            account = await TikTokAccount.objects.aget(username=self.username)
            stream = await LiveStream.objects.filter(
                account=account,
                is_active=True
            ).afirst()
            
            if stream:
                stream.viewer_count = count
                # Update peak viewers if current count is higher
                if count > stream.peak_viewers:
                    stream.peak_viewers = count
                await stream.asave()
        except Exception as e:
            logger.error(f"Failed to update viewer count: {e}")

    async def save_interaction(self, data):
        from .models import Interaction, LiveStream, TikTokAccount
        from django.utils import timezone
        
        try:
            account = await TikTokAccount.objects.aget(username=self.username)
            stream = await LiveStream.objects.filter(
                account=account, 
                is_active=True
            ).afirst()
            
            if stream:
                # Save interaction
                await Interaction.objects.acreate(
                    stream=stream,
                    interaction_type=data['type'],
                    username=data['username'],
                    message=data.get('message', ''),
                    gift_name=data.get('gift_name', ''),
                    gift_value=data.get('gift_value', 0)
                )
                
                # Update stream statistics
                if data['type'] == 'comment':
                    stream.total_comments += 1
                elif data['type'] == 'gift':
                    stream.total_gifts += 1
                elif data['type'] == 'like':
                    stream.total_likes += data.get('like_count', 1)
                elif data['type'] == 'share':
                    stream.total_shares += 1
                
                await stream.asave()
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")

    async def start(self):
        """Start the TikTok Live connection with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to @{self.username}... (Attempt {attempt + 1}/{max_retries})")
                logger.info(f"Make sure the user is currently live!")
                
                # Add random delay to avoid pattern detection
                if attempt > 0:
                    delay = retry_delay * (attempt + random.uniform(0.5, 1.5))
                    logger.info(f"Waiting {delay:.1f} seconds before retry...")
                    await asyncio.sleep(delay)
                
                # Try to connect
                await self.client.connect()
                logger.info(f"Connection successful!")
                self.is_connected = True
                return
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Connection attempt {attempt + 1} failed: {error_msg}")
                
                # Check if it's a device block error
                if "DEVICE_BLOCKED" in error_msg:
                    if attempt < max_retries - 1:
                        logger.warning("Device blocked by TikTok. Retrying with different session...")
                        # Recreate client with new session
                        self.client = TikTokLiveClient(unique_id=self.username)
                        self.setup_handlers()
                        continue
                    else:
                        logger.error("SOLUTION: Your IP/device is temporarily blocked by TikTok.")
                        logger.error("Try these solutions:")
                        logger.error("  1. Wait 30-60 minutes before trying again")
                        logger.error("  2. Use a different network/VPN")
                        logger.error("  3. Try from a different device")
                        logger.error("  4. Check if the user is actually live on TikTok")
                        raise Exception(f"TikTok blocked connection: Device/IP blocked. Please wait or change network.")
                
                elif "not found" in error_msg.lower() or "offline" in error_msg.lower():
                    raise Exception(f"User @{self.username} is not currently live or doesn't exist.")
                
                # For other errors, retry
                if attempt == max_retries - 1:
                    logger.error("All connection attempts failed.")
                    logger.error(f"Possible reasons:")
                    logger.error(f"   1. User @{self.username} is not currently live")
                    logger.error(f"   2. Username is incorrect")
                    logger.error(f"   3. Network/firewall issues")
                    logger.error(f"   4. TikTok API rate limiting")
                    raise Exception(f"Failed to connect after {max_retries} attempts: {error_msg}")

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
        from .models import LiveStream, TikTokAccount
        from django.utils import timezone
        
        try:
            account = await TikTokAccount.objects.aget(username=self.username)
            stream = await LiveStream.objects.filter(
                account=account,
                is_active=True
            ).afirst()
            
            if stream:
                stream.is_active = False
                stream.ended_at = timezone.now()
                await stream.asave()
                logger.info(f"Live stream ended: {stream.stream_id}")
        except Exception as e:
            logger.error(f"Failed to end live stream: {e}")
