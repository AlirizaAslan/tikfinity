from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import TikTokAccount, LiveStream, StreamInteraction, AutomationTrigger, AutoResponse, UserPoints, Widget, Action, Event, OverlayScreen, Timer, PointsTransaction, PointsSettings, CountdownTimer, PointsHalving, ChatbotSettings, ChatbotMessage, ChatbotLog, TTSSettings, TTSSpecialUser, TTSLog
from .actions_events_views import actions_and_events, create_action, create_event, simulate_event, create_timer, update_screen_settings
from .lastx_views import lastx_overlays, lastx_widget, lastx_test
from django.db.models import Count, Q
from django.utils import timezone
from .tiktok_oauth import TikTokOAuth
from .google_oauth import GoogleOAuth
import json
import random
import secrets
import logging
from TikTokLive import TikTokLiveClient
from TikTokLive.client.errors import UserOfflineError, UserNotFoundError

logger = logging.getLogger(__name__)

def terms_of_service(request):
    return render(request, 'tiktok_live/terms.html')

def privacy_policy(request):
    return render(request, 'tiktok_live/privacy.html')

def setup(request):
    """Setup page - TikFinity style (no login required)"""
    if request.method == 'POST':
        # Handle form submission
        tiktok_username = request.POST.get('tiktok_username', '').strip()
        if tiktok_username:
            # Store username in session
            request.session['tiktok_username'] = tiktok_username
            return redirect('tiktok_live:dashboard')
    
    tiktok_username = request.session.get('tiktok_username', '')
    return render(request, 'tiktok_live/setup.html', {
        'tiktok_username': tiktok_username
    })

def user_register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('tiktok_live:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        tiktok_username = request.POST.get('tiktok_username', '').strip('@')
        
        # Validation
        errors = []
        if not username or not email or not password:
            errors.append('All fields are required')
        if password != password_confirm:
            errors.append('Passwords do not match')
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        if User.objects.filter(email=email).exists():
            errors.append('Email already exists')
        
        if errors:
            return render(request, 'tiktok_live/register.html', {'errors': errors})
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Create user profile
        UserProfile.objects.create(user=user, tiktok_username=tiktok_username)
        
        # If TikTok username provided, create TikTok account as owned
        if tiktok_username:
            account = TikTokAccount.objects.create(
                user=user,
                username=tiktok_username,
                is_owner=True,
                can_control_stream=True,
                is_verified_owner=False,  # Will be verified later
                verification_method='username_match'
            )
            StreamControl.objects.create(account=account)
        
        # Auto login
        login(request, user)
        return redirect('tiktok_live:dashboard')
    
    return render(request, 'tiktok_live/register.html')

def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('tiktok_live:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('tiktok_live:dashboard')
        else:
            return render(request, 'tiktok_live/login.html', {
                'error': 'Invalid username or password'
            })
    
    return render(request, 'tiktok_live/login.html')

def user_logout(request):
    """User logout view"""
    logout(request)
    return redirect('tiktok_live:login')

def test_oauth_config(request):
    """Test OAuth configuration"""
    from django.conf import settings
    from django.http import HttpResponse
    
    client_key = getattr(settings, 'TIKTOK_CLIENT_KEY', '')
    client_secret = getattr(settings, 'TIKTOK_CLIENT_SECRET', '')
    redirect_uri = getattr(settings, 'TIKTOK_REDIRECT_URI', '')
    
    html = f"""
    <html>
    <head><title>TikTok OAuth Config Test</title></head>
    <body style="font-family: monospace; padding: 20px;">
        <h1>TikTok OAuth Configuration Test</h1>
        <hr>
        <h3>Client Key:</h3>
        <p><strong>{client_key}</strong></p>
        <p>Length: {len(client_key)}</p>
        
        <h3>Client Secret:</h3>
        <p><strong>{client_secret[:10]}...</strong></p>
        <p>Length: {len(client_secret)}</p>
        
        <h3>Redirect URI:</h3>
        <p><strong>{redirect_uri}</strong></p>
        
        <hr>
        <h3>Status:</h3>
        <ul>
            <li>Client Key: {'OK' if client_key else 'EMPTY'}</li>
            <li>Client Secret: {'OK' if client_secret else 'EMPTY'}</li>
            <li>Redirect URI: {'OK' if redirect_uri else 'EMPTY'}</li>
        </ul>
        
        <hr>
        <h3>Test OAuth URL:</h3>
        <a href="/tiktok/auth/tiktok/">Click here to test OAuth login</a>
    </body>
    </html>
    """
    return HttpResponse(html)

def tiktok_oauth_login(request):
    """Initiate TikTok OAuth login"""
    from django.conf import settings
    
    # Debug: Check configuration
    client_key = getattr(settings, 'TIKTOK_CLIENT_KEY', '')
    if not client_key or client_key == '':
        return render(request, 'tiktok_live/login.html', {
            'error': 'TikTok OAuth is not configured. Please add TIKTOK_CLIENT_KEY in settings.py'
        })
    
    oauth = TikTokOAuth()
    state = secrets.token_urlsafe(32)
    code_verifier = oauth.generate_code_verifier()
    
    request.session['oauth_state'] = state
    request.session['code_verifier'] = code_verifier
    
    auth_url = oauth.get_authorization_url(state=state, code_verifier=code_verifier)
    return redirect(auth_url)

def tiktok_oauth_callback(request):
    """Handle TikTok OAuth callback"""
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    session_state = request.session.get('oauth_state')
    code_verifier = request.session.get('code_verifier')
    
    if not state or state != session_state:
        return render(request, 'tiktok_live/login.html', {
            'error': 'Invalid OAuth state. Please try again.'
        })
    
    if not code:
        return render(request, 'tiktok_live/login.html', {
            'error': 'No authorization code received from TikTok.'
        })
    
    if not code_verifier:
        return render(request, 'tiktok_live/login.html', {
            'error': 'Session expired. Please try again.'
        })
    
    oauth = TikTokOAuth()
    user, error = oauth.authenticate_user(request, code, code_verifier)
    
    if error:
        return render(request, 'tiktok_live/login.html', {
            'error': f'TikTok authentication failed: {error}'
        })
    
    login(request, user)
    
    if 'oauth_state' in request.session:
        del request.session['oauth_state']
    if 'code_verifier' in request.session:
        del request.session['code_verifier']
    
    return redirect('tiktok_live:dashboard')

def google_oauth_login(request):
    """Initiate Google OAuth login"""
    oauth = GoogleOAuth()
    auth_url = oauth.get_authorization_url()
    return redirect(auth_url)

def google_oauth_callback(request):
    """Handle Google OAuth callback"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        return render(request, 'tiktok_live/login.html', {
            'error': f'Google authentication failed: {error}'
        })
    
    if not code:
        return render(request, 'tiktok_live/login.html', {
            'error': 'No authorization code received from Google.'
        })
    
    try:
        oauth = GoogleOAuth()
        user, created = oauth.authenticate_user(code)
        login(request, user)
        return redirect('tiktok_live:dashboard')
    except Exception as e:
        return render(request, 'tiktok_live/login.html', {
            'error': f'Google authentication failed: {str(e)}'
        })


def dashboard(request):
    """Main dashboard view - TikFinity style (no login required)"""
    # Get TikTok username from session or localStorage
    tiktok_username = request.session.get('tiktok_username', '')
    
    # If no username, redirect to setup
    if not tiktok_username and not request.user.is_authenticated:
        return redirect('tiktok_live:setup')
    
    # Simple context without database queries to avoid migration issues
    context = {
        'accounts': [],
        'owned_accounts': [],
        'monitored_accounts': [],
        'active_streams': [],
        'tiktok_username': tiktok_username
    }
    
    return render(request, 'tiktok_live/dashboard.html', context)

@login_required
def live_stream(request, username):
    account = get_object_or_404(TikTokAccount, username=username, user=request.user)
    stream = LiveStream.objects.filter(account=account, is_active=True).first()
    
    if not stream:
        stream = LiveStream.objects.create(
            account=account,
            stream_id=f"{username}_{timezone.now().timestamp()}",
            is_monitored=True
        )
    
    # Get stream control settings if available
    stream_control = None
    if hasattr(account, 'stream_control'):
        stream_control = account.stream_control
    
    context = {
        'account': account,
        'stream': stream,
        'username': username,
        'is_owner': account.is_owner,
        'can_control': account.can_control_stream,
        'stream_control': stream_control,
    }
    return render(request, 'tiktok_live/live_stream.html', context)

@login_required
def interactions(request, stream_id):
    stream = get_object_or_404(LiveStream, id=stream_id, account__user=request.user)
    
    interaction_type = request.GET.get('type', 'all')
    interactions_qs = StreamInteraction.objects.filter(stream=stream)
    
    if interaction_type != 'all':
        interactions_qs = interactions_qs.filter(interaction_type=interaction_type)
    
    interactions_list = interactions_qs[:100]
    
    stats = {
        'total': interactions_qs.count(),
        'comments': interactions_qs.filter(interaction_type='comment').count(),
        'gifts': interactions_qs.filter(interaction_type='gift').count(),
        'follows': interactions_qs.filter(interaction_type='follow').count(),
        'likes': interactions_qs.filter(interaction_type='like').count(),
    }
    
    context = {
        'stream': stream,
        'interactions': interactions_list,
        'stats': stats,
        'current_filter': interaction_type,
    }
    return render(request, 'tiktok_live/interactions.html', context)

@login_required
def automations(request):
    triggers = AutomationTrigger.objects.filter(account__user=request.user)
    accounts = TikTokAccount.objects.filter(user=request.user)
    
    context = {
        'triggers': triggers,
        'accounts': accounts,
    }
    return render(request, 'tiktok_live/automations.html', context)

@login_required
@require_http_methods(["POST"])
def create_automation(request):
    data = json.loads(request.body)
    account = get_object_or_404(TikTokAccount, id=data['account_id'], user=request.user)
    
    trigger = AutomationTrigger.objects.create(
        account=account,
        name=data['name'],
        trigger_type=data['trigger_type'],
        condition_value=data.get('condition_value', 1),
        action_type=data['action_type'],
        action_data=data.get('action_data', {})
    )
    
    return JsonResponse({'success': True, 'trigger_id': trigger.id})

@login_required
@require_http_methods(["POST"])
def toggle_automation(request, trigger_id):
    trigger = get_object_or_404(AutomationTrigger, id=trigger_id, account__user=request.user)
    trigger.is_active = not trigger.is_active
    trigger.save()
    
    return JsonResponse({'success': True, 'is_active': trigger.is_active})



@login_required
@require_http_methods(["DELETE"])
def delete_automation(request, trigger_id):
    trigger = get_object_or_404(AutomationTrigger, id=trigger_id, account__user=request.user)
    trigger.delete()
    
    return JsonResponse({'success': True})

@login_required
def auto_responses(request):
    responses = AutoResponse.objects.filter(account__user=request.user)
    accounts = TikTokAccount.objects.filter(user=request.user)
    
    context = {
        'responses': responses,
        'accounts': accounts,
    }
    return render(request, 'tiktok_live/auto_responses.html', context)

@login_required
@require_http_methods(["POST"])
def create_auto_response(request):
    data = json.loads(request.body)
    account = get_object_or_404(TikTokAccount, id=data['account_id'], user=request.user)
    
    response = AutoResponse.objects.create(
        account=account,
        keyword=data['keyword'],
        response_text=data['response_text']
    )
    
    return JsonResponse({'success': True, 'response_id': response.id})

@login_required
@require_http_methods(["POST"])
def add_account(request):
    data = json.loads(request.body)
    username = data.get('username', '').strip('@')
    is_owner = data.get('is_owner', False)  # User can mark if this is their own account
    
    # Validate username
    if not username:
        return JsonResponse({'success': False, 'error': 'Username is required'})
    
    if TikTokAccount.objects.filter(username=username).exists():
        return JsonResponse({'success': False, 'error': 'This account is already added'})
    
    account = TikTokAccount.objects.create(
        user=request.user,
        username=username,
        is_owner=is_owner,
        can_control_stream=is_owner  # Only owners can control their streams
    )
    
    # Create stream control settings if this is owner's account
    if is_owner:
        StreamControl.objects.create(account=account)
    
    return JsonResponse({
        'success': True, 
        'account_id': account.id,
        'is_owner': is_owner,
        'message': f'Account @{username} added successfully! Make sure the user is live before connecting.'
    })

@login_required
def get_stream_stats(request, stream_id):
    stream = get_object_or_404(LiveStream, id=stream_id, account__user=request.user)
    
    stats = {
        'viewer_count': stream.viewer_count,
        'peak_viewers': stream.peak_viewers,
        'total_interactions': StreamInteraction.objects.filter(stream=stream).count(),
        'total_comments': stream.total_comments,
        'total_gifts': stream.total_gifts,
        'total_likes': stream.total_likes,
        'total_shares': stream.total_shares,
        'follows': StreamInteraction.objects.filter(stream=stream, interaction_type='follow').count(),
        'total_gift_value': sum(
            i.gift_value for i in StreamInteraction.objects.filter(stream=stream, interaction_type='gift')
        ),
        'is_monitored': stream.is_monitored,
        'auto_response_enabled': stream.auto_response_enabled,
        'automation_enabled': stream.automation_enabled,
    }
    
    return JsonResponse(stats)

@login_required
@require_http_methods(["POST"])
def toggle_stream_monitoring(request, stream_id):
    """Toggle stream monitoring on/off"""
    stream = get_object_or_404(LiveStream, id=stream_id, account__user=request.user)
    
    # Only allow if user owns this account
    if not stream.account.can_control_stream:
        return JsonResponse({'success': False, 'error': 'You do not have permission to control this stream'})
    
    stream.is_monitored = not stream.is_monitored
    stream.save()
    
    return JsonResponse({
        'success': True, 
        'is_monitored': stream.is_monitored,
        'message': f'Monitoring {"enabled" if stream.is_monitored else "disabled"}'
    })

@login_required
@require_http_methods(["POST"])
def toggle_auto_response(request, stream_id):
    """Toggle auto-response for stream"""
    stream = get_object_or_404(LiveStream, id=stream_id, account__user=request.user)
    
    if not stream.account.can_control_stream:
        return JsonResponse({'success': False, 'error': 'You do not have permission to control this stream'})
    
    stream.auto_response_enabled = not stream.auto_response_enabled
    stream.save()
    
    return JsonResponse({
        'success': True, 
        'enabled': stream.auto_response_enabled,
        'message': f'Auto-response {"enabled" if stream.auto_response_enabled else "disabled"}'
    })

@login_required
@require_http_methods(["POST"])
def toggle_stream_automation(request, stream_id):
    """Toggle automation for stream"""
    stream = get_object_or_404(LiveStream, id=stream_id, account__user=request.user)
    
    if not stream.account.can_control_stream:
        return JsonResponse({'success': False, 'error': 'You do not have permission to control this stream'})
    
    stream.automation_enabled = not stream.automation_enabled
    stream.save()
    
    return JsonResponse({
        'success': True, 
        'enabled': stream.automation_enabled,
        'message': f'Automation {"enabled" if stream.automation_enabled else "disabled"}'
    })

@login_required
@require_http_methods(["POST"])
def update_stream_control(request, account_id):
    """Update stream control settings"""
    account = get_object_or_404(TikTokAccount, id=account_id, user=request.user)
    
    if not account.is_owner:
        return JsonResponse({'success': False, 'error': 'Only account owners can update control settings'})
    
    data = json.loads(request.body)
    
    # Get or create stream control
    stream_control, created = StreamControl.objects.get_or_create(account=account)
    
    # Update settings
    if 'can_view_analytics' in data:
        stream_control.can_view_analytics = data['can_view_analytics']
    if 'notify_on_gift' in data:
        stream_control.notify_on_gift = data['notify_on_gift']
    if 'notify_on_follow' in data:
        stream_control.notify_on_follow = data['notify_on_follow']
    if 'notify_threshold_viewers' in data:
        stream_control.notify_threshold_viewers = data['notify_threshold_viewers']
    if 'auto_start_monitoring' in data:
        stream_control.auto_start_monitoring = data['auto_start_monitoring']
    
    stream_control.save()
    
    return JsonResponse({'success': True, 'message': 'Settings updated successfully'})

@login_required
def my_streams(request):
    """View user's own TikTok streams"""
    # Get user's own accounts
    my_accounts = TikTokAccount.objects.filter(user=request.user, is_owner=True)
    
    # Get all streams for these accounts
    streams = LiveStream.objects.filter(account__in=my_accounts).order_by('-started_at')[:20]
    
    context = {
        'my_accounts': my_accounts,
        'streams': streams,
    }
    return render(request, 'tiktok_live/my_streams.html', context)

@login_required
@require_http_methods(["POST"])
def verify_ownership(request, account_id):
    """Verify TikTok account ownership"""
    account = get_object_or_404(TikTokAccount, id=account_id, user=request.user)
    
    if not account.is_owner:
        return JsonResponse({'success': False, 'error': 'This account is not marked as owned'})
    
    # Simple verification: user confirms they own this account
    account.is_verified_owner = True
    account.verification_method = 'manual'
    account.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Account ownership verified!'
    })

def check_live_status(request, username):
    """Check if TikTok user is live using TikTokLive"""
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
    import asyncio
    
    username_clean = username.strip('@')
    logger.info(f"Checking live status for: @{username_clean}")
    
    def check_live():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            client = TikTokLiveClient(unique_id=username_clean)
            
            async def test_connection():
                try:
                    # Try to connect to the live stream
                    logger.info(f"Attempting to connect to @{username_clean}...")
                    await client.start()
                    
                    # Wait for connection to stabilize
                    await asyncio.sleep(2)
                    
                    # If we get here without exception, user is live
                    logger.info(f"Successfully connected! @{username_clean} is LIVE")
                    
                    # Disconnect cleanly
                    try:
                        await client.disconnect()
                    except:
                        pass
                    
                    return True
                    
                except UserOfflineError:
                    logger.info(f"@{username_clean} is OFFLINE (UserOfflineError)")
                    return False
                except UserNotFoundError:
                    logger.info(f"@{username_clean} NOT FOUND (UserNotFoundError)")
                    return False
                except Exception as e:
                    logger.error(f"Error checking @{username_clean}: {type(e).__name__}: {e}")
                    return False
            
            result = loop.run_until_complete(asyncio.wait_for(test_connection(), timeout=10))
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout checking @{username_clean} - assuming OFFLINE")
            return False
        except Exception as e:
            logger.error(f"Unexpected error for @{username_clean}: {type(e).__name__}: {e}")
            return False
        finally:
            try:
                loop.close()
            except:
                pass
    
    try:
        with ThreadPoolExecutor() as executor:
            future = executor.submit(check_live)
            is_live = future.result(timeout=12)
        
        status = "LIVE" if is_live else "OFFLINE"
        logger.info(f"Final status for @{username_clean}: {status}")
        
        return JsonResponse({
            'success': True,
            'is_live': is_live,
            'status': status,
            'username': username_clean,
            'message': f'@{username_clean} is currently {status}'
        })
        
    except FuturesTimeoutError:
        logger.error(f"Executor timeout for @{username_clean}")
        return JsonResponse({
            'success': True,
            'is_live': False,
            'status': 'OFFLINE',
            'username': username_clean,
            'error': 'Connection timeout'
        })
    except Exception as e:
        logger.error(f"Exception in check_live_status: {type(e).__name__}: {e}")
        return JsonResponse({
            'success': True,
            'is_live': False,
            'status': 'OFFLINE',
            'username': username_clean,
            'error': str(e)
        })

def overlay_gallery(request):
    """Overlay Gallery - TikFinity style overlays for OBS/Live Studio"""
    user_id = request.user.id if request.user.is_authenticated else 2449591
    
    overlays = [
        {'id': 'coinmatch', 'name': 'Coin Match', 'description': 'Host live auctions where viewers bid with gifts to reach the top.', 'is_pro': True, 'width': 867, 'height': 555, 'test_enabled': False},
        {'id': 'wheelofactions', 'name': 'Wheel Of Actions', 'description': 'Link custom wheels to events and trigger actions on segments.', 'is_pro': True, 'width': 867, 'height': 455, 'test_enabled': True},
        {'id': 'cannon', 'name': 'Gift Cannon', 'description': 'Profile pictures fly through with gifts when viewers send gifts!', 'is_pro': True, 'width': 867, 'height': 305, 'test_enabled': True},
        {'id': 'likefountain', 'name': 'Like Fountain', 'description': 'Hearts rise when viewers send likes.', 'is_pro': True, 'width': 867, 'height': 305, 'test_enabled': True},
        {'id': 'socialmediarotator', 'name': 'Social Media Rotator', 'description': 'Highlight social channels with pop-up rotations.', 'is_pro': False, 'width': 867, 'height': 450, 'test_enabled': False},
        {'id': 'firework', 'name': 'Gift Firework', 'description': 'Breathtaking firework triggered by gifts.', 'is_pro': False, 'width': 867, 'height': 405, 'test_enabled': True},
        {'id': 'emojify', 'name': 'Emojify', 'description': 'Emojis slide across screen when sent in chat.', 'is_pro': False, 'width': 867, 'height': 305, 'test_enabled': True},
        {'id': 'chat', 'name': 'Chat', 'description': 'Displays TikTok stream chat.', 'is_pro': False, 'width': 867, 'height': 305, 'test_enabled': True},
        {'id': 'gifts', 'name': 'Gift Feed', 'description': 'Lists last received gifts.', 'is_pro': False, 'width': 867, 'height': 305, 'test_enabled': True},
        {'id': 'wheel', 'name': 'Wheel of Fortune', 'description': 'Wheel animation for fortune commands.', 'is_pro': False, 'width': 867, 'height': 605, 'test_enabled': True},
        {'id': 'topgifter', 'name': 'Top Gifters', 'description': 'Ranking of viewers who spent most coins.', 'is_pro': False, 'width': 867, 'height': 605, 'test_enabled': True},
        {'id': 'viewercount', 'name': 'Viewer Count', 'description': 'Shows current TikTok viewer count.', 'is_pro': False, 'width': 867, 'height': 80, 'test_enabled': True},
    ]
    
    return render(request, 'tiktok_live/overlay_gallery.html', {
        'overlays': overlays,
        'user_id': user_id,
        'base_widget_url': request.build_absolute_uri('/tiktok/widget/'),
    })

def widget_view(request, widget_id):
    """Serve individual overlay widgets"""
    cid = request.GET.get('cid', '2449591')
    preview = request.GET.get('preview', '0')
    test = request.GET.get('test', '0')
    customize = request.GET.get('customize', '0')
    
    widget_configs = {
        'coinmatch': {'name': 'Coin Match'},
        'chat': {'name': 'Chat'},
        'gifts': {'name': 'Gift Feed'},
        'viewercount': {'name': 'Viewer Count'},
        'wheelofactions': {'name': 'Wheel Of Actions'},
        'cannon': {'name': 'Gift Cannon'},
        'likefountain': {'name': 'Like Fountain'},
        'firework': {'name': 'Gift Firework'},
        'emojify': {'name': 'Emojify'},
    }
    
    widget_config = widget_configs.get(widget_id, {'name': 'Unknown Widget'})
    
    return render(request, 'tiktok_live/widget.html', {
        'widget_id': widget_id,
        'widget_name': widget_config['name'],
        'cid': cid,
        'preview': preview == '1',
        'test': test == '1',
        'customize': customize == '1',
    })

def sound_alerts(request):
    return render(request, 'tiktok_live/sound_alerts.html')

def chat_commands(request, subsection=None):
    subsections = {
        'commands': 'Commands',
        'settings': 'Settings'
    }
    return render(request, 'tiktok_live/chat_commands.html', {
        'subsection': subsection,
        'subsections': subsections,
        'current_title': subsections.get(subsection, 'Chat Commands')
    })

def tts_chat(request, subsection=None):
    if not request.user.is_authenticated:
        # Create default settings for non-authenticated users
        settings = {
            'is_enabled': False,
            'language': 'tr',
            'voice': 'default',
            'speed': 50,
            'pitch': 50,
            'volume': 100,
            'user_cooldown': 0,
            'max_queue_length': 5,
            'max_comment_length': 300,
            'filter_letter_spam': True,
            'filter_mentions': False,
            'filter_commands': False,
            'message_template': '{comment}',
            'charge_points': False,
            'cost_per_message': 5
        }
        return render(request, 'tiktok_live/tts_chat.html', {
            'not_authenticated': True, 
            'settings': settings, 
            'special_users': [], 
            'logs': []
        })
    
    try:
        settings = TTSSettings.objects.get(user=request.user)
    except TTSSettings.DoesNotExist:
        settings = TTSSettings.objects.create(user=request.user)
    
    special_users = TTSSpecialUser.objects.filter(user=request.user)
    logs = TTSLog.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'tiktok_live/tts_chat.html', {
        'settings': settings, 
        'special_users': special_users, 
        'logs': logs
    })

def users_points(request):
    """Users & Points management page"""
    if not request.user.is_authenticated:
        return render(request, 'tiktok_live/users_points.html', {
            'points_settings': None,
            'total_users': 0,
            'max_users': 2500,
            'not_authenticated': True
        })
    
    # Get or create points settings
    points_settings, created = PointsSettings.objects.get_or_create(
        user=request.user,
        defaults={
            'max_users': 2500,
            'points_per_gift': 10,
            'points_per_follow': 50,
            'points_per_like': 1,
            'points_per_comment': 5,
            'points_per_share': 25,
            'level_up_threshold': 100,
            'enable_points_system': True,
        }
    )
    
    # Get user points data
    user_points = UserPoints.objects.filter(user=request.user).order_by('-points_total')
    
    # Handle AJAX requests for data grid
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Pagination and filtering
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 40))
        sort_field = request.GET.get('sort', 'points_total')
        sort_order = request.GET.get('order', 'desc')
        
        # Apply sorting
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'
        
        user_points = user_points.order_by(sort_field)
        
        # Apply filters
        username_filter = request.GET.get('username')
        if username_filter:
            user_points = user_points.filter(tiktok_username__icontains=username_filter)
        
        points_filter = request.GET.get('points')
        if points_filter:
            try:
                points_filter = int(points_filter)
                user_points = user_points.filter(points_total=points_filter)
            except ValueError:
                pass
        
        level_points_filter = request.GET.get('level_points')
        if level_points_filter:
            try:
                level_points_filter = int(level_points_filter)
                user_points = user_points.filter(points_level=level_points_filter)
            except ValueError:
                pass
        
        first_activity_filter = request.GET.get('first_activity')
        if first_activity_filter:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(first_activity_filter, '%Y-%m-%d')
                user_points = user_points.filter(first_activity__date=date_obj.date())
            except ValueError:
                pass
        
        last_activity_filter = request.GET.get('last_activity')
        if last_activity_filter:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(last_activity_filter, '%Y-%m-%d')
                user_points = user_points.filter(last_activity__date=date_obj.date())
            except ValueError:
                pass
        
        # Pagination
        total_count = user_points.count()
        start = (page - 1) * page_size
        end = start + page_size
        user_points_page = user_points[start:end]
        
        # Format data for DevExtreme DataGrid
        data = []
        for up in user_points_page:
            data.append({
                'id': up.id,
                'username': up.tiktok_username,
                'display_name': up.display_name or up.tiktok_username,
                'profile_picture': up.profile_picture or '/img/nothumb.webp',
                'level': up.level,
                'points_total': f"{up.points_total:,}",
                'points_level': f"{up.points_level:,}",
                'first_activity': up.first_activity.strftime('%m/%d/%Y, %I:%M %p'),
                'last_activity': up.last_activity.strftime('%m/%d/%Y, %I:%M %p'),
            })
        
        return JsonResponse({
            'data': data,
            'totalCount': total_count,
        })
    
    # Regular page request
    total_users = user_points.count()
    
    context = {
        'points_settings': points_settings,
        'total_users': total_users,
        'max_users': points_settings.max_users,
    }
    
    return render(request, 'tiktok_live/users_points.html', context)

def transactions(request):
    return render(request, 'tiktok_live/transactions.html')

def song_requests(request):
    return render(request, 'tiktok_live/song_requests.html')

def likeathon(request):
    return render(request, 'tiktok_live/likeathon.html')

def timer(request):
    """Timer page with countdown functionality"""
    if not request.user.is_authenticated:
        return render(request, 'tiktok_live/timer.html', {
            'countdown_timer': None,
            'widget_url': '',
            'user_id': None,
            'not_authenticated': True
        })
    
    # Get or create countdown timer for user
    countdown_timer, created = CountdownTimer.objects.get_or_create(
        user=request.user,
        defaults={
            'default_start_value': 10,
            'current_value': 10,
            'seconds_per_coin': 1.0,
            'seconds_per_subscribe': 300.0,
            'seconds_per_follow': 0.0,
            'seconds_per_share': 0.0,
            'seconds_per_like': 0.0,
            'seconds_per_chat': 0.0,
            'enable_multiplier': False,
            'multiplier_value': 1.5,
            'shortcut_step': 1,
        }
    )
    
    context = {
        'countdown_timer': countdown_timer,
        'widget_url': countdown_timer.get_widget_url(),
        'user_id': request.user.id,
    }
    
    return render(request, 'tiktok_live/timer.html', context)

def wheel_fortune(request):
    return render(request, 'tiktok_live/wheel_fortune.html')

def points_drop(request):
    return render(request, 'tiktok_live/points_drop.html')

def challenge(request):
    return render(request, 'tiktok_live/challenge.html')

def split(request):
    return render(request, 'tiktok_live/split.html')

def viewer_analysis(request):
    return render(request, 'tiktok_live/viewer_analysis.html')

def event_api(request):
    return render(request, 'tiktok_live/event_api.html')

def profile_settings(request):
    return render(request, 'tiktok_live/profile_settings.html')

def target_overlays(request, subsection=None):
    subsections = {
        'like-target': 'Beğeni Hedefi',
        'share-target': 'Paylaşım Hedefi', 
        'follow-target': 'Takip Hedefi',
        'viewer-target': 'İzleyici Sayısı Hedefi',
        'coin-target': 'Kazanılan Coin Hedefi',
        'custom-targets': 'Özel Hedefler',
        'settings': 'Ayarlar'
    }
    return render(request, 'tiktok_live/target_overlays.html', {
        'subsection': subsection,
        'subsections': subsections,
        'current_title': subsections.get(subsection, 'Hedef Overlay\'leri')
    })

def gift_overlays(request, subsection=None):
    subsections = {
        'gift-notification': 'Hediye Bildirim Overlay\'i',
        'gift-bar': 'Hediye Bar Overlay\'i',
        'gift-ranking': 'Hediye Sıralaması',
        'settings': 'Ayarlar'
    }
    return render(request, 'tiktok_live/gift_overlays.html', {
        'subsection': subsection,
        'subsections': subsections,
        'current_title': subsections.get(subsection, 'Hediye Overlay\'leri')
    })

def recent_overlays(request, subsection=None):
    subsections = {
        'recent-comments': 'Son Yorumlar',
        'recent-gifts': 'Son Hediyeler',
        'recent-followers': 'Son Takipçiler',
        'recent-shares': 'Son Paylaşımlar',
        'settings': 'Ayarlar'
    }
    return render(request, 'tiktok_live/recent_overlays.html', {
        'subsection': subsection,
        'subsections': subsections,
        'current_title': subsections.get(subsection, 'Son X Overlay\'leri')
    })

def obs_panels(request):
    return render(request, 'tiktok_live/obs_panels.html')

def actions_events(request):
    if request.user.is_authenticated:
        actions = Action.objects.filter(user=request.user)
        events = Event.objects.filter(user=request.user)
        overlay_screens = OverlayScreen.objects.filter(user=request.user)
        timers = Timer.objects.filter(user=request.user)
        
        # Create default overlay screens if none exist
        if not overlay_screens.exists():
            for i in range(1, 9):
                OverlayScreen.objects.create(
                    user=request.user,
                    name=f'Screen {i}',
                    screen_number=i
                )
            overlay_screens = OverlayScreen.objects.filter(user=request.user)
    else:
        actions = []
        events = []
        overlay_screens = []
        timers = []
    
    context = {
        'actions': actions,
        'events': events,
        'overlay_screens': overlay_screens,
        'timers': timers,
        'actions_enabled': True,
    }
    return render(request, 'tiktok_live/actions_events.html', context)

def create_action(request):
    if request.method == 'POST':
        action = Action.objects.create(
            user=request.user,
            name=request.POST.get('name'),
            screen=request.POST.get('screen', 'Screen 1'),
            duration=int(request.POST.get('duration', 5)),
            points_change=int(request.POST.get('points_change', 0)),
            description=request.POST.get('description', ''),
            has_animation=request.POST.get('has_animation') == 'on',
            has_picture=request.POST.get('has_picture') == 'on',
            has_sound=request.POST.get('has_sound') == 'on',
            has_video=request.POST.get('has_video') == 'on',
            text_content=request.POST.get('text_content', ''),
            text_color=request.POST.get('text_color', '#FFFFFF'),
        )
        return JsonResponse({'success': True, 'action_id': action.id})
    return JsonResponse({'success': False})

def edit_action(request, action_id):
    action = get_object_or_404(Action, id=action_id, user=request.user)
    if request.method == 'POST':
        action.name = request.POST.get('name')
        action.screen = request.POST.get('screen', 'Screen 1')
        action.duration = int(request.POST.get('duration', 5))
        action.points_change = int(request.POST.get('points_change', 0))
        action.description = request.POST.get('description', '')
        action.has_animation = request.POST.get('has_animation') == 'on'
        action.has_picture = request.POST.get('has_picture') == 'on'
        action.has_sound = request.POST.get('has_sound') == 'on'
        action.has_video = request.POST.get('has_video') == 'on'
        action.text_content = request.POST.get('text_content', '')
        action.text_color = request.POST.get('text_color', '#FFFFFF')
        action.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def delete_action(request, action_id):
    action = get_object_or_404(Action, id=action_id, user=request.user)
    action.delete()
    return JsonResponse({'success': True})

def play_action(request, action_id):
    action = get_object_or_404(Action, id=action_id, user=request.user)
    return JsonResponse({'success': True, 'message': f'Playing action: {action.name}'})

def create_event(request):
    if request.method == 'POST':
        event = Event.objects.create(
            user=request.user,
            trigger_type=request.POST.get('trigger_type'),
            user_type=request.POST.get('user_type', 'any'),
            specific_user=request.POST.get('specific_user', ''),
            min_coins=int(request.POST.get('min_coins', 1)),
            min_likes=int(request.POST.get('min_likes', 100)),
            custom_command=request.POST.get('custom_command', ''),
            specific_gift=request.POST.get('specific_gift', ''),
        )
        action_ids = request.POST.getlist('actions')
        for action_id in action_ids:
            try:
                action = Action.objects.get(id=action_id, user=request.user)
                event.actions.add(action)
            except Action.DoesNotExist:
                pass
        return JsonResponse({'success': True, 'event_id': event.id})
    return JsonResponse({'success': False})

def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, user=request.user)
    if request.method == 'POST':
        event.trigger_type = request.POST.get('trigger_type')
        event.user_type = request.POST.get('user_type', 'any')
        event.specific_user = request.POST.get('specific_user', '')
        event.min_coins = int(request.POST.get('min_coins', 1))
        event.min_likes = int(request.POST.get('min_likes', 100))
        event.custom_command = request.POST.get('custom_command', '')
        event.specific_gift = request.POST.get('specific_gift', '')
        event.save()
        
        event.actions.clear()
        action_ids = request.POST.getlist('actions')
        for action_id in action_ids:
            try:
                action = Action.objects.get(id=action_id, user=request.user)
                event.actions.add(action)
            except Action.DoesNotExist:
                pass
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, user=request.user)
    event.delete()
    return JsonResponse({'success': True})

def create_timer(request):
    if request.method == 'POST':
        try:
            action = Action.objects.get(id=request.POST.get('action_id'), user=request.user)
            timer = Timer.objects.create(
                user=request.user,
                interval_minutes=int(request.POST.get('interval_minutes')),
                action=action
            )
            return JsonResponse({'success': True, 'timer_id': timer.id})
        except Action.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Action not found'})
    return JsonResponse({'success': False})

def delete_timer(request, timer_id):
    timer = get_object_or_404(Timer, id=timer_id, user=request.user)
    timer.delete()
    return JsonResponse({'success': True})

def simulate_event(request, event_type):
    if request.method == 'POST':
        events = Event.objects.filter(user=request.user, trigger_type=event_type, is_active=True)
        triggered_count = 0
        
        for event in events:
            for action in event.actions.all():
                triggered_count += 1
        
        return JsonResponse({
            'success': True, 
            'message': f'Simulated {event_type} event',
            'triggered_actions': triggered_count
        })
    return JsonResponse({'success': False})

@login_required
def users_points_data(request):
    """API endpoint for users points data grid"""
    user_points = UserPoints.objects.filter(user=request.user)
    
    # Apply filters
    username_filter = request.GET.get('username')
    if username_filter:
        user_points = user_points.filter(tiktok_username__icontains=username_filter)
    
    points_filter = request.GET.get('points')
    if points_filter:
        try:
            points_filter = int(points_filter)
            user_points = user_points.filter(points_total=points_filter)
        except ValueError:
            pass
    
    # Sorting
    sort_field = request.GET.get('sort', 'points_total')
    sort_order = request.GET.get('order', 'desc')
    
    if sort_order == 'desc':
        sort_field = f'-{sort_field}'
    
    user_points = user_points.order_by(sort_field)
    
    # Format data
    data = []
    for up in user_points:
        data.append({
            'id': up.id,
            'username': up.tiktok_username,
            'display_name': up.display_name or up.tiktok_username,
            'profile_picture': up.profile_picture or '/img/nothumb.webp',
            'level': up.level,
            'points_total': up.points_total,
            'points_level': up.points_level,
            'first_activity': up.first_activity.isoformat(),
            'last_activity': up.last_activity.isoformat(),
        })
    
    return JsonResponse({'data': data, 'totalCount': len(data)})

@login_required
@require_http_methods(["POST"])
def update_points_settings(request):
    """Update points system settings"""
    try:
        data = json.loads(request.body)
        points_settings, created = PointsSettings.objects.get_or_create(user=request.user)
        
        if 'max_users' in data:
            points_settings.max_users = int(data['max_users'])
        if 'points_per_gift' in data:
            points_settings.points_per_gift = int(data['points_per_gift'])
        if 'points_per_follow' in data:
            points_settings.points_per_follow = int(data['points_per_follow'])
        if 'points_per_like' in data:
            points_settings.points_per_like = int(data['points_per_like'])
        if 'points_per_comment' in data:
            points_settings.points_per_comment = int(data['points_per_comment'])
        if 'points_per_share' in data:
            points_settings.points_per_share = int(data['points_per_share'])
        if 'level_up_threshold' in data:
            points_settings.level_up_threshold = int(data['level_up_threshold'])
        if 'enable_points_system' in data:
            points_settings.enable_points_system = bool(data['enable_points_system'])
        
        points_settings.save()
        
        return JsonResponse({'success': True, 'message': 'Settings updated successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def reset_points(request):
    """Reset all user points"""
    try:
        data = json.loads(request.body)
        reset_type = data.get('type', 'all')
        
        if reset_type == 'all':
            UserPoints.objects.filter(user=request.user).delete()
            PointsTransaction.objects.filter(user_points__user=request.user).delete()
            message = 'All user points have been reset'
        elif reset_type == 'points_only':
            UserPoints.objects.filter(user=request.user).update(
                points_total=0,
                points_level=0,
                level=1
            )
            message = 'All points have been reset to 0'
        
        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def user_audit(request, user_id):
    """View user audit/transaction history"""
    try:
        user_points = get_object_or_404(UserPoints, id=user_id, user=request.user)
        transactions = PointsTransaction.objects.filter(user_points=user_points).order_by('-created_at')[:50]
        
        transaction_data = []
        for transaction in transactions:
            transaction_data.append({
                'type': transaction.get_transaction_type_display(),
                'points_change': transaction.points_change,
                'description': transaction.description,
                'created_at': transaction.created_at.strftime('%m/%d/%Y, %I:%M %p'),
            })
        
        return JsonResponse({
            'success': True,
            'user': {
                'username': user_points.tiktok_username,
                'display_name': user_points.display_name,
                'level': user_points.level,
                'points_total': user_points.points_total,
                'points_level': user_points.points_level,
            },
            'transactions': transaction_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def goal_widget(request):
    cid = request.GET.get('cid', '2449591')
    metric = request.GET.get('metric', 'likes')
    preview = request.GET.get('preview', '0')
    test = request.GET.get('test', '0')
    
    return render(request, 'tiktok_live/goal_widget.html', {
        'cid': cid,
        'metric': metric,
        'preview': preview == '1',
        'test': test == '1',
    })

def top_gift_widget(request):
    cid = request.GET.get('cid', '2449591')
    preview = request.GET.get('preview', '0')
    return render(request, 'tiktok_live/top_gift_widget.html', {
        'cid': cid,
        'preview': preview == '1',
    })

def top_streak_widget(request):
    cid = request.GET.get('cid', '2449591')
    preview = request.GET.get('preview', '0')
    return render(request, 'tiktok_live/top_streak_widget.html', {
        'cid': cid,
        'preview': preview == '1',
    })

def gift_counter_widget(request):
    cid = request.GET.get('cid', '2449591')
    counter = request.GET.get('c', '1')
    preview = request.GET.get('preview', '0')
    return render(request, 'tiktok_live/gift_counter_widget.html', {
        'cid': cid,
        'counter': counter,
        'preview': preview == '1',
    })

def lastx_widget(request):
    cid = request.GET.get('cid', '2449591')
    x_type = request.GET.get('x', 'follower')
    preview = request.GET.get('preview', '0')
    return render(request, 'tiktok_live/lastx_widget.html', {
        'cid': cid,
        'x_type': x_type,
        'preview': preview == '1',
    })

def activity_feed_widget(request):
    cid = request.GET.get('cid', '2449591')
    dock_id = request.GET.get('did', '1')
    preview = request.GET.get('preview', '0')
    return render(request, 'tiktok_live/activity_feed_widget.html', {
        'cid': cid,
        'dock_id': dock_id,
        'preview': preview == '1',
    })

# Timer Control Views
@login_required
@require_http_methods(["POST"])
def timer_start(request):
    """Start the countdown timer"""
    try:
        countdown_timer = CountdownTimer.objects.get(user=request.user)
        countdown_timer.start()
        return JsonResponse({
            'success': True,
            'message': 'Timer started',
            'is_running': countdown_timer.is_running,
            'remaining_seconds': countdown_timer.get_remaining_seconds()
        })
    except CountdownTimer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Timer not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def timer_pause(request):
    """Pause the countdown timer"""
    try:
        countdown_timer = CountdownTimer.objects.get(user=request.user)
        countdown_timer.pause()
        return JsonResponse({
            'success': True,
            'message': 'Timer paused',
            'is_running': countdown_timer.is_running,
            'is_paused': countdown_timer.is_paused,
            'remaining_seconds': countdown_timer.get_remaining_seconds()
        })
    except CountdownTimer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Timer not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def timer_reset(request):
    """Reset the countdown timer"""
    try:
        countdown_timer = CountdownTimer.objects.get(user=request.user)
        countdown_timer.reset()
        return JsonResponse({
            'success': True,
            'message': 'Timer reset',
            'is_running': countdown_timer.is_running,
            'remaining_seconds': countdown_timer.get_remaining_seconds()
        })
    except CountdownTimer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Timer not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def timer_add_time(request):
    """Add time to the countdown timer"""
    try:
        data = json.loads(request.body)
        seconds = int(data.get('seconds', 10))
        
        countdown_timer = CountdownTimer.objects.get(user=request.user)
        countdown_timer.add_time(seconds)
        
        return JsonResponse({
            'success': True,
            'message': f'Added {seconds} seconds',
            'remaining_seconds': countdown_timer.get_remaining_seconds()
        })
    except CountdownTimer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Timer not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def timer_subtract_time(request):
    """Subtract time from the countdown timer"""
    try:
        data = json.loads(request.body)
        seconds = int(data.get('seconds', 10))
        
        countdown_timer = CountdownTimer.objects.get(user=request.user)
        countdown_timer.subtract_time(seconds)
        
        return JsonResponse({
            'success': True,
            'message': f'Subtracted {seconds} seconds',
            'remaining_seconds': countdown_timer.get_remaining_seconds()
        })
    except CountdownTimer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Timer not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def timer_update_settings(request):
    """Update timer settings"""
    try:
        data = json.loads(request.body)
        countdown_timer = CountdownTimer.objects.get(user=request.user)
        
        # Update timer settings
        if 'default_start_value' in data:
            countdown_timer.default_start_value = int(data['default_start_value'])
        if 'seconds_per_coin' in data:
            countdown_timer.seconds_per_coin = float(data['seconds_per_coin'])
        if 'seconds_per_subscribe' in data:
            countdown_timer.seconds_per_subscribe = float(data['seconds_per_subscribe'])
        if 'seconds_per_follow' in data:
            countdown_timer.seconds_per_follow = float(data['seconds_per_follow'])
        if 'seconds_per_share' in data:
            countdown_timer.seconds_per_share = float(data['seconds_per_share'])
        if 'seconds_per_like' in data:
            countdown_timer.seconds_per_like = float(data['seconds_per_like'])
        if 'seconds_per_chat' in data:
            countdown_timer.seconds_per_chat = float(data['seconds_per_chat'])
        if 'enable_multiplier' in data:
            countdown_timer.enable_multiplier = bool(data['enable_multiplier'])
        if 'multiplier_value' in data:
            countdown_timer.multiplier_value = float(data['multiplier_value'])
        if 'shortcut_start_pause' in data:
            countdown_timer.shortcut_start_pause = data['shortcut_start_pause']
        if 'shortcut_increase' in data:
            countdown_timer.shortcut_increase = data['shortcut_increase']
        if 'shortcut_reduce' in data:
            countdown_timer.shortcut_reduce = data['shortcut_reduce']
        if 'shortcut_step' in data:
            countdown_timer.shortcut_step = int(data['shortcut_step'])
        
        countdown_timer.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Timer settings updated successfully'
        })
    except CountdownTimer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Timer not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def timer_set_expire_action(request):
    """Set timer expiry action"""
    try:
        data = json.loads(request.body)
        countdown_timer = CountdownTimer.objects.get(user=request.user)
        
        countdown_timer.expire_action = data.get('action', 'none')
        countdown_timer.expire_action_data = data.get('action_data', {})
        countdown_timer.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Expiry action updated successfully'
        })
    except CountdownTimer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Timer not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def timer_widget(request):
    """Timer widget for overlay"""
    cid = request.GET.get('cid', '2449591')
    timer_id = request.GET.get('timer_id')
    preview = request.GET.get('preview', '0')
    
    try:
        if timer_id:
            countdown_timer = CountdownTimer.objects.get(widget_id=timer_id)
        else:
            # Get timer by user ID
            user = User.objects.get(id=cid)
            countdown_timer = CountdownTimer.objects.get(user=user)
    except (CountdownTimer.DoesNotExist, User.DoesNotExist):
        countdown_timer = None
    
    return render(request, 'tiktok_live/timer_widget.html', {
        'countdown_timer': countdown_timer,
        'cid': cid,
        'preview': preview == '1',
    })

def timer_status_api(request):
    """API endpoint for timer status"""
    try:
        user_id = request.GET.get('cid')
        if user_id:
            user = User.objects.get(id=user_id)
            countdown_timer = CountdownTimer.objects.get(user=user)
        else:
            return JsonResponse({'success': False, 'error': 'User ID required'})
        
        return JsonResponse({
            'success': True,
            'is_running': countdown_timer.is_running,
            'is_paused': countdown_timer.is_paused,
            'remaining_seconds': countdown_timer.get_remaining_seconds(),
            'current_value': countdown_timer.current_value,
            'default_start_value': countdown_timer.default_start_value,
        })
    except (CountdownTimer.DoesNotExist, User.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Timer not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def halving(request):
    """Halving page - reduce user points by percentage"""
    if request.user.is_authenticated:
        last_halving = PointsHalving.objects.filter(user=request.user).order_by('-executed_at').first()
    else:
        last_halving = None
    
    context = {
        'last_halving': last_halving,
    }
    return render(request, 'tiktok_live/halving.html', context)

@login_required
@require_http_methods(["POST"])
def execute_halving(request):
    """Execute points halving"""
    try:
        data = json.loads(request.body)
        percentage = int(data.get('percentage', 50))
        
        if percentage < 1 or percentage > 100:
            return JsonResponse({'success': False, 'error': 'Percentage must be between 1 and 100'})
        
        # Get all user points
        user_points = UserPoints.objects.filter(user=request.user)
        affected_count = user_points.count()
        
        # Calculate reduction factor
        reduction_factor = (100 - percentage) / 100
        
        # Update all user points
        for up in user_points:
            up.points_total = int(up.points_total * reduction_factor)
            up.points_level = int(up.points_level * reduction_factor)
            up.save()
        
        # Record halving
        PointsHalving.objects.create(
            user=request.user,
            percentage=percentage,
            affected_users=affected_count
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully reduced points by {percentage}% for {affected_count} users',
            'affected_users': affected_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def chatbot(request):
    if not request.user.is_authenticated:
        return render(request, 'tiktok_live/chatbot.html', {'not_authenticated': True, 'settings': None, 'messages': [], 'logs': []})
    settings, created = ChatbotSettings.objects.get_or_create(user=request.user)
    default_messages = [
        ('help', '', '@%username% the commands are as following: To see your %currencyname%: %cmdpoints% | %currencyname% to send to a friend: %cmdsend% [Amount] [Username] | Spin the Wheel of Fortune: %cmdspin% | Show other commands: %cmdcustomglobal%, %cmdcustomsub%, %cmdcustompersonal%'),
        ('show_global_commands', '', '@%username% Commands: %globalcommands%'),
        ('show_subscriber_commands', '', '@%username% Subscriber Commands: %subcommands%'),
        ('show_user_commands', '', '@%username% Your personal Commands: %usercommands%'),
        ('points_info_top100', 'User in the top 100', '@%username% you have got %points% %currencyname% (Level: %level%) and you are on place %rank%!'),
        ('points_info_other', 'User not in the top 100', '@%username% you have %points% %currencyname% (Level: %level%).'),
        ('points_transfer_success', 'Send successful', '@%username% %amount% %currencyname% has successfully been given to @%destination%!'),
        ('points_transfer_syntax', 'Incorrect syntax', '@%username% please write down the amount and the receiver behind the instruction.'),
        ('points_transfer_insufficient', 'Send failed (not enough credits)', '@%username% you don\'t have enough %currencyname%!'),
        ('points_transfer_notfound', 'Send failed (receiver not found)', '@%username% we couldn\'t find that user!'),
        ('wheel_insufficient', 'Not enough credits', '@%username% you don\'t have enough %currencyname%! You are missing %requiredpoints% %currencyname%!'),
        ('wheel_no_win', 'No win (0)', '@%username% unlucky this time :('),
        ('wheel_cooldown', 'Waiting time necessary', '@%username% %minutes% minutes until the next chance for a win!'),
        ('wheel_win', 'Win', '@%username% you have been given %amount% %currencyname%!'),
        ('level_up', 'Level Up', '@%username% you have just reached Level: %level%!'),
        ('action_queue_full', 'Queue is full', '@%username% please wait a little bit!'),
        ('action_insufficient', 'Not enough credits', '@%username% you don\'t have enough %currencyname%! You need %actionamount% %currencyname% to execute this action!'),
        ('action_level_low', 'Level too low', '@%username% only users with a level of %requiredlevel% or higher can use this chat command!'),
        ('tts_insufficient', 'Not enough credits', '@%username% you don\'t have enough %currencyname%! You need %actionamount% %currencyname% to use Text-to-Speech!'),
        ('song_insufficient', 'Not enough credits', '@%username% you don\'t have enough %currencyname%! You need %cost% %currencyname% for this action!'),
        ('song_not_found', 'Song not found', '@%username% Song not found.'),
        ('song_queue_full', 'Queue size limit reached', '@%username% The playlist is full. Please try again later.'),
        ('song_user_limit', 'Queue size limit reached for user', '@%username% You already have songs in the playlist. Please wait a bit!'),
        ('song_duplicate', 'Song already in queue', '@%username% This song is already in the playback queue.'),
        ('song_explicit', 'Song not allowed', '@%username% the requested song contains explicit content which is not allowed here.'),
        ('song_added', 'Song added to queue', '@%username% the track "%track%" has been added! Use !revoke if it is the wrong song.'),
        ('song_revoked', 'Song revoke success', '@%username% your last song request has been revoked!'),
        ('song_skip_denied', 'Skip not allowed', '@%username% unable to execute the !skip command for the current song. Not allowed by broadcaster.'),
    ]
    for command, scenario, default_text in default_messages:
        ChatbotMessage.objects.get_or_create(user=request.user, command=command, defaults={'scenario': scenario, 'message_text': default_text})
    messages = ChatbotMessage.objects.filter(user=request.user).order_by('id')
    logs = ChatbotLog.objects.filter(user=request.user).order_by('-sent_at')[:10]
    return render(request, 'tiktok_live/chatbot.html', {'settings': settings, 'messages': messages, 'logs': logs})

@login_required
@require_http_methods(["POST"])
def chatbot_send_test(request):
    test_message = "This is a test message from TikFinity Chatbot!"
    ChatbotLog.objects.create(user=request.user, message=test_message)
    return JsonResponse({'success': True, 'message': 'Test message sent', 'log': test_message})

@login_required
@require_http_methods(["POST"])
def chatbot_update_settings(request):
    try:
        data = json.loads(request.body)
        settings, created = ChatbotSettings.objects.get_or_create(user=request.user)
        if 'is_enabled' in data:
            settings.is_enabled = bool(data['is_enabled'])
        if 'max_messages_per_15_seconds' in data:
            settings.max_messages_per_15_seconds = int(data['max_messages_per_15_seconds'])
        if 'enable_streamerbot' in data:
            settings.enable_streamerbot = bool(data['enable_streamerbot'])
        settings.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def chatbot_update_message(request):
    try:
        data = json.loads(request.body)
        message = ChatbotMessage.objects.get(user=request.user, command=data.get('command'))
        message.message_text = data.get('message_text')
        message.is_active = data.get('is_active', True)
        message.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def tts_update_settings(request):
    try:
        data = json.loads(request.body)
        settings, created = TTSSettings.objects.get_or_create(user=request.user)
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        settings.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@require_http_methods(["POST"])
def tts_generate(request):
    """Generate TTS audio for live chat messages using gTTS"""
    try:
        from gtts import gTTS
        import os
        import hashlib
        from django.conf import settings
        
        data = json.loads(request.body)
        text = data.get('text', '')
        username = data.get('username', 'Unknown')
        language = data.get('language', 'tr')
        
        if not text:
            return JsonResponse({'success': False, 'error': 'Text is required'})
        
        # Check TTS settings if user is authenticated
        if request.user.is_authenticated:
            try:
                tts_settings = TTSSettings.objects.get(user=request.user)
                if not tts_settings.is_enabled:
                    return JsonResponse({'success': False, 'error': 'TTS is disabled'})
                language = tts_settings.language
            except TTSSettings.DoesNotExist:
                pass
        
        # Create media directory
        media_dir = os.path.join(settings.BASE_DIR, 'media', 'tts')
        os.makedirs(media_dir, exist_ok=True)
        
        # Generate unique filename
        text_hash = hashlib.md5(f"{text}_{language}".encode()).hexdigest()[:8]
        audio_filename = f"tts_{text_hash}.mp3"
        audio_path = os.path.join(media_dir, audio_filename)
        
        # Generate audio if not exists
        if not os.path.exists(audio_path):
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(audio_path)
        
        # Log TTS usage if user is authenticated
        if request.user.is_authenticated:
            TTSLog.objects.create(user=request.user, tiktok_username=username, message=text)
        
        audio_url = f"/media/tts/{audio_filename}"
        return JsonResponse({
            'success': True,
            'audio_url': audio_url,
            'text': text,
            'username': username
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["POST"])
def tts_test(request):
    try:
        from gtts import gTTS
        import os
        import hashlib
        from django.conf import settings
        
        data = json.loads(request.body)
        text = data.get('text', 'Test message')
        language = data.get('language', 'tr')
        
        if not text:
            return JsonResponse({'success': False, 'error': 'Text is required'})
        
        # Create media directory
        media_dir = os.path.join(settings.BASE_DIR, 'media', 'tts')
        os.makedirs(media_dir, exist_ok=True)
        
        # Generate unique filename
        text_hash = hashlib.md5(f"{text}_{language}".encode()).hexdigest()[:8]
        audio_filename = f"tts_test_{text_hash}.mp3"
        audio_path = os.path.join(media_dir, audio_filename)
        
        # Generate TTS audio using gTTS
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(audio_path)
        
        # Log TTS usage if user is authenticated
        if request.user.is_authenticated:
            TTSLog.objects.create(user=request.user, tiktok_username='Test', message=text)
        
        audio_url = f"/media/tts/{audio_filename}"
        return JsonResponse({
            'success': True, 
            'message': 'TTS test completed',
            'audio_url': audio_url
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_tiktok_profile(request, username):
    """Get TikTok profile information"""
    username_clean = username.strip('@')
    
    profile_data = {
        'username': username_clean,
        'display_name': username_clean,
        'profile_picture': f'https://p16-sg.tiktokcdn.com/tos-alisg-avt-0068/29c35c87994ae2863915bf384f16acea~tplv-tiktokx-cropcenter:100:100.webp',
    }
    
    return JsonResponse({
        'success': True,
        'username': profile_data['username'],
        'display_name': profile_data['display_name'],
        'profile_picture': profile_data['profile_picture'],
    })