# backend/test_pdf.py
"""Quick PDF generation test"""

from app.utils.pdf_generator import generate_legal_pdf
from pathlib import Path

# Create test directory
output_dir = Path("data/generated/test")
output_dir.mkdir(parents=True, exist_ok=True)

# Test content
content = """
NON-DISCLOSURE AGREEMENT

This is a test document to verify PDF generation works.

1. INTRODUCTION
This agreement is entered into for testing purposes.

2. TERMS
The terms of this agreement include various test clauses.

3. CONCLUSION
This concludes the test document.
"""

# Generate PDF
output_path = output_dir / "test_nda.pdf"

try:
    result = generate_legal_pdf(
        content=content,
        output_path=str(output_path),
        title="Test NDA",
        metadata={"author": "Test", "date": "2024-01-15"}
    )
    
    print(f"✅ PDF generated successfully!")
    print(f"📄 Path: {result}")
    print(f"📊 Size: {Path(result).stat().st_size} bytes")
    print(f"\n👉 Open: {output_path}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()