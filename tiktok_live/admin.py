from django.contrib import admin
from .models import TikTokAccount, LiveStream, Interaction, AutomationTrigger, AutoResponse, StreamControl, UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'tiktok_username', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'tiktok_username', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(TikTokAccount)
class TikTokAccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'user', 'is_owner', 'is_verified_owner', 'can_control_stream', 'is_active', 'created_at']
    list_filter = ['is_owner', 'is_verified_owner', 'can_control_stream', 'is_active', 'created_at']
    search_fields = ['username', 'user__username', 'display_name']
    readonly_fields = ['created_at']

@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    list_display = ['account', 'stream_id', 'is_active', 'viewer_count', 'peak_viewers', 'is_monitored', 'started_at']
    list_filter = ['is_active', 'is_monitored', 'auto_response_enabled', 'automation_enabled', 'started_at']
    search_fields = ['account__username', 'stream_id']
    readonly_fields = ['started_at', 'ended_at', 'total_comments', 'total_gifts', 'total_likes', 'total_shares']

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ['username', 'interaction_type', 'stream', 'timestamp', 'is_processed']
    list_filter = ['interaction_type', 'is_processed', 'timestamp']
    search_fields = ['username', 'message']
    readonly_fields = ['timestamp']

@admin.register(AutomationTrigger)
class AutomationTriggerAdmin(admin.ModelAdmin):
    list_display = ['name', 'account', 'trigger_type', 'action_type', 'is_active', 'times_triggered']
    list_filter = ['trigger_type', 'action_type', 'is_active']
    search_fields = ['name', 'account__username']
    readonly_fields = ['created_at', 'last_triggered', 'times_triggered']

@admin.register(AutoResponse)
class AutoResponseAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'account', 'is_active', 'times_triggered', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['keyword', 'response_text']
    readonly_fields = ['created_at', 'last_triggered', 'times_triggered']

@admin.register(StreamControl)
class StreamControlAdmin(admin.ModelAdmin):
    list_display = ['account', 'can_view_analytics', 'can_manage_automations', 'notify_on_gift', 'notify_on_follow']
    list_filter = ['can_view_analytics', 'can_manage_automations', 'notify_on_gift', 'notify_on_follow']
    search_fields = ['account__username']
    readonly_fields = ['created_at', 'updated_at']
