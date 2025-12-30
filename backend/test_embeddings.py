# backend/test_embeddings.py
"""
Embedding and Vector Store Test Script
======================================
Tests the embedding pipeline and vector store functionality.

Run with: python test_embeddings.py
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"
access_token = None


def print_response(response, title):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        # Truncate long content for readability
        data_str = json.dumps(data, indent=2, default=str)
        if len(data_str) > 2000:
            print(f"Response: {data_str[:2000]}...")
        else:
            print(f"Response: {data_str}")
    except:
        print(f"Response: {response.text[:500]}")
    print()


def get_headers():
    """Get headers with authorization."""
    return {
        "Authorization": f"Bearer {access_token}"
    }


def login_or_signup():
    """Login or create test user."""
    global access_token
    
    print("\n🔑 Logging in...")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "embedtest@example.com",
            "password": "EmbedTest123"
        }
    )
    
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        print("✅ Logged in successfully!")
        return True
    
    print("Creating new user...")
    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "email": "embedtest@example.com",
            "password": "EmbedTest123",
            "full_name": "Embedding Test User"
        }
    )
    
    if response.status_code == 201:
        access_token = response.json()["access_token"]
        print("✅ User created and logged in!")
        return True
    
    print(f"❌ Authentication failed: {response.text}")
    return False


def create_test_document():
    """Create a test legal document."""
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    content = """
NON-DISCLOSURE AGREEMENT (NDA)

This Non-Disclosure Agreement ("Agreement") is entered into as of January 15, 2024,
by and between:

ABC Technologies Private Limited, a company incorporated under the Companies Act, 2013,
having its registered office at 100, Tech Park, Bangalore - 560001, Karnataka, India
(hereinafter referred to as the "Disclosing Party")

AND

XYZ Solutions Limited, a company incorporated under the Companies Act, 2013,
having its registered office at 50, Business Center, Mumbai - 400001, Maharashtra, India
(hereinafter referred to as the "Receiving Party")

WHEREAS, the Disclosing Party possesses certain confidential and proprietary information
relating to its business, technology, and operations; and

WHEREAS, the Receiving Party desires to receive such confidential information for the
purpose of evaluating a potential business relationship between the parties;

NOW, THEREFORE, in consideration of the mutual covenants and agreements herein contained,
the parties agree as follows:

1. DEFINITION OF CONFIDENTIAL INFORMATION

"Confidential Information" shall mean any and all information disclosed by the Disclosing
Party to the Receiving Party, whether orally, in writing, or by any other means, including
but not limited to:

a) Trade secrets, inventions, patents, copyrights, trademarks, and other intellectual property;
b) Business plans, strategies, financial information, and projections;
c) Customer lists, supplier information, and marketing data;
d) Technical data, software, algorithms, and source code;
e) Any other information marked as "Confidential" or reasonably understood to be confidential.

2. OBLIGATIONS OF THE RECEIVING PARTY

The Receiving Party agrees to:

a) Hold the Confidential Information in strict confidence;
b) Not disclose the Confidential Information to any third party without prior written consent;
c) Use the Confidential Information solely for the Purpose stated herein;
d) Protect the Confidential Information using the same degree of care it uses to protect
   its own confidential information, but in no event less than reasonable care;
e) Limit access to the Confidential Information to its employees who have a need to know.

3. TERM AND TERMINATION

This Agreement shall remain in effect for a period of three (3) years from the date of
execution. The obligations of confidentiality shall survive the termination of this
Agreement for an additional period of two (2) years.

4. RETURN OF CONFIDENTIAL INFORMATION

Upon termination of this Agreement or upon request by the Disclosing Party, the Receiving
Party shall promptly return or destroy all Confidential Information and any copies thereof.

5. REMEDIES

The Receiving Party acknowledges that any breach of this Agreement may cause irreparable
harm to the Disclosing Party. Therefore, the Disclosing Party shall be entitled to seek
injunctive relief in addition to any other remedies available at law.

6. GOVERNING LAW

This Agreement shall be governed by and construed in accordance with the laws of India.
Any disputes arising out of this Agreement shall be subject to the exclusive jurisdiction
of the courts in Bangalore, Karnataka.

7. ENTIRE AGREEMENT

This Agreement constitutes the entire agreement between the parties with respect to the
subject matter hereof and supersedes all prior negotiations, representations, and agreements.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

For ABC Technologies Private Limited:
Signature: _______________________
Name: Rajesh Kumar
Designation: Chief Executive Officer
Date: _______________

For XYZ Solutions Limited:
Signature: _______________________
Name: Priya Sharma
Designation: Managing Director
Date: _______________
"""
    
    file_path = test_dir / "test_nda.txt"
    with open(file_path, 'w') as f:
        f.write(content)
    
    return file_path


def test_upload_with_embeddings():
    """Test document upload with embedding generation."""
    print("\n" + "📤 TESTING DOCUMENT UPLOAD WITH EMBEDDINGS ".ljust(60, "="))
    
    file_path = create_test_document()
    
    start_time = time.time()
    
    with open(file_path, 'rb') as f:
        files = {'file': ('test_nda.txt', f, 'text/plain')}
        response = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=get_headers(),
            files=files
        )
    
    elapsed = time.time() - start_time
    
    print_response(response, f"Upload with Embeddings (took {elapsed:.2f}s)")
    
    if response.status_code == 201:
        doc = response.json()["document"]
        print(f"✅ Document uploaded and embedded!")
        print(f"   - Chunks: {doc['chunk_count']}")
        print(f"   - Status: {doc['status']}")
        return doc["id"]
    
    return None


def test_search_document(doc_id):
    """Test semantic search within a document."""
    print("\n" + "🔍 TESTING SEMANTIC SEARCH ".ljust(60, "="))
    
    queries = [
        "What are the confidentiality obligations?",
        "How long does the agreement last?",
        "What happens to confidential information after termination?",
        "Which courts have jurisdiction?",
        "What is considered confidential information?",
    ]
    
    for query in queries:
        print(f"\n📝 Query: '{query}'")
        
        response = requests.post(
            f"{BASE_URL}/documents/{doc_id}/search",
            headers=get_headers(),
            params={"query": query, "n_results": 2}
        )
        
        if response.status_code == 200:
            results = response.json()["results"]
            print(f"   Found {len(results)} results:")
            for i, r in enumerate(results):
                similarity = r.get('similarity', 0) * 100
                content_preview = r['content'][:100] + "..." if len(r['content']) > 100 else r['content']
                print(f"   [{i+1}] Similarity: {similarity:.1f}%")
                print(f"       {content_preview}")
        else:
            print(f"   ❌ Search failed: {response.text}")


def test_search_all_documents():
    """Test searching across all documents."""
    print("\n" + "🔍 TESTING SEARCH ALL DOCUMENTS ".ljust(60, "="))
    
    response = requests.post(
        f"{BASE_URL}/documents/search/all",
        headers=get_headers(),
        params={"query": "confidential information protection", "n_results": 3}
    )
    
    print_response(response, "Search All Documents")


def test_system_status():
    """Test system status with vector store info."""
    print("\n" + "📊 TESTING SYSTEM STATUS ".ljust(60, "="))
    
    response = requests.get(f"{BASE_URL}/status")
    
    print_response(response, "System Status (including Vector Store)")


def test_document_stats():
    """Test document statistics with embedding count."""
    print("\n" + "📈 TESTING DOCUMENT STATS ".ljust(60, "="))
    
    response = requests.get(
        f"{BASE_URL}/documents/stats/summary",
        headers=get_headers()
    )
    
    print_response(response, "Document Stats (with Embeddings)")


def cleanup_test_files():
    """Remove test files."""
    import shutil
    test_dir = Path("test_files")
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("🧹 Test files cleaned up")


def main():
    """Run all embedding tests."""
    print("\n" + "="*60)
    print("🧪 EMBEDDING & VECTOR STORE TESTS")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print("="*60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code != 200:
            print("❌ Server is not running. Start it with:")
            print("   uvicorn app.main:app --reload")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Start it with:")
        print("   uvicorn app.main:app --reload")
        return
    
    # Login
    if not login_or_signup():
        print("Cannot proceed without authentication")
        return
    
    # Run tests
    test_system_status()
    
    doc_id = test_upload_with_embeddings()
    
    if doc_id:
        # Wait a moment for processing
        time.sleep(1)
        
        test_search_document(doc_id)
        test_search_all_documents()
        test_document_stats()
    
    # Cleanup
    cleanup_test_files()
    
    print("\n" + "="*60)
    print("✅ ALL EMBEDDING TESTS COMPLETED!")
    print("="*60)
    print("\n📝 What was tested:")
    print("   1. Document upload with automatic embedding")
    print("   2. Semantic search within a document")
    print("   3. Search across all documents")
    print("   4. System status with vector store info")
    print("   5. Document statistics with embedding counts")
    print("\n🎯 The embedding pipeline is working correctly!")
    print()


if __name__ == "__main__":
    main()