from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Action, Event, OverlayScreen, Timer
import json

def actions_and_events(request):
    """Actions & Events page using layout template"""
    tiktok_username = request.session.get('tiktok_username', '')
    
    context = {
        'tiktok_username': tiktok_username,
        'actions': [],
        'events': [],
        'screens': [{'id': i, 'name': f'Screen {i}', 'url': f'https://tikfinity.zerody.one/widget/myactions?cid=2449591&screen={i}', 'max_queue': 5, 'status': 'Offline'} for i in range(1, 9)],
        'timers': [],
        'actions_enabled': True
    }
    
    return render(request, 'tiktok_live/actions_events_layout.html', context)

@require_http_methods(["POST"])
def create_action(request):
    """Create new action"""
    try:
        data = json.loads(request.body)
        return JsonResponse({
            'success': True,
            'message': 'Action created successfully (demo)'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["POST"])
def create_event(request):
    """Create new event"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        
        event = Event.objects.create(
            user=request.user,
            trigger_type=data.get('trigger_type'),
            trigger_user=data.get('trigger_user', 'any'),
            specific_user=data.get('specific_user', ''),
            min_coins=data.get('min_coins', 0),
            min_likes=data.get('min_likes', 0),
            specific_gift=data.get('specific_gift', ''),
            custom_command=data.get('custom_command', ''),
            min_trigger_level=data.get('min_trigger_level', 0),
            actions=data.get('actions', []),
            random_actions=data.get('random_actions', []),
            is_active=data.get('is_active', True)
        )
        
        return JsonResponse({
            'success': True,
            'event_id': event.id,
            'message': 'Event created successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["POST"])
def simulate_event(request):
    """Simulate events for testing"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        event_type = data.get('event_type')
        
        # Simulate different event types
        simulation_data = {
            'follow': {'username': 'TestUser', 'event': 'follow'},
            'share': {'username': 'TestUser', 'event': 'share'},
            'subscribe': {'username': 'TestUser', 'event': 'subscribe'},
            'like': {'username': 'TestUser', 'event': 'like', 'count': 15},
            'gift': {
                'username': 'TestUser', 
                'event': 'gift',
                'gift_name': data.get('gift_name', 'Rose'),
                'coins': data.get('coins', 1),
                'repeat_count': 1
            }
        }
        
        if event_type in simulation_data:
            # Here you would trigger the actual action execution
            # For now, just return success
            return JsonResponse({
                'success': True,
                'message': f'{event_type.title()} event simulated',
                'data': simulation_data[event_type]
            })
        else:
            return JsonResponse({'error': 'Invalid event type'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["POST"])
def create_timer(request):
    """Create new timer"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        
        timer = Timer.objects.create(
            user=request.user,
            interval_minutes=data.get('interval_minutes', 5),
            action_id=data.get('action_id'),
            is_active=data.get('is_active', True)
        )
        
        return JsonResponse({
            'success': True,
            'timer_id': timer.id,
            'message': 'Timer created successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["POST"])
def update_screen_settings(request):
    """Update overlay screen settings"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        screen_id = data.get('screen_id')
        max_queue = data.get('max_queue', 5)
        
        # In a real implementation, you'd save this to database
        # For now, just return success
        return JsonResponse({
            'success': True,
            'message': f'Screen {screen_id} settings updated',
            'max_queue': max_queue
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)