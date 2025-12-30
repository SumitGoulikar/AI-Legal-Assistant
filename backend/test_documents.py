# backend/test_documents.py
"""
Document Upload Test Script
===========================
Tests the complete document upload and management flow.

Run with: python test_documents.py
"""

import requests
import json
import os
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
        print(f"Response: {json.dumps(data, indent=2, default=str)}")
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
    
    # Try login first
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "doctest@example.com",
            "password": "DocTest123"
        }
    )
    
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        print("✅ Logged in successfully!")
        return True
    
    # If login fails, signup
    print("Creating new user...")
    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "email": "doctest@example.com",
            "password": "DocTest123",
            "full_name": "Document Test User"
        }
    )
    
    if response.status_code == 201:
        access_token = response.json()["access_token"]
        print("✅ User created and logged in!")
        return True
    
    print(f"❌ Authentication failed: {response.text}")
    return False


def create_sample_files():
    """Create sample files for testing."""
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # Create sample TXT file
    txt_path = test_dir / "sample_contract.txt"
    txt_content = """
SAMPLE SERVICE AGREEMENT

This Service Agreement ("Agreement") is entered into as of January 15, 2024
("Effective Date") by and between:

Party A: ABC Corporation, a company incorporated under the laws of India,
having its registered office at 123 Business Park, Mumbai, Maharashtra
("Service Provider")

AND

Party B: XYZ Limited, a company incorporated under the laws of India,
having its registered office at 456 Tech Hub, Bangalore, Karnataka
("Client")

WHEREAS, the Service Provider is engaged in the business of providing
software development and IT consulting services; and

WHEREAS, the Client desires to engage the Service Provider to provide
certain services as described herein;

NOW, THEREFORE, in consideration of the mutual covenants and agreements
set forth herein, the parties agree as follows:

1. SERVICES
The Service Provider agrees to provide the following services to the Client:
a) Software development and maintenance
b) Technical consultation and support
c) System integration services
d) Training and documentation

2. TERM
This Agreement shall commence on the Effective Date and shall continue
for a period of twelve (12) months unless terminated earlier in accordance
with the provisions hereof.

3. COMPENSATION
The Client agrees to pay the Service Provider a monthly fee of INR 5,00,000
(Rupees Five Lakhs Only) for the services rendered under this Agreement.

4. CONFIDENTIALITY
Both parties agree to maintain the confidentiality of all proprietary
information exchanged during the course of this Agreement.

5. TERMINATION
Either party may terminate this Agreement by providing thirty (30) days
written notice to the other party.

6. GOVERNING LAW
This Agreement shall be governed by and construed in accordance with the
laws of India. Any disputes arising out of this Agreement shall be subject
to the exclusive jurisdiction of the courts in Mumbai.

7. ENTIRE AGREEMENT
This Agreement constitutes the entire agreement between the parties and
supersedes all prior negotiations, representations, or agreements relating
to the subject matter hereof.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the
date first written above.

For ABC Corporation:               For XYZ Limited:
_____________________             _____________________
Authorized Signatory              Authorized Signatory
Date:                             Date:
"""
    
    with open(txt_path, 'w') as f:
        f.write(txt_content)
    
    print(f"✅ Created sample file: {txt_path}")
    return txt_path


def test_upload_document():
    """Test document upload."""
    print("\n" + "📤 TESTING DOCUMENT UPLOAD ".ljust(60, "="))
    
    # Create sample file
    txt_path = create_sample_files()
    
    # Upload the file
    with open(txt_path, 'rb') as f:
        files = {'file': ('sample_contract.txt', f, 'text/plain')}
        response = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=get_headers(),
            files=files
        )
    
    print_response(response, "Upload TXT Document")
    
    if response.status_code == 201:
        doc_id = response.json()["document"]["id"]
        print(f"✅ Document uploaded! ID: {doc_id}")
        return doc_id
    else:
        print("❌ Upload failed!")
        return None


def test_list_documents():
    """Test listing documents."""
    print("\n" + "📋 TESTING LIST DOCUMENTS ".ljust(60, "="))
    
    response = requests.get(
        f"{BASE_URL}/documents",
        headers=get_headers()
    )
    
    print_response(response, "List Documents")
    
    if response.status_code == 200:
        docs = response.json()["documents"]
        print(f"✅ Found {len(docs)} document(s)")
        return docs
    return []


def test_get_document(doc_id):
    """Test getting document details."""
    print("\n" + "🔍 TESTING GET DOCUMENT ".ljust(60, "="))
    
    response = requests.get(
        f"{BASE_URL}/documents/{doc_id}",
        headers=get_headers()
    )
    
    print_response(response, "Get Document Details")


def test_get_document_content(doc_id):
    """Test getting document content."""
    print("\n" + "📄 TESTING GET DOCUMENT CONTENT ".ljust(60, "="))
    
    response = requests.get(
        f"{BASE_URL}/documents/{doc_id}/content",
        headers=get_headers()
    )
    
    print_response(response, "Get Document Content")


def test_get_document_chunks(doc_id):
    """Test getting document chunks."""
    print("\n" + "🧩 TESTING GET DOCUMENT CHUNKS ".ljust(60, "="))
    
    response = requests.get(
        f"{BASE_URL}/documents/{doc_id}/chunks",
        headers=get_headers()
    )
    
    print_response(response, "Get Document Chunks")


def test_document_stats():
    """Test document statistics."""
    print("\n" + "📊 TESTING DOCUMENT STATS ".ljust(60, "="))
    
    response = requests.get(
        f"{BASE_URL}/documents/stats/summary",
        headers=get_headers()
    )
    
    print_response(response, "Document Statistics")


def test_delete_document(doc_id):
    """Test document deletion."""
    print("\n" + "🗑️ TESTING DELETE DOCUMENT ".ljust(60, "="))
    
    response = requests.delete(
        f"{BASE_URL}/documents/{doc_id}",
        headers=get_headers()
    )
    
    print_response(response, "Delete Document")


def test_upload_invalid_file():
    """Test uploading invalid file type."""
    print("\n" + "❌ TESTING INVALID FILE UPLOAD ".ljust(60, "="))
    
    # Create a fake .exe file
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    invalid_path = test_dir / "malware.exe"
    
    with open(invalid_path, 'w') as f:
        f.write("fake executable")
    
    with open(invalid_path, 'rb') as f:
        files = {'file': ('malware.exe', f, 'application/octet-stream')}
        response = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=get_headers(),
            files=files
        )
    
    print_response(response, "Upload Invalid File Type (should fail)")
    
    # Cleanup
    os.remove(invalid_path)


def test_access_other_user_document():
    """Test that users can't access other users' documents."""
    print("\n" + "🔒 TESTING ACCESS CONTROL ".ljust(60, "="))
    
    # Try to access a fake document ID
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    response = requests.get(
        f"{BASE_URL}/documents/{fake_id}",
        headers=get_headers()
    )
    
    print_response(response, "Access Non-existent Document (should fail)")


def cleanup_test_files():
    """Remove test files."""
    import shutil
    test_dir = Path("test_files")
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("🧹 Test files cleaned up")


def main():
    """Run all document tests."""
    print("\n" + "="*60)
    print("🧪 DOCUMENT MANAGEMENT TESTS")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print("="*60)
    
    # Login
    if not login_or_signup():
        print("Cannot proceed without authentication")
        return
    
    # Run tests
    doc_id = test_upload_document()
    
    if doc_id:
        test_list_documents()
        test_get_document(doc_id)
        test_get_document_content(doc_id)
        test_get_document_chunks(doc_id)
        test_document_stats()
        
        # Test validation
        test_upload_invalid_file()
        test_access_other_user_document()
        
        # Cleanup - delete the test document
        # Uncomment if you want to delete after testing
        # test_delete_document(doc_id)
    
    # Cleanup test files
    cleanup_test_files()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED!")
    print("="*60)
    print("\n📝 Summary:")
    print("   - Check Swagger UI at http://localhost:8000/docs")
    print("   - Documents endpoint: /api/v1/documents")
    print("   - Try uploading a PDF or DOCX file via Swagger!")
    print()


if __name__ == "__main__":
    main()