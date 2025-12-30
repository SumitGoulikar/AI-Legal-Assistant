# backend/app/main.py
import os
import time
from datetime import datetime
from contextlib import asynccontextmanager  # <--- THIS WAS MISSING

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.core.exceptions import LegalAssistantException
from app.database import init_db, close_db, AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.services.template_service import TemplateService

# ============================================
# LIFESPAN EVENTS (Startup/Shutdown)
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # -------- STARTUP --------
    print("=" * 50)
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📍 Environment: {'Development' if settings.DEBUG else 'Production'}")
    print(f"🌍 Jurisdiction: {settings.DEFAULT_JURISDICTION}")
    print("=" * 50)
    
    # Create data directories if they don't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.GENERATED_DIR, exist_ok=True)
    os.makedirs(settings.KNOWLEDGE_BASE_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    
    # Initialize database
    print("📦 Initializing database...")
    await init_db()

    # --- GUEST USER CREATION ---
    print("👤 Ensuring Guest User exists...")
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        # Check if guest exists by fixed ID
        result = await session.execute(select(User).where(User.id == "00000000-0000-0000-0000-000000000000"))
        guest = result.scalar_one_or_none()
        
        if not guest:
            # Check by email if ID check failed (to prevent duplicates)
            result_email = await session.execute(select(User).where(User.email == "guest@example.com"))
            guest_email = result_email.scalar_one_or_none()
            
            if guest_email:
                print("ℹ️ Guest user exists but ID might be different. Using existing.")
            else:
                guest_user = User(
                    id="00000000-0000-0000-0000-000000000000", # Fixed ID
                    email="guest@example.com",
                    hashed_password=hash_password("guest"),
                    full_name="Guest User",
                    is_active=True,
                    is_admin=True
                )
                session.add(guest_user)
                await session.commit()
                print("✅ Guest User created.")
        else:
            print("✅ Guest User found.")
    # ---------------------------
    
    # Load templates
    print("📋 Loading document templates...")
    async with AsyncSessionLocal() as session:
        template_service = TemplateService(session)
        count = await template_service.load_templates_from_directory("./templates")
        print(f"   ✅ Loaded {count} template(s)")
    
    # Initialize AI services (Lazy load)
    print("🧠 AI services ready (lazy load)")
    
    print("✅ All systems initialized successfully!")
    print(f"📖 API Docs available at: http://localhost:{settings.PORT}/docs")
    print("=" * 50)
    
    yield  # Application runs here
    
    # -------- SHUTDOWN --------
    print("\n" + "=" * 50)
    print("🛑 Shutting down gracefully...")
    
    # Close database connections
    await close_db()
    
    print("👋 Goodbye!")
    print("=" * 50)


# ============================================
# CREATE FASTAPI APPLICATION
# ============================================
app = FastAPI(
    title=settings.APP_NAME,
    description="AI Legal Assistant API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    lifespan=lifespan,
)

# ============================================
# CORS MIDDLEWARE
# ============================================
app.add_middleware(
    CORSMiddleware,
    # ALLOW ALL ORIGINS FOR DEV
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# REGISTER API ROUTERS
# ============================================
# In router registration section
from app.api import auth, documents, chat, generate, admin

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(generate.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)

# ============================================
# STATUS ENDPOINT
# ============================================
@app.get("/api/v1/status", tags=["Status"])
async def detailed_status():
    return {"status": "operational", "mode": "guest_access"}

# ============================================
# RUNNER
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )