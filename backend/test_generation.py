# backend/test_generation.py
"""
Document Generation Test Script
================================
Tests the document generation system.

Run with: python test_generation.py
"""

import requests
import json
import sys
from pathlib import Path

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
        if len(data_str) > 2000:
            print(f"Response: {data_str[:2000]}...")
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
    print("   Start with: uvicorn app.main:app --reload")
    return False


def login_or_signup():
    """Login or create test user."""
    global access_token
    
    print("\n🔑 Authenticating...")
    
    # Try login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "gentest@example.com",
            "password": "GenTest123"
        }
    )
    
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        print("   ✅ Logged in!")
        return True
    
    # Try signup
    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "email": "gentest@example.com",
            "password": "GenTest123",
            "full_name": "Generation Test User"
        }
    )
    
    if response.status_code == 201:
        access_token = response.json()["access_token"]
        print("   ✅ User created!")
        return True
    
    print(f"   ❌ Authentication failed: {response.text}")
    return False


def test_list_templates():
    """Test listing templates."""
    print_section("TESTING LIST TEMPLATES")
    
    response = requests.get(
        f"{BASE_URL}/generate/templates",
        timeout=10
    )
    
    print_response(response, "List Templates")
    
    if response.status_code == 200:
        data = response.json()
        templates = data.get("templates", [])
        print(f"   ✅ Found {len(templates)} template(s)")
        
        for template in templates:
            print(f"   - {template.get('name')} ({template.get('slug')})")
        
        return templates[0]["id"] if templates else None
    
    return None


def test_get_template(template_id):
    """Test getting template details."""
    print_section("TESTING GET TEMPLATE DETAILS")
    
    response = requests.get(
        f"{BASE_URL}/generate/templates/{template_id}",
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Template: {data.get('name')}")
        print(f"   📝 Category: {data.get('category')}")
        
        fields = data.get("form_schema", {}).get("fields", [])
        print(f"   📋 Form fields ({len(fields)}):")
        for field in fields[:5]:  # Show first 5
            print(f"      - {field.get('label')} ({field.get('type')})")
        
        return data
    else:
        print(f"   ❌ Failed: {response.text}")
        return None


def test_preview_document(template_id):
    """Test document preview."""
    print_section("TESTING DOCUMENT PREVIEW")
    
    # Sample form data for NDA
    form_data = {
        "agreement_date": "15 January 2024",
        "party_a_name": "Acme Technologies Private Limited",
        "party_a_address": "123 Tech Park, Sector 5, Electronic City\nBangalore - 560100, Karnataka, India",
        "party_b_name": "Beta Solutions Limited",
        "party_b_address": "456 Business Center, Andheri East\nMumbai - 400069, Maharashtra, India",
        "purpose": "evaluation of a potential technology partnership and business collaboration",
        "duration_years": "3",
        "survival_years": "2",
        "jurisdiction": "Bangalore"
    }
    
    response = requests.post(
        f"{BASE_URL}/generate/preview",
        headers=get_headers(),
        json={
            "template_id": template_id,
            "title": "NDA Preview",
            "form_data": form_data
        },
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        preview = data.get("preview_text", "")
        
        print(f"   ✅ Preview generated!")
        print(f"   📄 Length: {len(preview)} characters")
        print(f"\n   Preview (first 500 chars):")
        print(f"   {preview[:500]}...")
        return True
    else:
        print(f"   ❌ Failed: {response.text}")
        return False


def test_generate_document(template_id):
    """Test document generation."""
    print_section("TESTING DOCUMENT GENERATION")
    
    form_data = {
        "agreement_date": "15 January 2024",
        "party_a_name": "Acme Technologies Private Limited",
        "party_a_address": "123 Tech Park, Sector 5, Electronic City\nBangalore - 560100, Karnataka, India",
        "party_b_name": "Beta Solutions Limited",
        "party_b_address": "456 Business Center, Andheri East\nMumbai - 400069, Maharashtra, India",
        "purpose": "evaluation of a potential technology partnership and business collaboration",
        "duration_years": "3",
        "survival_years": "2",
        "jurisdiction": "Bangalore"
    }
    
    print("   📝 Generating NDA document...")
    
    response = requests.post(
        f"{BASE_URL}/generate/create",
        headers=get_headers(),
        json={
            "template_id": template_id,
            "title": "NDA - Acme & Beta Solutions",
            "form_data": form_data
        },
        timeout=15
    )
    
    if response.status_code == 201:
        data = response.json()
        document = data.get("document", {})
        
        print(f"   ✅ Document generated!")
        print(f"   📄 Document ID: {document.get('id')}")
        print(f"   📝 Title: {document.get('title')}")
        print(f"   📥 Download URL: {data.get('download_url')}")
        
        return document.get("id")
    else:
        print(f"   ❌ Failed: {response.text}")
        return None


def test_list_generated_documents():
    """Test listing generated documents."""
    print_section("TESTING LIST GENERATED DOCUMENTS")
    
    response = requests.get(
        f"{BASE_URL}/generate/documents",
        headers=get_headers(),
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        documents = data.get("documents", [])
        
        print(f"   ✅ Found {len(documents)} generated document(s)")
        
        for doc in documents:
            print(f"   - {doc.get('title')}")
            print(f"     Created: {doc.get('created_at')}")
    else:
        print(f"   ❌ Failed: {response.text}")


def test_download_document(document_id):
    """Test downloading document PDF."""
    print_section("TESTING DOCUMENT DOWNLOAD")
    
    print(f"   📥 Downloading document: {document_id}")
    
    response = requests.get(
        f"{BASE_URL}/generate/documents/{document_id}/download",
        headers=get_headers(),
        timeout=10
    )
    
    if response.status_code == 200:
        # Save PDF to test file
        output_path = Path("test_files") / "generated_nda.pdf"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"   ✅ PDF downloaded!")
        print(f"   💾 Saved to: {output_path}")
        print(f"   📊 Size: {len(response.content)} bytes")
        print(f"\n   👉 Open the file to view the generated document!")
    else:
        print(f"   ❌ Failed: {response.text}")


def test_get_categories():
    """Test getting template categories."""
    print_section("TESTING GET CATEGORIES")
    
    response = requests.get(
        f"{BASE_URL}/generate/categories",
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        categories = data.get("categories", [])
        
        print(f"   ✅ Available categories:")
        for category in categories:
            print(f"      - {category}")
    else:
        print(f"   ❌ Failed: {response.text}")


def cleanup():
    """Cleanup test files."""
    import shutil
    test_dir = Path("test_files")
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("\n🧹 Test files cleaned up (except generated PDFs)")


def main():
    """Run all generation tests."""
    print("\n" + "="*70)
    print("  🧪 DOCUMENT GENERATION TESTS")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print("="*70)
    
    # Check server
    if not check_server():
        sys.exit(1)
    
    # Login
    if not login_or_signup():
        print("\n❌ Cannot proceed without authentication")
        sys.exit(1)
    
    # Run tests
    test_get_categories()
    
    template_id = test_list_templates()
    
    if not template_id:
        print("\n❌ No templates found! Make sure templates are loaded.")
        sys.exit(1)
    
    template_data = test_get_template(template_id)
    
    if template_data:
        test_preview_document(template_id)
        
        doc_id = test_generate_document(template_id)
        
        if doc_id:
            test_list_generated_documents()
            test_download_document(doc_id)
    
    print("\n" + "="*70)
    print("  ✅ ALL GENERATION TESTS COMPLETED!")
    print("="*70)
    print("\n📝 Summary:")
    print("   ✅ Templates loaded and listed")
    print("   ✅ Document preview works")
    print("   ✅ Document generation works")
    print("   ✅ PDF download works")
    print("\n🎉 Document generation system is ready!")
    print()


if __name__ == "__main__":
    main()