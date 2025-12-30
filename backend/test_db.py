# backend/test_db.py
"""
Database Test Script
====================
Tests that all models can be created and basic CRUD operations work.
Run with: python test_db.py
"""

import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import (
    User, 
    Document, 
    ChatSession, 
    ChatMessage,
    Template,
    GeneratedDocument,
    KnowledgeBase
)


async def test_database():
    """Test database operations."""
    
    print("=" * 50)
    print("🧪 Testing Database Operations")
    print("=" * 50)
    
    # Initialize database (creates tables)
    await init_db()
    
    async with AsyncSessionLocal() as session:
        try:
            # ============================================
            # TEST 1: Create a User
            # ============================================
            print("\n📝 Test 1: Creating a test user...")
            
            test_user = User(
                email="test@example.com",
                hashed_password="hashed_password_here",
                full_name="Test User",
                is_active=True,
                is_admin=False
            )
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            
            print(f"   ✅ Created user: {test_user}")
            print(f"   📧 Email: {test_user.email}")
            print(f"   🆔 ID: {test_user.id}")
            
            # ============================================
            # TEST 2: Query the User
            # ============================================
            print("\n🔍 Test 2: Querying user by email...")
            
            stmt = select(User).where(User.email == "test@example.com")
            result = await session.execute(stmt)
            found_user = result.scalar_one_or_none()
            
            if found_user:
                print(f"   ✅ Found user: {found_user.full_name}")
            else:
                print("   ❌ User not found!")
                
            # ============================================
            # TEST 3: Create a Chat Session with Messages
            # ============================================
            print("\n💬 Test 3: Creating a chat session...")
            
            chat_session = ChatSession(
                user_id=test_user.id,
                title="Test Legal Query",
                session_type="general"
            )
            session.add(chat_session)
            await session.commit()
            await session.refresh(chat_session)
            
            print(f"   ✅ Created session: {chat_session.id}")
            
            # Add messages
            user_message = ChatMessage(
                session_id=chat_session.id,
                role="user",
                content="What is a contract under Indian law?"
            )
            session.add(user_message)
            
            ai_message = ChatMessage(
                session_id=chat_session.id,
                role="assistant",
                content="Under the Indian Contract Act, 1872, a contract is defined as...",
                sources=[{"source": "Indian Contract Act, 1872", "section": "2(h)"}],
                tokens_used=150
            )
            session.add(ai_message)
            await session.commit()
            
            print(f"   ✅ Added 2 messages to session")
            
            # ============================================
            # TEST 4: Create a Template
            # ============================================
            print("\n📄 Test 4: Creating a document template...")
            
            nda_template = Template(
                name="Non-Disclosure Agreement",
                slug="nda",
                description="A standard NDA for protecting confidential information",
                category="agreements",
                template_body="""
NON-DISCLOSURE AGREEMENT

This Agreement is made on {{agreement_date}} between:

Party A: {{party_a_name}} (Disclosing Party)
Party B: {{party_b_name}} (Receiving Party)

WHEREAS, the Disclosing Party possesses certain confidential information...
                """,
                form_schema={
                    "fields": [
                        {"name": "agreement_date", "label": "Agreement Date", "type": "date", "required": True},
                        {"name": "party_a_name", "label": "Party A Name", "type": "text", "required": True},
                        {"name": "party_b_name", "label": "Party B Name", "type": "text", "required": True},
                    ]
                },
                applicable_laws=["Indian Contract Act, 1872", "Information Technology Act, 2000"]
            )
            session.add(nda_template)
            await session.commit()
            await session.refresh(nda_template)
            
            print(f"   ✅ Created template: {nda_template.name}")
            
            # ============================================
            # TEST 5: Create a Knowledge Base Entry
            # ============================================
            print("\n📚 Test 5: Creating knowledge base entry...")
            
            kb_entry = KnowledgeBase(
                title="Indian Contract Act, 1872",
                description="An Act to define and amend certain parts of the law relating to contracts.",
                source="Government of India",
                category="acts",
                tags=["contract", "civil", "commercial"],
                status="pending"
            )
            session.add(kb_entry)
            await session.commit()
            await session.refresh(kb_entry)
            
            print(f"   ✅ Created knowledge base: {kb_entry.title}")
            
            # ============================================
            # TEST 6: Count Records
            # ============================================
            print("\n📊 Test 6: Counting records...")
            
            user_count = await session.execute(select(User))
            print(f"   👤 Users: {len(user_count.scalars().all())}")
            
            session_count = await session.execute(select(ChatSession))
            print(f"   💬 Chat Sessions: {len(session_count.scalars().all())}")
            
            template_count = await session.execute(select(Template))
            print(f"   📄 Templates: {len(template_count.scalars().all())}")
            
            kb_count = await session.execute(select(KnowledgeBase))
            print(f"   📚 Knowledge Base: {len(kb_count.scalars().all())}")
            
            # ============================================
            # CLEANUP: Delete test data
            # ============================================
            print("\n🧹 Cleaning up test data...")
            
            await session.delete(kb_entry)
            await session.delete(nda_template)
            await session.delete(chat_session)  # Cascades to messages
            await session.delete(test_user)
            await session.commit()
            
            print("   ✅ Test data cleaned up")
            
            print("\n" + "=" * 50)
            print("✅ All database tests passed!")
            print("=" * 50)
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(test_database())