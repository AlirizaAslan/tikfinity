from django.urls import path
from . import views

app_name = 'tiktok_live'

urlpatterns = [
    # Setup (No login required)
    path('setup/', views.setup, name='setup'),
    path('', views.setup, name='home'),  # Default to setup
    
    # Legal Pages
    path('terms/', views.terms_of_service, name='terms'),
    path('privacy/', views.privacy_policy, name='privacy'),
    
    # Authentication
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # TikTok OAuth
    path('auth/tiktok/', views.tiktok_oauth_login, name='tiktok_oauth_login'),
    path('auth/tiktok/callback/', views.tiktok_oauth_callback, name='tiktok_oauth_callback'),
    path('test-oauth/', views.test_oauth_config, name='test_oauth_config'),
    
    # Google OAuth
    path('auth/google/', views.google_oauth_login, name='google_oauth_login'),
    path('auth/google/callback/', views.google_oauth_callback, name='google_oauth_callback'),
    
    # Dashboard & Streams
    path('', views.dashboard, name='dashboard'),
    path('live/<str:username>/', views.live_stream, name='live_stream'),
    path('interactions/<int:stream_id>/', views.interactions, name='interactions'),
    
    # Automations
    path('automations/', views.automations, name='automations'),
    path('automations/create/', views.create_automation, name='create_automation'),
    path('automations/<int:trigger_id>/toggle/', views.toggle_automation, name='toggle_automation'),
    path('automations/<int:trigger_id>/delete/', views.delete_automation, name='delete_automation'),
    
    # Auto Responses
    path('auto-responses/', views.auto_responses, name='auto_responses'),
    path('auto-responses/create/', views.create_auto_response, name='create_auto_response'),
    
    # Account Management
    path('account/add/', views.add_account, name='add_account'),
    path('account/<int:account_id>/verify/', views.verify_ownership, name='verify_ownership'),
    
    # Stream Stats & Control
    path('stream/<int:stream_id>/stats/', views.get_stream_stats, name='stream_stats'),
    path('stream/<int:stream_id>/toggle-monitoring/', views.toggle_stream_monitoring, name='toggle_monitoring'),
    path('stream/<int:stream_id>/toggle-auto-response/', views.toggle_auto_response, name='toggle_auto_response'),
    path('stream/<int:stream_id>/toggle-automation/', views.toggle_stream_automation, name='toggle_stream_automation'),
    
    # Stream Control Settings
    path('account/<int:account_id>/update-control/', views.update_stream_control, name='update_stream_control'),
    
    # My Streams
    path('my-streams/', views.my_streams, name='my_streams'),
    
    # API - Live Status Check
    path('api/check-live/<str:username>/', views.check_live_status, name='check_live_status'),
]
