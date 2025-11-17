from TikTokLive import TikTokLiveClient
from TikTokLive.events import *
import asyncio
import logging
from .models import Action, Event, StreamInteraction, LiveStream, UserPoints, PointsTransaction

logger = logging.getLogger(__name__)

class TikTokLiveConnector:
    def __init__(self, username, user_id):
        self.username = username
        self.user_id = user_id
        self.client = TikTokLiveClient(unique_id=username)
        self.is_connected = False
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Setup event handlers for TikTok Live events"""
        
        @self.client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            logger.info(f"Connected to @{event.unique_id} (Room ID: {event.room_id})")
            self.is_connected = True
        
        @self.client.on(DisconnectEvent)
        async def on_disconnect(event: DisconnectEvent):
            logger.info("Disconnected from TikTok Live")
            self.is_connected = False
        
        @self.client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            await self.handle_comment(event)
        
        @self.client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            await self.handle_gift(event)
        
        @self.client.on(FollowEvent)
        async def on_follow(event: FollowEvent):
            await self.handle_follow(event)
        
        @self.client.on(ShareEvent)
        async def on_share(event: ShareEvent):
            await self.handle_share(event)
        
        @self.client.on(LikeEvent)
        async def on_like(event: LikeEvent):
            await self.handle_like(event)
        
        @self.client.on(JoinEvent)
        async def on_join(event: JoinEvent):
            await self.handle_join(event)
    
    async def handle_comment(self, event: CommentEvent):
        """Handle comment events"""
        try:
            # Save interaction
            await self.save_interaction('comment', event.user, event.comment)
            
            # Check for custom commands
            if event.comment.startswith('!') or event.comment.startswith('/'):
                await self.check_command_events(event.user, event.comment)
            
            logger.info(f"Comment from @{event.user.unique_id}: {event.comment}")
        except Exception as e:
            logger.error(f"Error handling comment: {e}")
    
    async def handle_gift(self, event: GiftEvent):
        """Handle gift events"""
        try:
            # Save interaction
            await self.save_interaction('gift', event.user, '', 
                                      gift_name=event.gift.name,
                                      gift_count=event.gift.count,
                                      gift_value=event.gift.diamond_count)
            
            # Award points
            await self.award_points(event.user.unique_id, 'gift', event.gift.diamond_count)
            
            # Check gift events
            await self.check_gift_events(event.user, event.gift)
            
            logger.info(f"Gift from @{event.user.unique_id}: {event.gift.name} x{event.gift.count}")
        except Exception as e:
            logger.error(f"Error handling gift: {e}")
    
    async def handle_follow(self, event: FollowEvent):
        """Handle follow events"""
        try:
            # Save interaction
            await self.save_interaction('follow', event.user)
            
            # Award points
            await self.award_points(event.user.unique_id, 'follow', 50)
            
            # Check follow events
            await self.check_follow_events(event.user)
            
            logger.info(f"New follower: @{event.user.unique_id}")
        except Exception as e:
            logger.error(f"Error handling follow: {e}")
    
    async def handle_share(self, event: ShareEvent):
        """Handle share events"""
        try:
            # Save interaction
            await self.save_interaction('share', event.user)
            
            # Award points
            await self.award_points(event.user.unique_id, 'share', 25)
            
            # Check share events
            await self.check_share_events(event.user)
            
            logger.info(f"Share from @{event.user.unique_id}")
        except Exception as e:
            logger.error(f"Error handling share: {e}")
    
    async def handle_like(self, event: LikeEvent):
        """Handle like events"""
        try:
            # Save interaction
            await self.save_interaction('like', event.user)
            
            # Award points
            await self.award_points(event.user.unique_id, 'like', 1)
            
            # Check like events (batch processing)
            await self.check_like_events(event.user, event.count)
            
            logger.info(f"Likes from @{event.user.unique_id}: {event.count}")
        except Exception as e:
            logger.error(f"Error handling like: {e}")
    
    async def handle_join(self, event: JoinEvent):
        """Handle user join events"""
        try:
            # Save interaction
            await self.save_interaction('join', event.user)
            
            logger.info(f"User joined: @{event.user.unique_id}")
        except Exception as e:
            logger.error(f"Error handling join: {e}")
    
    async def save_interaction(self, interaction_type, user, message='', **kwargs):
        """Save interaction to database"""
        try:
            # Get or create live stream
            stream, created = await LiveStream.objects.aget_or_create(
                account__username=self.username,
                is_active=True,
                defaults={'stream_id': f"{self.username}_{timezone.now().timestamp()}"}
            )
            
            # Create interaction
            await StreamInteraction.objects.acreate(
                stream=stream,
                interaction_type=interaction_type,
                username=user.unique_id,
                display_name=user.display_name or user.unique_id,
                message=message,
                gift_name=kwargs.get('gift_name', ''),
                gift_count=kwargs.get('gift_count', 1),
                gift_value=kwargs.get('gift_value', 0)
            )
        except Exception as e:
            logger.error(f"Error saving interaction: {e}")
    
    async def award_points(self, username, transaction_type, points):
        """Award points to user"""
        try:
            user_points, created = await UserPoints.objects.aget_or_create(
                user_id=self.user_id,
                tiktok_username=username,
                defaults={'points_total': 0, 'level': 1}
            )
            
            user_points.points_total += points
            user_points.points_level += points
            
            # Level up check
            if user_points.points_level >= 100:
                user_points.level += 1
                user_points.points_level = 0
            
            await user_points.asave()
            
            # Create transaction record
            await PointsTransaction.objects.acreate(
                user_points=user_points,
                transaction_type=transaction_type,
                points_change=points
            )
        except Exception as e:
            logger.error(f"Error awarding points: {e}")
    
    async def check_follow_events(self, user):
        """Check and trigger follow events"""
        events = Event.objects.filter(
            user_id=self.user_id,
            trigger_type='follow',
            is_active=True
        )
        
        async for event in events:
            if await self.user_matches_event(user, event):
                await self.execute_event_actions(event, user)
    
    async def check_gift_events(self, user, gift):
        """Check and trigger gift events"""
        events = Event.objects.filter(
            user_id=self.user_id,
            trigger_type='gift',
            is_active=True
        )
        
        async for event in events:
            if await self.user_matches_event(user, event):
                # Check gift conditions
                if event.specific_gift and event.specific_gift != gift.name:
                    continue
                if gift.diamond_count < event.min_coins:
                    continue
                
                await self.execute_event_actions(event, user, gift=gift)
    
    async def check_like_events(self, user, like_count):
        """Check and trigger like events"""
        events = Event.objects.filter(
            user_id=self.user_id,
            trigger_type='like',
            is_active=True
        )
        
        async for event in events:
            if await self.user_matches_event(user, event):
                if like_count >= event.min_likes:
                    await self.execute_event_actions(event, user, like_count=like_count)
    
    async def check_share_events(self, user):
        """Check and trigger share events"""
        events = Event.objects.filter(
            user_id=self.user_id,
            trigger_type='share',
            is_active=True
        )
        
        async for event in events:
            if await self.user_matches_event(user, event):
                await self.execute_event_actions(event, user)
    
    async def check_command_events(self, user, command):
        """Check and trigger custom command events"""
        events = Event.objects.filter(
            user_id=self.user_id,
            trigger_type='command',
            is_active=True
        )
        
        async for event in events:
            if event.custom_command and command.startswith(event.custom_command):
                if await self.user_matches_event(user, event):
                    await self.execute_event_actions(event, user, command=command)
    
    async def user_matches_event(self, user, event):
        """Check if user matches event criteria"""
        if event.user_type == 'any':
            return True
        elif event.user_type == 'specific':
            return user.unique_id == event.specific_user
        elif event.user_type == 'topgifter':
            # Check if user is in top gifters (simplified)
            return True  # Implement top gifter logic
        
        return False
    
    async def execute_event_actions(self, event, user, **kwargs):
        """Execute actions for triggered event"""
        try:
            actions = event.actions.all()
            async for action in actions:
                await self.execute_action(action, user, **kwargs)
        except Exception as e:
            logger.error(f"Error executing event actions: {e}")
    
    async def execute_action(self, action, user, **kwargs):
        """Execute a specific action"""
        try:
            # This would integrate with your overlay system
            # For now, just log the action
            logger.info(f"Executing action '{action.name}' for user @{user.unique_id}")
            
            # Here you would:
            # 1. Send action data to overlay screens
            # 2. Play sounds/videos
            # 3. Show animations
            # 4. Send TTS messages
            # 5. Trigger webhooks
            # etc.
            
        except Exception as e:
            logger.error(f"Error executing action: {e}")
    
    async def start(self):
        """Start the TikTok Live connection"""
        try:
            await self.client.start()
        except Exception as e:
            logger.error(f"Error starting TikTok Live client: {e}")
            raise
    
    async def stop(self):
        """Stop the TikTok Live connection"""
        try:
            await self.client.stop()
        except Exception as e:
            logger.error(f"Error stopping TikTok Live client: {e}")
    
    def is_live(self):
        """Check if currently connected to live stream"""
        return self.is_connected