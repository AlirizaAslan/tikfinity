from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from django.contrib.auth.models import User
import secrets
import hashlib
import base64

class GoogleOAuth:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        self.token_url = 'https://oauth2.googleapis.com/token'
    
    def get_authorization_url(self):
        """Generate Google OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f'{self.auth_url}?{query_string}'
    
    def get_access_token(self, code):
        """Exchange authorization code for access token"""
        import requests as req
        
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        response = req.post(self.token_url, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Failed to get access token: {response.text}')
    
    def verify_token(self, token):
        """Verify Google ID token and get user info"""
        try:
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                self.client_id
            )
            return idinfo
        except Exception as e:
            raise Exception(f'Token verification failed: {str(e)}')
    
    def authenticate_user(self, code):
        """Authenticate user with Google OAuth"""
        token_data = self.get_access_token(code)
        id_token_str = token_data.get('id_token')
        
        if not id_token_str:
            raise Exception('No ID token received')
        
        user_info = self.verify_token(id_token_str)
        
        email = user_info.get('email')
        name = user_info.get('name', '')
        google_id = user_info.get('sub')
        
        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0] + '_' + google_id[:8],
                'first_name': name.split()[0] if name else '',
                'last_name': ' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
            }
        )
        
        return user, created
