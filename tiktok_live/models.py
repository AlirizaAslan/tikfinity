from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """Extended user profile with TikTok information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tiktok_username = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class TikTokAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    is_owner = models.BooleanField(default=False)  # True if this is the user's own TikTok account
    can_control_stream = models.BooleanField(default=False)  # True if user can control their stream
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: Store TikTok user info
    display_name = models.CharField(max_length=200, blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    # Ownership verification
    is_verified_owner = models.BooleanField(default=False)
    verification_method = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('username_match', 'Username Match'),
        ('manual', 'Manual Verification'),
        ('live_test', 'Live Stream Test'),
    ])

    class Meta:
        unique_together = ['user', 'username']

    def __str__(self):
        owner_tag = " (Owner)" if self.is_owner else ""
        verified_tag = " ✓" if self.is_verified_owner else ""
        return f"{self.username}{owner_tag}{verified_tag}"

class LiveStream(models.Model):
    account = models.ForeignKey(TikTokAccount, on_delete=models.CASCADE)
    stream_id = models.CharField(max_length=255, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    viewer_count = models.IntegerField(default=0)
    
    # Stream control
    is_monitored = models.BooleanField(default=True)  # Whether to monitor this stream
    auto_response_enabled = models.BooleanField(default=False)
    automation_enabled = models.BooleanField(default=False)
    
    # Stream stats
    total_comments = models.IntegerField(default=0)
    total_gifts = models.IntegerField(default=0)
    total_likes = models.IntegerField(default=0)
    total_shares = models.IntegerField(default=0)
    peak_viewers = models.IntegerField(default=0)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        status = "🔴 Live" if self.is_active else "⚫ Ended"
        return f"{status} {self.account.username} - {self.stream_id}"

class Interaction(models.Model):
    INTERACTION_TYPES = [
        ('comment', 'Yorum'),
        ('like', 'Beğeni'),
        ('follow', 'Takip'),
        ('gift', 'Hediye'),
        ('share', 'Paylaşım'),
        ('join', 'Katılım'),
    ]
    
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    username = models.CharField(max_length=100)
    message = models.TextField(blank=True, null=True)
    gift_name = models.CharField(max_length=100, blank=True, null=True)
    gift_value = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.username} - {self.interaction_type}"

class AutomationTrigger(models.Model):
    account = models.ForeignKey(TikTokAccount, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    trigger_type = models.CharField(max_length=20, choices=Interaction.INTERACTION_TYPES)
    condition_value = models.IntegerField(default=1)
    action_type = models.CharField(max_length=50, choices=[
        ('message', 'Mesaj Gönder'),
        ('animation', 'Animasyon Oynat'),
        ('sound', 'Ses Çal'),
        ('script', 'Script Çalıştır'),
    ])
    action_data = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Automation stats
    times_triggered = models.IntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class AutoResponse(models.Model):
    account = models.ForeignKey(TikTokAccount, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=100)
    response_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Response stats
    times_triggered = models.IntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.keyword} -> {self.response_text[:50]}"

class StreamControl(models.Model):
    """Control settings for user's own live streams"""
    account = models.OneToOneField(TikTokAccount, on_delete=models.CASCADE, related_name='stream_control')
    
    # Control permissions
    can_view_analytics = models.BooleanField(default=True)
    can_manage_automations = models.BooleanField(default=True)
    can_manage_responses = models.BooleanField(default=True)
    can_moderate_comments = models.BooleanField(default=False)
    
    # Notifications
    notify_on_gift = models.BooleanField(default=True)
    notify_on_follow = models.BooleanField(default=True)
    notify_threshold_viewers = models.IntegerField(default=100)
    
    # Stream preferences
    auto_start_monitoring = models.BooleanField(default=True)
    save_interactions = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stream Control for {self.account.username}"
