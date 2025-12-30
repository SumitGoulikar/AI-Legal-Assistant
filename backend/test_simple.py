# backend/test_simple.py
"""Simple test to verify API connection."""

import requests

print("=" * 50)
print("🧪 SIMPLE API TEST")
print("=" * 50)

BASE_URL = "http://localhost:8000"

# Test 1: Health check
print("\n1️⃣ Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except requests.exceptions.ConnectionError:
    print("   ❌ Cannot connect! Is the server running?")
    print("   Run: uvicorn app.main:app --reload")
    exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 2: API info
print("\n2️⃣ Testing API info...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/info", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   App: {data['data']['app_name']}")
        print(f"   Version: {data['data']['version']}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Signup
print("\n3️⃣ Testing signup...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/signup",
        json={
            "email": "simpletest@example.com",
            "password": "SimpleTest123",
            "full_name": "Simple Test"
        },
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        print("   ✅ Signup successful!")
        token = response.json()["access_token"]
        print(f"   Token: {token[:50]}...")
    elif response.status_code == 409:
        print("   ℹ️ User already exists, trying login...")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": "simpletest@example.com",
                "password": "SimpleTest123"
            },
            timeout=10
        )
        if response.status_code == 200:
            print("   ✅ Login successful!")
            token = response.json()["access_token"]
        else:
            print(f"   ❌ Login failed: {response.text}")
    else:
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 50)
print("✅ Simple test completed!")
print("=" * 50)