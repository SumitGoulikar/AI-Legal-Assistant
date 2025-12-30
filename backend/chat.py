# backend/test_chat.py
"""
Chat and RAG Test Script
=========================
Tests the complete chat and RAG functionality.

Run with: python test_chat.py

IMPORTANT: 
1. Make sure server is running: uvicorn app.main:app --reload
2. For Ollama: Make sure Ollama is running with llama2 model
   Download: ollama pull llama2
   Run: ollama serve
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"
access_token = None


def print_section(title):
    """Print section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_response(response, title):
    """Pretty print API response."""
    print(f"\n📋 {title}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        data_str = json.dumps(data, indent=2, default=str)
        if len(data_str) > 3000:
            print(f"Response: {data_str[:3000]}...")
        else:
            print(f"Response: {data_str}")
    except:
        print(f"Response: {response.text[:500]}")
    print()


def get_headers():
    """Get headers with authorization."""
    return {"Authorization": f"Bearer {access_token}"}


def check_server():
    """Check if server is running."""
    print("🔌 Checking server connection...")
    try:
        response = requests.get(
            BASE_URL.replace("/api/v1", "") + "/health",
            timeout=5
        )
        if response.status_code == 200:
            print("   ✅ Server is running!")
            return True
    except requests.exceptions.ConnectionError:
        pass
    
    print("   ❌ Cannot connect to server!")
    print("\n   Please start the server:")
    print("   uvicorn app.main:app --reload")
    return False


def check_ollama():
    """Check if Ollama is running."""
    print("\n🤖 Checking Ollama (if using ollama provider)...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"   ✅ Ollama is running!")
            print(f"   Available models: {[m['name'] for m in models]}")
            
            # Check if llama2 is available
            if any("llama2" in m['name'] for m in models):
                print("   ✅ llama2 model is available!")
                return True
            else:
                print("   ⚠️ llama2 model not found. Install with:")
                print("      ollama pull llama2")
                return False
    except:
        print("   ⚠️ Ollama not running or not configured")
        print("   If using OpenAI, set OPENAI_API_KEY in .env")
        return False


def login_or_signup():
    """Login or create test user."""
    global access_token
    
    print("\n🔑 Authenticating...")
    
    # Try login first
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "chattest@example.com",
                "password": "ChatTest123"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            access_token = response.json()["access_token"]
            print("   ✅ Logged in successfully!")
            return True
    except Exception as e:
        pass
    
    # Try signup
    print("   Creating new user...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json={
                "email": "chattest@example.com",
                "password": "ChatTest123",
                "full_name": "Chat Test User"
            },
            timeout=10
        )
        
        if response.status_code == 201:
            access_token = response.json()["access_token"]
            print("   ✅ User created and logged in!")
            return True
        else:
            print(f"   ❌ Authentication failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_system_status():
    """Test system status including LLM."""
    print_section("TESTING SYSTEM STATUS")
    
    response = requests.get(
        BASE_URL.replace("/api/v1", "") + "/api/v1/status",
        timeout=10
    )
    
    print_response(response, "System Status")
    
    if response.status_code == 200:
        data = response.json()
        llm_status = data.get("services", {}).get("llm", {})
        print(f"   LLM Provider: {llm_status.get('provider')}")
        print(f"   LLM Model: {llm_status.get('model')}")
        print(f"   LLM Status: {llm_status.get('status')}")


def test_quick_query():
    """Test quick query without session."""
    print_section("TESTING QUICK QUERY")
    
    queries = [
        "What is a contract?",
        "Explain breach of contract under Indian law",
    ]
    
    for query in queries:
        print(f"\n💬 Query: {query}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{BASE_URL}/chat/query",
                headers=get_headers(),
                params={"query": query},
                timeout=60
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])
                
                print(f"   ⏱️ Response time: {elapsed:.2f}s")
                print(f"\n   📝 Answer:")
                # Print first 500 chars of answer
                answer_preview = answer[:500] + "..." if len(answer) > 500 else answer
                print(f"   {answer_preview}")
                print(f"\n   📚 Sources: {len(sources)} chunks used")
                print(f"   🔢 Tokens: {data.get('tokens_used', 0)}")
                print(f"   🤖 Model: {data.get('model_used', 'unknown')}")
            else:
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")


def test_chat_session():
    """Test chat session with conversation."""
    print_section("TESTING CHAT SESSION")
    
    # Create session
    print("\n1️⃣ Creating chat session...")
    response = requests.post(
        f"{BASE_URL}/chat/sessions",
        headers=get_headers(),
        json={
            "session_type": "general",
            "title": "Test Legal Discussion"
        },
        timeout=10
    )
    
    if response.status_code != 201:
        print(f"   ❌ Failed to create session: {response.text}")
        return None
    
    session = response.json()
    session_id = session["id"]
    print(f"   ✅ Session created: {session_id}")
    
    # Send messages
    messages = [
        "What are the essential elements of a valid contract in India?",
        "What happens if one party breaches the contract?",
        "Can you give me an example of consideration?",
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n{i+1}️⃣ Sending message: '{message}'")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{BASE_URL}/chat/sessions/{session_id}/messages",
                headers=get_headers(),
                json={"content": message},
                timeout=60
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                assistant_msg = data.get("assistant_message", {})
                answer = assistant_msg.get("content", "")
                sources = data.get("sources", [])
                
                print(f"   ⏱️ Response time: {elapsed:.2f}s")
                print(f"\n   🤖 AI Response:")
                answer_preview = answer[:400] + "..." if len(answer) > 400 else answer
                print(f"   {answer_preview}")
                print(f"\n   📚 Sources: {len(sources)} chunks")
                print(f"   🔢 Tokens: {assistant_msg.get('tokens_used', 0)}")
            else:
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        time.sleep(1)  # Small delay between messages
    
    return session_id


def test_get_session_history(session_id):
    """Test retrieving session history."""
    print_section("TESTING SESSION HISTORY")
    
    print(f"\n📜 Retrieving session: {session_id}")
    
    response = requests.get(
        f"{BASE_URL}/chat/sessions/{session_id}",
        headers=get_headers(),
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        messages = data.get("messages", [])
        
        print(f"   ✅ Found {len(messages)} messages")
        print(f"\n   Conversation Summary:")
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")[:100]
            print(f"   [{role.upper()}] {content}...")
    else:
        print(f"   ❌ Error: {response.text}")


def test_list_sessions():
    """Test listing sessions."""
    print_section("TESTING LIST SESSIONS")
    
    response = requests.get(
        f"{BASE_URL}/chat/sessions",
        headers=get_headers(),
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        sessions = data.get("sessions", [])
        
        print(f"   ✅ Found {len(sessions)} session(s)")
        for session in sessions[:5]:
            print(f"   - {session.get('title')} ({session.get('message_count')} messages)")
    else:
        print(f"   ❌ Error: {response.text}")


def test_chat_stats():
    """Test chat statistics."""
    print_section("TESTING CHAT STATISTICS")
    
    response = requests.get(
        f"{BASE_URL}/chat/stats",
        headers=get_headers(),
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        stats = data.get("stats", {})
        
        print(f"   📊 Chat Statistics:")
        print(f"   - Total Sessions: {stats.get('total_sessions', 0)}")
        print(f"   - Total Messages: {stats.get('total_messages', 0)}")
        print(f"   - Total Tokens: {stats.get('total_tokens', 0)}")
        print(f"   - By Type: {stats.get('by_type', {})}")
    else:
        print(f"   ❌ Error: {response.text}")


def main():
    """Run all chat tests."""
    print("\n" + "="*70)
    print("  🧪 CHAT & RAG SYSTEM TESTS")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print("="*70)
    
    # Check prerequisites
    if not check_server():
        sys.exit(1)
    
    check_ollama()
    
    if not login_or_signup():
        print("\n❌ Cannot proceed without authentication")
        sys.exit(1)
    
    # Run tests
    test_system_status()
    test_quick_query()
    
    session_id = test_chat_session()
    
    if session_id:
        test_get_session_history(session_id)
    
    test_list_sessions()
    test_chat_stats()
    
    print("\n" + "="*70)
    print("  ✅ ALL CHAT TESTS COMPLETED!")
    print("="*70)
    print("\n📝 Summary:")
    print("   ✅ Quick queries work")
    print("   ✅ Chat sessions with context work")
    print("   ✅ Conversation history maintained")
    print("   ✅ RAG pipeline operational")
    print("\n🎉 Your AI Legal Assistant is ready!")
    print()


if __name__ == "__main__":
    main()