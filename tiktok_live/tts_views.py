from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json
import asyncio

@login_required
@require_http_methods(["POST"])
def tts_connect(request):
    try:
        from .connection_manager import connection_manager
        
        data = json.loads(request.body)
        username = data.get('username', '').replace('@', '').strip()
        
        if not username:
            return JsonResponse({'success': False, 'error': 'Username required'})
        
        async def connect():
            try:
                connector = await connection_manager.get_or_create_connection(username)
                return True
            except Exception as e:
                raise e
        
        success = asyncio.run(connect())
        
        return JsonResponse({
            'success': True,
            'message': f'Connected to @{username} for TTS',
            'username': username
        })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def tts_disconnect(request):
    try:
        from .connection_manager import connection_manager
        
        data = json.loads(request.body)
        username = data.get('username', '').replace('@', '').strip()
        
        if username:
            asyncio.run(connection_manager.close_connection(username))
        
        return JsonResponse({'success': True, 'message': 'Disconnected'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})