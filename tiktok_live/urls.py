from django.urls import path
from . import views
from .actions_events_views import actions_and_events, create_action, create_event, simulate_event, create_timer, update_screen_settings

app_name = 'tiktok_live'

urlpatterns = [
    # Main pages
    path('', views.dashboard, name='dashboard'),
    path('setup/', views.setup, name='setup'),
    path('start/', views.dashboard, name='start'),
    
    # Auth
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # OAuth
    path('auth/tiktok/', views.tiktok_oauth_login, name='tiktok_oauth_login'),
    path('auth/tiktok/callback/', views.tiktok_oauth_callback, name='tiktok_oauth_callback'),
    path('auth/google/', views.google_oauth_login, name='google_oauth_login'),
    path('auth/google/callback/', views.google_oauth_callback, name='google_oauth_callback'),
    
    # Actions & Events
    path('actions-events/', actions_and_events, name='actions_events'),
    path('actions-events/create-action/', create_action, name='create_action'),
    path('actions-events/create-event/', create_event, name='create_event'),
    path('actions-events/simulate/', simulate_event, name='simulate_event'),
    path('actions-events/create-timer/', create_timer, name='create_timer'),
    path('actions-events/update-screen/', update_screen_settings, name='update_screen_settings'),
    
    # Test/Debug
    path('test-oauth/', views.test_oauth_config, name='test_oauth_config'),
    
    # Terms & Privacy
    path('terms/', views.terms_of_service, name='terms'),
    path('privacy/', views.privacy_policy, name='privacy'),
    
    # Tools
    path('halving/', views.halving, name='halving'),
    path('halving/execute/', views.execute_halving, name='execute_halving'),
    
    # Users & Points
    path('users-points/', views.users_points, name='users_points'),
    path('users-points/data/', views.users_points_data, name='users_points_data'),
    path('users-points/update-settings/', views.update_points_settings, name='update_points_settings'),
    path('users-points/reset/', views.reset_points, name='reset_points'),
    path('users-points/audit/<int:user_id>/', views.user_audit, name='user_audit'),
    
    # Timer
    path('timer/', views.timer, name='timer'),
    path('timer/start/', views.timer_start, name='timer_start'),
    path('timer/pause/', views.timer_pause, name='timer_pause'),
    path('timer/reset/', views.timer_reset, name='timer_reset'),
    path('timer/add-time/', views.timer_add_time, name='timer_add_time'),
    path('timer/subtract-time/', views.timer_subtract_time, name='timer_subtract_time'),
    path('timer/update-settings/', views.timer_update_settings, name='timer_update_settings'),
    path('timer/set-expire-action/', views.timer_set_expire_action, name='timer_set_expire_action'),
    
    # Widgets
    path('widget/timer/', views.timer_widget, name='timer_widget'),
    path('widget/goal/', views.goal_widget, name='goal_widget'),
    path('widget/top-gift/', views.top_gift_widget, name='top_gift_widget'),
    path('widget/top-streak/', views.top_streak_widget, name='top_streak_widget'),
    path('widget/gift-counter/', views.gift_counter_widget, name='gift_counter_widget'),
    path('widget/lastx/', views.lastx_widget, name='lastx_widget'),
    path('widget/activity-feed/', views.activity_feed_widget, name='activity_feed_widget'),
    
    # API endpoints
    path('api/timer/status/', views.timer_status_api, name='timer_status_api'),
    path('check-live/<str:username>/', views.check_live_status, name='check_live_status'),
    path('profile/<str:username>/', views.get_tiktok_profile, name='get_tiktok_profile'),
    
    # Overlay Gallery
    path('overlay-gallery/', views.overlay_gallery, name='overlay_gallery'),
    path('widget/<str:widget_id>/', views.widget_view, name='widget_view'),
    
    # Other pages
    path('sound-alerts/', views.sound_alerts, name='sound_alerts'),
    path('chat-commands/', views.chat_commands, name='chat_commands'),
    path('chat-commands/<str:subsection>/', views.chat_commands, name='chat_commands_sub'),
    path('tts-chat/', views.tts_chat, name='tts_chat'),
    path('tts-chat/<str:subsection>/', views.tts_chat, name='tts_chat_sub'),
    path('transactions/', views.transactions, name='transactions'),
    path('song-requests/', views.song_requests, name='song_requests'),
    path('likeathon/', views.likeathon, name='likeathon'),
    path('wheel-fortune/', views.wheel_fortune, name='wheel_fortune'),
    path('points-drop/', views.points_drop, name='points_drop'),
    path('challenge/', views.challenge, name='challenge'),
    path('split/', views.split, name='split'),
    path('viewer-analysis/', views.viewer_analysis, name='viewer_analysis'),
    path('event-api/', views.event_api, name='event_api'),
    path('profile-settings/', views.profile_settings, name='profile_settings'),
    path('target-overlays/', views.target_overlays, name='target_overlays'),
    path('target-overlays/<str:subsection>/', views.target_overlays, name='target_overlays_sub'),
    path('gift-overlays/', views.gift_overlays, name='gift_overlays'),
    path('gift-overlays/<str:subsection>/', views.gift_overlays, name='gift_overlays_sub'),
    path('recent-overlays/', views.recent_overlays, name='recent_overlays'),
    path('recent-overlays/<str:subsection>/', views.recent_overlays, name='recent_overlays_sub'),
    path('obs-panels/', views.obs_panels, name='obs_panels'),
    path('automations/', views.automations, name='automations'),
    path('auto-responses/', views.auto_responses, name='auto_responses'),
    path('my-streams/', views.my_streams, name='my_streams'),
    path('chatbot/', views.chatbot, name='chatbot'),
    
    # AJAX endpoints
    path('ajax/add-account/', views.add_account, name='add_account'),
    path('ajax/chatbot/send-test/', views.chatbot_send_test, name='chatbot_send_test'),
    path('ajax/chatbot/update-settings/', views.chatbot_update_settings, name='chatbot_update_settings'),
    path('ajax/chatbot/update-message/', views.chatbot_update_message, name='chatbot_update_message'),
    path('ajax/tts/update-settings/', views.tts_update_settings, name='tts_update_settings'),
    path('ajax/tts/generate/', views.tts_generate, name='tts_generate'),
    path('ajax/tts/test/', views.tts_test, name='tts_test'),
    
    # Stream management
    path('stream/<str:username>/', views.live_stream, name='live_stream'),
    path('stream/<int:stream_id>/interactions/', views.interactions, name='interactions'),
    path('stream/<int:stream_id>/stats/', views.get_stream_stats, name='get_stream_stats'),
    path('stream/<int:stream_id>/toggle-monitoring/', views.toggle_stream_monitoring, name='toggle_stream_monitoring'),
    path('stream/<int:stream_id>/toggle-auto-response/', views.toggle_auto_response, name='toggle_auto_response'),
    path('stream/<int:stream_id>/toggle-automation/', views.toggle_stream_automation, name='toggle_stream_automation'),
    path('account/<int:account_id>/update-control/', views.update_stream_control, name='update_stream_control'),
    path('account/<int:account_id>/verify/', views.verify_ownership, name='verify_ownership'),
    
    # Automation management
    path('automation/create/', views.create_automation, name='create_automation'),
    path('automation/<int:trigger_id>/toggle/', views.toggle_automation, name='toggle_automation'),
    path('automation/<int:trigger_id>/delete/', views.delete_automation, name='delete_automation'),
    path('auto-response/create/', views.create_auto_response, name='create_auto_response'),
]