from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import TikTokAccount, LiveStream, Interaction, AutomationTrigger, AutoResponse, StreamControl, UserProfile
from django.db.models import Count, Q
from django.utils import timezone
from .tiktok_oauth import TikTokOAuth
from .google_oauth import GoogleOAuth
import json
import random
import secrets

def terms_of_service(request):
    return render(request, 'tiktok_live/terms.html')

def privacy_policy(request):
    return render(request, 'tiktok_live/privacy.html')

def setup(request):
    """Setup page - TikFinity style (no login required)"""
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
            <li>Client Key: {'✅ OK' if client_key else '❌ EMPTY'}</li>
            <li>Client Secret: {'✅ OK' if client_secret else '❌ EMPTY'}</li>
            <li>Redirect URI: {'✅ OK' if redirect_uri else '❌ EMPTY'}</li>
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
    
    accounts = TikTokAccount.objects.filter(user=request.user)
    active_streams = LiveStream.objects.filter(account__user=request.user, is_active=True)
    
    # Separate owned and monitored accounts
    owned_accounts = accounts.filter(is_owner=True)
    monitored_accounts = accounts.filter(is_owner=False)
    
    context = {
        'accounts': accounts,
        'owned_accounts': owned_accounts,
        'monitored_accounts': monitored_accounts,
        'active_streams': active_streams,
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
    interactions_qs = Interaction.objects.filter(stream=stream)
    
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
        'total_interactions': Interaction.objects.filter(stream=stream).count(),
        'total_comments': stream.total_comments,
        'total_gifts': stream.total_gifts,
        'total_likes': stream.total_likes,
        'total_shares': stream.total_shares,
        'follows': Interaction.objects.filter(stream=stream, interaction_type='follow').count(),
        'total_gift_value': sum(
            i.gift_value for i in Interaction.objects.filter(stream=stream, interaction_type='gift')
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
