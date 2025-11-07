from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class TikTokAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200, blank=True)
    profile_picture = models.URLField(blank=True)
    follower_count = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    is_live = models.BooleanField(default=False)
    
    # OAuth tokens
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Stream control settings
    enable_monitoring = models.BooleanField(default=True)
    enable_auto_response = models.BooleanField(default=False)
    enable_automation = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"@{self.username}"

class LiveStream(models.Model):
    account = models.ForeignKey(TikTokAccount, on_delete=models.CASCADE)
    stream_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=500, blank=True)
    viewer_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.account.username} - {self.title}"

class StreamInteraction(models.Model):
    INTERACTION_TYPES = [
        ('comment', 'Comment'),
        ('like', 'Like'),
        ('gift', 'Gift'),
        ('follow', 'Follow'),
        ('share', 'Share'),
        ('join', 'Join'),
    ]
    
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    username = models.CharField(max_length=100)
    display_name = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
    gift_name = models.CharField(max_length=100, blank=True)
    gift_count = models.IntegerField(default=1)
    gift_value = models.IntegerField(default=0)  # in coins
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} - {self.interaction_type}"

class AutomationTrigger(models.Model):
    TRIGGER_TYPES = [
        ('keyword', 'Keyword in Comment'),
        ('gift_received', 'Gift Received'),
        ('follower_milestone', 'Follower Milestone'),
        ('viewer_milestone', 'Viewer Milestone'),
        ('like_milestone', 'Like Milestone'),
    ]
    
    ACTION_TYPES = [
        ('auto_reply', 'Auto Reply'),
        ('play_sound', 'Play Sound'),
        ('show_alert', 'Show Alert'),
        ('change_scene', 'Change OBS Scene'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    trigger_type = models.CharField(max_length=30, choices=TRIGGER_TYPES)
    trigger_value = models.CharField(max_length=500)  # keyword, gift name, milestone number
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    action_value = models.TextField()  # reply message, sound file, alert text, scene name
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class AutoResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trigger_keywords = models.TextField(help_text="Comma-separated keywords")
    response_message = models.TextField()
    is_active = models.BooleanField(default=True)
    cooldown_seconds = models.IntegerField(default=30)
    last_triggered = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Auto Response: {self.trigger_keywords[:50]}"

class UserPoints(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tiktok_username = models.CharField(max_length=100)
    tiktok_user_id = models.CharField(max_length=100, blank=True)
    display_name = models.CharField(max_length=200, blank=True)
    profile_picture = models.URLField(blank=True)
    points_total = models.IntegerField(default=0)
    points_level = models.IntegerField(default=0)  # Points counted towards level
    level = models.IntegerField(default=1)
    total_gifts_sent = models.IntegerField(default=0)
    total_coins_spent = models.IntegerField(default=0)
    first_activity = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'tiktok_username']
    
    def __str__(self):
        return f"{self.tiktok_username} - {self.points_total} points"

class PointsTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('gift', 'Gift Received'),
        ('follow', 'Follow'),
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('manual', 'Manual Adjustment'),
        ('bonus', 'Bonus Points'),
        ('penalty', 'Penalty'),
    ]
    
    user_points = models.ForeignKey(UserPoints, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    points_change = models.IntegerField()
    description = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user_points.tiktok_username} - {self.points_change} points"

class PointsSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    max_users = models.IntegerField(default=2500)
    points_per_gift = models.IntegerField(default=10)
    points_per_follow = models.IntegerField(default=50)
    points_per_like = models.IntegerField(default=1)
    points_per_comment = models.IntegerField(default=5)
    points_per_share = models.IntegerField(default=25)
    level_up_threshold = models.IntegerField(default=100)
    enable_points_system = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Points Settings - {self.user.username}"

class Widget(models.Model):
    WIDGET_TYPES = [
        ('goal', 'Goal Widget'),
        ('top_gifts', 'Top Gifts'),
        ('top_streaks', 'Top Streaks'),
        ('gift_counter', 'Gift Counter'),
        ('last_x', 'Last X Events'),
        ('activity_feed', 'Activity Feed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    widget_id = models.UUIDField(default=uuid.uuid4, unique=True)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    title = models.CharField(max_length=200)
    settings = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} ({self.widget_type})"

# Actions & Events Models
class Action(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    screen = models.CharField(max_length=50, default='Screen 1')
    duration = models.IntegerField(default=5)  # seconds
    points_change = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    
    # Action types
    has_animation = models.BooleanField(default=False)
    has_picture = models.BooleanField(default=False)
    has_sound = models.BooleanField(default=False)
    has_video = models.BooleanField(default=False)
    
    # Media files
    animation_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    audio_url = models.URLField(blank=True)
    video_url = models.URLField(blank=True)
    
    # Text and TTS
    text_content = models.TextField(blank=True)
    text_color = models.CharField(max_length=7, default='#FFFFFF')
    tts_text = models.TextField(blank=True)
    tts_voice = models.CharField(max_length=50, default='default')
    
    # Settings
    volume = models.IntegerField(default=100)
    cooldown_global = models.IntegerField(default=0)  # seconds
    cooldown_user = models.IntegerField(default=0)  # seconds
    enable_fade = models.BooleanField(default=True)
    enable_streak = models.BooleanField(default=False)
    skip_on_next = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Event(models.Model):
    TRIGGER_CHOICES = [
        ('follow', 'Follow'),
        ('like', 'Like'),
        ('gift', 'Gift'),
        ('subscribe', 'Subscribe / Super Fan'),
        ('command', 'Custom Command'),
        ('share', 'Share'),
    ]
    
    USER_CHOICES = [
        ('any', 'Any'),
        ('specific', 'Specific User'),
        ('topgifter', 'Top Gifters'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    # Trigger settings
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_CHOICES)
    user_type = models.CharField(max_length=20, choices=USER_CHOICES, default='any')
    specific_user = models.CharField(max_length=100, blank=True)
    
    # Trigger conditions
    min_coins = models.IntegerField(default=1)
    min_likes = models.IntegerField(default=100)
    custom_command = models.CharField(max_length=100, blank=True)
    specific_gift = models.CharField(max_length=100, blank=True)
    
    # Actions
    actions = models.ManyToManyField(Action, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.trigger_type} - {self.user_type}"

class OverlayScreen(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    screen_number = models.IntegerField()
    max_queue_length = models.IntegerField(default=5)
    is_online = models.BooleanField(default=False)
    
    def get_url(self):
        return f"https://tikfinity.zerody.one/widget/myactions?cid={self.user.id}&screen={self.screen_number}"
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"

class Timer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    interval_minutes = models.IntegerField()
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Timer {self.interval_minutes}min - {self.action.name}"

class CountdownTimer(models.Model):
    EXPIRE_ACTIONS = [
        ('none', 'Do Nothing'),
        ('end_stream', 'End Stream'),
        ('play_sound', 'Play Sound'),
        ('show_message', 'Show Message'),
        ('trigger_action', 'Trigger Action'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    widget_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Timer settings
    default_start_value = models.IntegerField(default=10)  # minutes
    current_value = models.IntegerField(default=10)  # current countdown value in minutes
    is_running = models.BooleanField(default=False)
    is_paused = models.BooleanField(default=False)
    
    # Expiry action
    expire_action = models.CharField(max_length=20, choices=EXPIRE_ACTIONS, default='none')
    expire_action_data = models.JSONField(default=dict, blank=True)
    
    # Interaction settings (seconds to add/subtract per interaction)
    seconds_per_coin = models.FloatField(default=1.0)
    seconds_per_subscribe = models.FloatField(default=300.0)
    seconds_per_follow = models.FloatField(default=0.0)
    seconds_per_share = models.FloatField(default=0.0)
    seconds_per_like = models.FloatField(default=0.0)
    seconds_per_chat = models.FloatField(default=0.0)
    
    # Multiplier settings
    enable_multiplier = models.BooleanField(default=False)
    multiplier_value = models.FloatField(default=1.5)
    
    # Keyboard shortcuts
    shortcut_start_pause = models.CharField(max_length=50, blank=True)
    shortcut_increase = models.CharField(max_length=50, blank=True)
    shortcut_reduce = models.CharField(max_length=50, blank=True)
    shortcut_step = models.IntegerField(default=1)  # seconds
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_widget_url(self):
        return f"/tiktok/widget/timer/?cid={self.user.id}&timer_id={self.widget_id}"
    
    def get_remaining_seconds(self):
        """Calculate remaining seconds based on current state"""
        if not self.is_running:
            return self.current_value * 60
        
        if self.is_paused:
            return self.current_value * 60
        
        # Calculate elapsed time since start
        if self.started_at:
            elapsed = timezone.now() - self.started_at
            remaining = (self.current_value * 60) - elapsed.total_seconds()
            return max(0, remaining)
        
        return self.current_value * 60
    
    def add_time(self, seconds):
        """Add time to the timer"""
        if self.enable_multiplier:
            seconds *= self.multiplier_value
        
        current_seconds = self.get_remaining_seconds()
        new_seconds = current_seconds + seconds
        self.current_value = max(0, new_seconds / 60)
        self.save()
    
    def subtract_time(self, seconds):
        """Subtract time from the timer"""
        if self.enable_multiplier:
            seconds *= self.multiplier_value
        
        current_seconds = self.get_remaining_seconds()
        new_seconds = current_seconds - seconds
        self.current_value = max(0, new_seconds / 60)
        self.save()
    
    def start(self):
        """Start the timer"""
        self.is_running = True
        self.is_paused = False
        self.started_at = timezone.now()
        self.save()
    
    def pause(self):
        """Pause the timer"""
        if self.is_running:
            self.is_paused = True
            self.paused_at = timezone.now()
            # Update current_value to reflect elapsed time
            remaining = self.get_remaining_seconds()
            self.current_value = remaining / 60
            self.save()
    
    def reset(self):
        """Reset the timer to default value"""
        self.is_running = False
        self.is_paused = False
        self.current_value = self.default_start_value
        self.started_at = None
        self.paused_at = None
        self.save()
    
    def __str__(self):
        return f"Countdown Timer - {self.user.username}"