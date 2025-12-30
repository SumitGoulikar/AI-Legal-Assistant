# backend/test_auth.py
"""
Authentication Test Script
==========================
Tests the complete authentication flow:
1. Signup
2. Login
3. Get current user
4. Update profile
5. Change password
6. Verify token

Run with: python test_auth.py
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Store token for authenticated requests
access_token = None


def print_response(response, title):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()


def get_headers():
    """Get headers with authorization if token exists."""
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def test_signup():
    """Test user registration."""
    global access_token
    
    print("\n" + "🔐 TESTING SIGNUP ".ljust(60, "="))
    
    # Test with valid data
    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "email": "testuser@example.com",
            "password": "SecurePass123",
            "full_name": "Test User"
        }
    )
    print_response(response, "Signup - Valid Data")
    
    if response.status_code == 201:
        data = response.json()
        access_token = data.get("access_token")
        print(f"✅ Signup successful! Token received.")
        return True
    elif response.status_code == 409:
        print(f"ℹ️ User already exists, will try login instead.")
        return False
    else:
        print(f"❌ Signup failed!")
        return False


def test_signup_validation():
    """Test signup validation errors."""
    print("\n" + "🔐 TESTING SIGNUP VALIDATION ".ljust(60, "="))
    
    # Test with weak password
    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "email": "weak@example.com",
            "password": "weak",  # Too short, no uppercase, no digit
            "full_name": "Weak Password User"
        }
    )
    print_response(response, "Signup - Weak Password (should fail)")
    
    # Test with invalid email
    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "email": "not-an-email",
            "password": "SecurePass123",
            "full_name": "Invalid Email User"
        }
    )
    print_response(response, "Signup - Invalid Email (should fail)")


def test_login():
    """Test user login."""
    global access_token
    
    print("\n" + "🔑 TESTING LOGIN ".ljust(60, "="))
    
    # Test with valid credentials
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "SecurePass123"
        }
    )
    print_response(response, "Login - Valid Credentials")
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        print(f"✅ Login successful! Token received.")
        return True
    else:
        print(f"❌ Login failed!")
        return False


def test_login_invalid():
    """Test login with invalid credentials."""
    print("\n" + "🔑 TESTING LOGIN VALIDATION ".ljust(60, "="))
    
    # Test with wrong password
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "WrongPassword123"
        }
    )
    print_response(response, "Login - Wrong Password (should fail)")
    
    # Test with non-existent email
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SecurePass123"
        }
    )
    print_response(response, "Login - Non-existent User (should fail)")


def test_get_me():
    """Test getting current user profile."""
    print("\n" + "👤 TESTING GET CURRENT USER ".ljust(60, "="))
    
    # With valid token
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers=get_headers()
    )
    print_response(response, "Get Current User - With Token")
    
    # Without token
    response = requests.get(
        f"{BASE_URL}/auth/me"
    )
    print_response(response, "Get Current User - No Token (should fail)")


def test_update_me():
    """Test updating user profile."""
    print("\n" + "✏️ TESTING UPDATE PROFILE ".ljust(60, "="))
    
    response = requests.put(
        f"{BASE_URL}/auth/me",
        headers=get_headers(),
        json={
            "full_name": "Updated Test User"
        }
    )
    print_response(response, "Update Profile")


def test_verify_token():
    """Test token verification."""
    print("\n" + "✅ TESTING TOKEN VERIFICATION ".ljust(60, "="))
    
    response = requests.get(
        f"{BASE_URL}/auth/verify",
        headers=get_headers()
    )
    print_response(response, "Verify Token")


def test_user_stats():
    """Test getting user statistics."""
    print("\n" + "📊 TESTING USER STATS ".ljust(60, "="))
    
    response = requests.get(
        f"{BASE_URL}/auth/stats",
        headers=get_headers()
    )
    print_response(response, "User Stats")


def test_change_password():
    """Test changing password."""
    print("\n" + "🔒 TESTING PASSWORD CHANGE ".ljust(60, "="))
    
    # Change password
    response = requests.put(
        f"{BASE_URL}/auth/password",
        headers=get_headers(),
        json={
            "current_password": "SecurePass123",
            "new_password": "NewSecurePass456"
        }
    )
    print_response(response, "Change Password")
    
    if response.status_code == 200:
        # Try logging in with new password
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "NewSecurePass456"
            }
        )
        print_response(response, "Login with New Password")
        
        # Change back to original password
        if response.status_code == 200:
            global access_token
            access_token = response.json().get("access_token")
            
            requests.put(
                f"{BASE_URL}/auth/password",
                headers=get_headers(),
                json={
                    "current_password": "NewSecurePass456",
                    "new_password": "SecurePass123"
                }
            )
            print("   ↩️ Password reverted to original for future tests")


def test_invalid_token():
    """Test with invalid token."""
    print("\n" + "🚫 TESTING INVALID TOKEN ".ljust(60, "="))
    
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    print_response(response, "Get User with Invalid Token (should fail)")


def main():
    """Run all authentication tests."""
    print("\n" + "="*60)
    print("🧪 AUTHENTICATION SYSTEM TESTS")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print("="*60)
    
    # Run tests
    signup_success = test_signup()
    test_signup_validation()
    
    if not signup_success:
        test_login()
    
    test_login_invalid()
    test_get_me()
    test_update_me()
    test_verify_token()
    test_user_stats()
    test_change_password()
    test_invalid_token()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED!")
    print("="*60)
    print("\n📝 Summary:")
    print("   - If you see 2xx responses for valid requests: ✅ Working")
    print("   - If you see 4xx responses for invalid requests: ✅ Validation working")
    print("   - Check the Swagger UI at http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    main()