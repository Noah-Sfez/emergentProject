import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import User, UserRole, TokenData
from database import get_database

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# HTTP Bearer token
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify JWT token and return token data"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(user_id=user_id, email=email)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    token_data = verify_token(token)
    
    db = get_database()
    user_doc = await db.users.find_one({"id": token_data.user_id})
    
    if user_doc is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user_doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return User(**user_doc)

async def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password"""
    db = get_database()
    user_doc = await db.users.find_one({"email": email})
    
    if not user_doc:
        return None
    
    if not verify_password(password, user_doc["password"]):
        return None
    
    return User(**user_doc)

# Role-based access control decorators
def require_role(required_roles: list):
    """Decorator to require specific roles"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (injected by FastAPI)
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def check_family_access(user: User, family_id: str) -> bool:
    """Check if user has access to a specific family"""
    # Admin and family office admin have access to all families in their office
    if user.role in [UserRole.ADMIN, UserRole.FAMILY_OFFICE_ADMIN]:
        return True
    
    # Family members can only access their own family
    if user.role == UserRole.FAMILY_MEMBER:
        return user.family_id == family_id
    
    # Advisors can access families they're assigned to
    if user.role == UserRole.ADVISOR:
        db = get_database()
        
        # Check if advisor has any meetings or messages with this family
        meetings_count = await db.meetings.count_documents({
            "advisor_id": user.id,
            "family_id": family_id
        })
        
        messages_count = await db.messages.count_documents({
            "$or": [
                {"sender_id": user.id, "family_id": family_id},
                {"recipient_id": user.id, "family_id": family_id}
            ]
        })
        
        return meetings_count > 0 or messages_count > 0
    
    return False

async def check_document_access(user: User, document: Dict[str, Any]) -> bool:
    """Check if user has access to a specific document"""
    # Check family access first
    if not await check_family_access(user, document["family_id"]):
        return False
    
    # Check specific document permissions
    if document.get("access_permissions"):
        return user.id in document["access_permissions"]
    
    # If no specific permissions, use family access
    return True