from django.contrib import admin
from .models import TikTokAccount, LiveStream, StreamInteraction, AutomationTrigger, AutoResponse, UserPoints, Widget, Action, Event, OverlayScreen, Timer

@admin.register(TikTokAccount)
class TikTokAccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'user', 'is_verified', 'is_live', 'created_at']
    list_filter = ['is_verified', 'is_live', 'created_at']
    search_fields = ['username', 'user__username', 'display_name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    list_display = ['account', 'stream_id', 'is_active', 'viewer_count', 'started_at']
    list_filter = ['is_active', 'started_at']
    search_fields = ['account__username', 'stream_id', 'title']
    readonly_fields = ['started_at', 'ended_at']

@admin.register(StreamInteraction)
class StreamInteractionAdmin(admin.ModelAdmin):
    list_display = ['username', 'interaction_type', 'stream', 'timestamp']
    list_filter = ['interaction_type', 'timestamp']
    search_fields = ['username', 'message']
    readonly_fields = ['timestamp']

@admin.register(AutomationTrigger)
class AutomationTriggerAdmin(admin.ModelAdmin):
    list_display = ['name', 'trigger_type', 'action_type', 'is_active']
    list_filter = ['trigger_type', 'action_type', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_at']

@admin.register(AutoResponse)
class AutoResponseAdmin(admin.ModelAdmin):
    list_display = ['trigger_keywords', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['trigger_keywords', 'response_message']
    readonly_fields = ['created_at']

@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'screen', 'duration', 'created_at']
    list_filter = ['screen', 'has_animation', 'has_picture', 'has_sound', 'has_video']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['trigger_type', 'user_type', 'is_active', 'created_at']
    list_filter = ['trigger_type', 'user_type', 'is_active']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(OverlayScreen)
class OverlayScreenAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'screen_number', 'max_queue_length', 'is_online']
    list_filter = ['is_online']
    search_fields = ['name']

@admin.register(Timer)
class TimerAdmin(admin.ModelAdmin):
    list_display = ['action', 'interval_minutes', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    readonly_fields = ['created_at']
