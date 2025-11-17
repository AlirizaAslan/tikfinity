from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import StreamInteraction, TikTokAccount
import json

@login_required
def lastx_overlays(request):
    """Last X Overlays page"""
    return render(request, 'tiktok_live/lastx_overlays.html')

def lastx_widget(request):
    """Widget endpoint for Last X overlays"""
    widget_type = request.GET.get('type', 'follower')
    user_id = request.GET.get('user')
    preview = request.GET.get('preview', '0') == '1'
    test = request.GET.get('test', '0') == '1'
    
    last_user = None
    
    if user_id and not test:
        try:
            # Map widget types to interaction types
            interaction_mapping = {
                'follower': 'follow',
                'gifter': 'gift',
                'chatter': 'comment',
                'like': 'like',
                'share': 'share',
                'subscriber': 'subscribe'
            }
            
            interaction_type = interaction_mapping.get(widget_type, widget_type)
            
            # Get the last interaction of the specified type
            interaction = StreamInteraction.objects.filter(
                stream__account__user_id=user_id,
                interaction_type=interaction_type
            ).order_by('-timestamp').first()
            
            if interaction:
                last_user = {
                    'username': interaction.username,
                    'timestamp': interaction.timestamp
                }
        except Exception as e:
            pass
    
    # Test data
    if test or not last_user:
        test_users = {
            'follower': 'TestFollower123',
            'gifter': 'TestGifter456', 
            'subscriber': 'TestSubscriber789',
            'share': 'TestSharer101',
            'like': 'TestLiker202',
            'chatter': 'TestChatter303'
        }
        last_user = {
            'username': test_users.get(widget_type, 'TestUser'),
            'timestamp': timezone.now()
        }
    
    return render(request, 'tiktok_live/lastx_widget.html', {
        'type': widget_type,
        'last_user': last_user,
        'preview': preview,
        'user_id': user_id
    })

@require_http_methods(["POST"])
def lastx_test(request):
    """Trigger test data for widget"""
    try:
        data = json.loads(request.body)
        widget_type = data.get('type')
        user_id = data.get('user_id')
        
        # Create test interaction
        from .models import TikTokAccount, LiveStream
        
        account, _ = TikTokAccount.objects.get_or_create(
            user_id=user_id,
            defaults={'username': 'test_account'}
        )
        
        stream, _ = LiveStream.objects.get_or_create(
            account=account,
            is_active=True,
            defaults={'stream_id': f'test_{timezone.now().timestamp()}'}
        )
        
        test_usernames = {
            'follower': 'TestFollower123',
            'gifter': 'TestGifter456', 
            'subscriber': 'TestSubscriber789',
            'share': 'TestSharer101',
            'like': 'TestLiker202',
            'chatter': 'TestChatter303'
        }
        
        StreamInteraction.objects.create(
            stream=stream,
            interaction_type=widget_type,
            username=test_usernames.get(widget_type, 'TestUser'),
            message='Test message' if widget_type == 'chatter' else '',
            gift_name='Test Gift' if widget_type == 'gifter' else ''
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})