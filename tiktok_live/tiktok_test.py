"""Test TikTok OAuth Configuration"""
from django.conf import settings

def test_oauth_config():
    """Test OAuth configuration"""
    print("\n" + "="*50)
    print("TikTok OAuth Configuration Test")
    print("="*50)
    
    client_key = getattr(settings, 'TIKTOK_CLIENT_KEY', '')
    client_secret = getattr(settings, 'TIKTOK_CLIENT_SECRET', '')
    redirect_uri = getattr(settings, 'TIKTOK_REDIRECT_URI', '')
    
    print(f"\nClient Key: {client_key}")
    print(f"Client Key Length: {len(client_key)}")
    print(f"Client Key Type: {type(client_key)}")
    
    print(f"\nClient Secret: {client_secret[:10]}...")
    print(f"Client Secret Length: {len(client_secret)}")
    
    print(f"\nRedirect URI: {redirect_uri}")
    
    # Check for issues
    issues = []
    if not client_key:
        issues.append("❌ Client Key is empty")
    if not client_secret:
        issues.append("❌ Client Secret is empty")
    if not redirect_uri:
        issues.append("❌ Redirect URI is empty")
    if ' ' in client_key:
        issues.append("❌ Client Key contains spaces")
    if ' ' in client_secret:
        issues.append("❌ Client Secret contains spaces")
    
    if issues:
        print("\n⚠️  Issues Found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ Configuration looks good!")
    
    print("\n" + "="*50 + "\n")
    
    return len(issues) == 0
