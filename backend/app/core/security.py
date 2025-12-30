# backend/app/core/security.py
"""
Security Utilities
==================
Handles password hashing and JWT token operations.

Password Hashing:
- Uses bcrypt (industry standard)
- Automatically handles salting
- Secure against rainbow table attacks

JWT Tokens:
- Stateless authentication
- Contains user ID and expiration
- Signed with secret key (HS256 algorithm)
"""

from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings


# ============================================
# PASSWORD HASHING
# ============================================
# CryptContext handles password hashing with bcrypt
# - bcrypt is slow by design (resistant to brute force)
# - Automatically generates and stores salt
# - deprecated="auto" means old schemes are auto-upgraded

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    """
    Hash a plain text password.
    
    Args:
        password: Plain text password from user
        
    Returns:
        Hashed password string (includes salt)
        
    Example:
        >>> hashed = hash_password("mysecretpassword")
        >>> # Returns something like: $2b$12$LQv3c1yqBo...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Password provided by user during login
        hashed_password: Stored hash from database
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("mysecretpassword")
        >>> verify_password("mysecretpassword", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================
# JWT TOKEN HANDLING
# ============================================

def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Optional custom expiration time
        additional_claims: Optional extra data to include in token
        
    Returns:
        Encoded JWT token string
        
    Token Structure:
        {
            "sub": "user_id_here",        # Subject (user ID)
            "exp": 1234567890,            # Expiration timestamp
            "iat": 1234567890,            # Issued at timestamp
            "type": "access",             # Token type
            ...additional_claims
        }
    """
    # Calculate expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Build token payload
    to_encode = {
        "sub": str(subject),          # Subject (user ID)
        "exp": expire,                 # Expiration time
        "iat": datetime.utcnow(),     # Issued at
        "type": "access",              # Token type
    }
    
    # Add any additional claims
    if additional_claims:
        to_encode.update(additional_claims)
    
    # Encode and sign the token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: The JWT token string
        
    Returns:
        Decoded token payload if valid, None if invalid
        
    Raises:
        Returns None on any error (expired, invalid signature, etc.)
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def get_token_subject(token: str) -> Optional[str]:
    """
    Extract the subject (user ID) from a token.
    
    Args:
        token: The JWT token string
        
    Returns:
        User ID string if valid, None if invalid
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("sub")
    return None


# ============================================
# TOKEN VALIDATION HELPERS
# ============================================

def is_token_expired(token: str) -> bool:
    """
    Check if a token has expired.
    
    Args:
        token: The JWT token string
        
    Returns:
        True if expired or invalid, False if still valid
    """
    payload = decode_access_token(token)
    if not payload:
        return True
    
    exp = payload.get("exp")
    if not exp:
        return True
    
    # Check if expiration time has passed
    return datetime.utcnow() > datetime.fromtimestamp(exp)


def create_password_reset_token(email: str) -> str:
    """
    Create a password reset token (shorter expiration).
    
    Args:
        email: User's email address
        
    Returns:
        JWT token for password reset (valid for 1 hour)
    """
    return create_access_token(
        subject=email,
        expires_delta=timedelta(hours=1),
        additional_claims={"type": "password_reset"}
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token.
    
    Args:
        token: The password reset token
        
    Returns:
        Email address if valid, None if invalid
    """
    payload = decode_access_token(token)
    if payload and payload.get("type") == "password_reset":
        return payload.get("sub")
    return None