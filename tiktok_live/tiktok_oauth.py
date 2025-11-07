"""
TikTok OAuth Authentication Backend
"""
import requests
import hashlib
import base64
import secrets
import urllib.parse
from django.conf import settings
from django.contrib.auth.models import User
from .models import TikTokAccount

class TikTokOAuth:
    """TikTok OAuth handler with PKCE support"""
    
    AUTHORIZE_URL = "https://www.tiktok.com/v2/auth/authorize/"
    TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    USER_INFO_URL = "https://open.tiktokapis.com/v2/user/info/"
    
    # Required fields for TikTok API
    REQUIRED_FIELDS = ['open_id', 'union_id', 'avatar_url', 'display_name']
    
    def __init__(self, client_key=None, client_secret=None, redirect_uri=None):
        self.client_key = client_key or getattr(settings, 'TIKTOK_CLIENT_KEY', '')
        self.client_secret = client_secret or getattr(settings, 'TIKTOK_CLIENT_SECRET', '')
        self.redirect_uri = redirect_uri or getattr(settings, 'TIKTOK_REDIRECT_URI', '')
    
    def generate_code_verifier(self):
        """Generate PKCE code verifier"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    def generate_code_challenge(self, verifier):
        """Generate PKCE code challenge from verifier"""
        digest = hashlib.sha256(verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    
    def get_authorization_url(self, state=None, code_verifier=None):
        """Generate TikTok OAuth authorization URL with PKCE"""
        code_challenge = self.generate_code_challenge(code_verifier)
        
        params = {
            'client_key': self.client_key,
            'response_type': 'code',
            'scope': 'user.info.basic',
            'redirect_uri': self.redirect_uri,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        # URL encode parameters properly
        query_string = urllib.parse.urlencode(params)
        return f"{self.AUTHORIZE_URL}?{query_string}"
    
    def get_access_token(self, code, code_verifier):
        """Exchange authorization code for access token with PKCE"""
        data = {
            'client_key': self.client_key,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'code_verifier': code_verifier
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(self.TOKEN_URL, data=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    
    def get_user_info(self, access_token):
        """Get TikTok user information"""
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(self.USER_INFO_URL, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    
    def authenticate_user(self, request, code, code_verifier):
        """Authenticate user with TikTok OAuth code"""
        # Get access token
        token_data = self.get_access_token(code, code_verifier)
        if not token_data:
            return None, "Failed to get access token"
        
        access_token = token_data.get('access_token')
        if not access_token:
            return None, "No access token in response"
        
        # Get user info
        user_info = self.get_user_info(access_token)
        if not user_info:
            return None, "Failed to get user info"
        
        user_data = user_info.get('data', {}).get('user', {})
        tiktok_username = user_data.get('display_name', '') or user_data.get('username', '')
        tiktok_id = user_data.get('open_id', '') or user_data.get('union_id', '')
        
        if not tiktok_username:
            return None, "No username in TikTok response"
        
        # Create or get Django user
        username = f"tiktok_{tiktok_id}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f"{username}@tiktok.local"
            }
        )
        
        # Store TikTok username in user's first_name field
        if not user.first_name:
            user.first_name = tiktok_username
            user.save()
        
        # Create or update TikTok account
        account, _ = TikTokAccount.objects.get_or_create(
            user=user,
            username=tiktok_username,
            defaults={
                'is_verified': True,
                'display_name': user_data.get('display_name', ''),
                'profile_picture': user_data.get('avatar_url', '') or user_data.get('avatar_large_url', ''),
                'bio': user_data.get('bio_description', '')
            }
        )
        
        if not account.is_verified:
            account.is_verified = True
            account.save()
        
        # Account created successfully
        
        return user, None
