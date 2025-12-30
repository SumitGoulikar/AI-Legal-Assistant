# backend/test_both_llms.py
"""
Test Both LLM Providers
========================
Tests Ollama and OpenAI to verify both work.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
access_token = None


def login():
    """Login to get token."""
    global access_token
    
    print("🔑 Logging in...")
    
    # Try login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "llmtest@example.com",
            "password": "LlmTest123"
        }
    )
    
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        print("   ✅ Logged in!\n")
        return True
    
    # Try signup
    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "email": "llmtest@example.com",
            "password": "LlmTest123",
            "full_name": "LLM Test User"
        }
    )
    
    if response.status_code == 201:
        access_token = response.json()["access_token"]
        print("   ✅ User created!\n")
        return True
    
    return False


def test_query(provider_name):
    """Test a query with current provider."""
    print(f"\n{'='*60}")
    print(f"  TESTING {provider_name.upper()}")
    print(f"{'='*60}\n")
    
    query = "What is a contract in one sentence?"
    
    print(f"💬 Query: {query}")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/chat/query",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"query": query},
            timeout=60
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            
            print(f"\n⏱️  Response time: {elapsed:.2f}s")
            print(f"🤖 Model: {data.get('model_used', 'unknown')}")
            print(f"🔢 Tokens: {data.get('tokens_used', 0)}")
            print(f"\n📝 Answer:")
            # Show first 300 chars
            answer_preview = answer[:300] + "..." if len(answer) > 300 else answer
            print(f"{answer_preview}\n")
            
            return True
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"{response.text}\n")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception: {e}\n")
        return False


def check_status():
    """Check which provider is currently active."""
    try:
        response = requests.get(
            BASE_URL.replace("/api/v1", "") + "/api/v1/status"
        )
        
        if response.status_code == 200:
            data = response.json()
            llm_info = data.get("services", {}).get("llm", {})
            
            return {
                "provider": llm_info.get("provider"),
                "model": llm_info.get("model"),
                "status": llm_info.get("status"),
            }
    except:
        pass
    
    return None


def main():
    """Test both providers."""
    print("\n" + "="*60)
    print("  🧪 TESTING BOTH LLM PROVIDERS")
    print("="*60)
    
    # Check server
    print("\n🔌 Checking server...")
    try:
        response = requests.get(
            BASE_URL.replace("/api/v1", "") + "/health",
            timeout=5
        )
        if response.status_code != 200:
            print("   ❌ Server not running!")
            print("   Start with: uvicorn app.main:app --reload")
            return
    except:
        print("   ❌ Cannot connect to server!")
        print("   Start with: uvicorn app.main:app --reload")
        return
    
    print("   ✅ Server is running!")
    
    # Login
    if not login():
        print("❌ Authentication failed!")
        return
    
    # Check current provider
    status = check_status()
    if status:
        print(f"📊 Current configuration:")
        print(f"   Provider: {status['provider']}")
        print(f"   Model: {status['model']}")
        print(f"   Status: {status['status']}")
    
    # Test current provider
    if status and status['provider'] == 'ollama':
        test_query("Ollama")
        
        print("\n" + "="*60)
        print("  📝 To test OpenAI:")
        print("="*60)
        print("1. Edit backend/.env")
        print("2. Change: LLM_PROVIDER=openai")
        print("3. Restart server: uvicorn app.main:app --reload")
        print("4. Run: python test_both_llms.py")
        
    elif status and status['provider'] == 'openai':
        test_query("OpenAI")
        
        print("\n" + "="*60)
        print("  📝 To test Ollama:")
        print("="*60)
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Edit backend/.env")
        print("3. Change: LLM_PROVIDER=ollama")
        print("4. Restart server: uvicorn app.main:app --reload")
        print("5. Run: python test_both_llms.py")
    else:
        print("\n⚠️ LLM provider not properly configured!")
    
    print("\n" + "="*60)
    print("  ✅ TEST COMPLETED")
    print("="*60)
    print()


if __name__ == "__main__":
    main()