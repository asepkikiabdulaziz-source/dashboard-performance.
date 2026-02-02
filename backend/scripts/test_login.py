#!/usr/bin/env python3
"""
Script to test login functionality
Usage: python scripts/test_login.py <email> <password>
"""
import sys
import os
import requests
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

def test_login(email, password):
    """Test login with Supabase Auth directly"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ ERROR: SUPABASE_URL or SUPABASE_KEY not set in environment")
        print(f"   SUPABASE_URL: {'SET' if url else 'NOT SET'}")
        print(f"   SUPABASE_KEY: {'SET' if key else 'NOT SET'}")
        return False
    
    print(f"🔍 Testing login for: {email}")
    print(f"📍 Supabase URL: {url[:50]}...")
    
    try:
        # Test Supabase Auth endpoint
        api_url = f"{url}/auth/v1/token?grant_type=password"
        headers = {
            "apikey": key,
            "Content-Type": "application/json"
        }
        payload = {
            "email": email,
            "password": password
        }
        
        print(f"🌐 Calling: {api_url}")
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            user = data.get("user")
            
            if access_token and user:
                print("✅ Login successful!")
                print(f"   User ID: {user.get('id')}")
                print(f"   Email: {user.get('email')}")
                print(f"   Token: {access_token[:50]}...")
                return True
            else:
                print("❌ Login response missing access_token or user")
                return False
        else:
            print(f"❌ Login failed!")
            print(f"   Response: {response.text[:500]}")
            try:
                error_data = response.json()
                if 'error' in error_data:
                    print(f"   Error: {error_data.get('error')}")
                if 'error_description' in error_data:
                    print(f"   Description: {error_data.get('error_description')}")
            except:
                pass
            return False
            
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timeout (Supabase not responding)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to Supabase (check URL)")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/test_login.py <email> <password>")
        print("\nExample:")
        print("  python scripts/test_login.py admin@company.com admin123")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    success = test_login(email, password)
    sys.exit(0 if success else 1)
