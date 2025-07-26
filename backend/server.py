import os
import uvicorn
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import aiofiles
import base64

# Import our modules
from database import connect_to_mongo, close_mongo_connection, get_database
from auth import (
    authenticate_user, create_access_token, get_current_user, 
    get_password_hash, check_family_access, check_document_access
)
from models import (
    User, UserCreate, UserLogin, UserResponse, UserRole,
    FamilyOffice, FamilyOfficeCreate, Family, FamilyCreate,
    Document, DocumentCreate, DocumentResponse, DocumentType,
    Meeting, MeetingCreate, MeetingUpdate, MeetingStatus,
    Message, MessageCreate, MessageResponse, MessageType,
    Token
)

# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    
    # Create default data if needed
    await create_default_data()
    
    yield
    
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="Multi-Family Office Platform API",
    description="Secure API for multi-family office client portal",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Multi-Family Office Platform API", "version": "1.0.0"}

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Authentication endpoints
@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    db = get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Verify family office exists
    family_office = await db.family_offices.find_one({"id": user_data.family_office_id})
    if not family_office:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Family office not found"
        )
    
    # Verify family exists if family_id is provided
    if user_data.family_id:
        family = await db.families.find_one({"id": user_data.family_id})
        if not family:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Family not found"
            )
    
    # Create user
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        family_office_id=user_data.family_office_id,
        family_id=user_data.family_id
    )
    
    # Hash password and add to user document
    user_dict = user.dict()
    user_dict["password"] = get_password_hash(user_data.password)
    
    await db.users.insert_one(user_dict)
    
    return UserResponse(**user.dict())

@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login user and return access token"""
    user = await authenticate_user(user_credentials.email, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email}, 
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400,  # 24 hours in seconds
        user=UserResponse(**user.dict())
    )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(**current_user.dict())

# Family Office endpoints
@app.post("/api/family-offices", response_model=FamilyOffice)
async def create_family_office(
    family_office_data: FamilyOfficeCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new family office (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create family offices"
        )
    
    db = get_database()
    
    family_office = FamilyOffice(
        name=family_office_data.name,
        description=family_office_data.description
    )
    
    await db.family_offices.insert_one(family_office.dict())
    
    return family_office

@app.get("/api/family-offices", response_model=List[FamilyOffice])
async def get_family_offices(current_user: User = Depends(get_current_user)):
    """Get family offices accessible to current user"""
    db = get_database()
    
    if current_user.role == UserRole.ADMIN:
        # Admin can see all family offices
        family_offices = await db.family_offices.find().to_list(length=None)
    else:
        # Others can only see their own family office
        family_offices = await db.family_offices.find(
            {"id": current_user.family_office_id}
        ).to_list(length=None)
    
    return [FamilyOffice(**fo) for fo in family_offices]

# Family endpoints
@app.post("/api/families", response_model=Family)
async def create_family(
    family_data: FamilyCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new family"""
    if current_user.role not in [UserRole.ADMIN, UserRole.FAMILY_OFFICE_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create families"
        )
    
    db = get_database()
    
    family = Family(
        name=family_data.name,
        family_office_id=family_data.family_office_id
    )
    
    await db.families.insert_one(family.dict())
    
    return family

@app.get("/api/families", response_model=List[Family])
async def get_families(current_user: User = Depends(get_current_user)):
    """Get families accessible to current user"""
    db = get_database()
    
    if current_user.role == UserRole.ADMIN:
        # Admin can see all families
        families = await db.families.find().to_list(length=None)
    elif current_user.role == UserRole.FAMILY_OFFICE_ADMIN:
        # Family office admin can see families in their office
        families = await db.families.find(
            {"family_office_id": current_user.family_office_id}
        ).to_list(length=None)
    else:
        # Others can only see their own family
        families = await db.families.find(
            {"id": current_user.family_id}
        ).to_list(length=None)
    
    return [Family(**f) for f in families]

# Document endpoints
@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("other"),
    family_id: str = Form(...),
    description: str = Form(None),
    tags: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    """Upload a document"""
    if not family_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Family ID is required"
        )
    
    # Check family access
    if not await check_family_access(current_user, family_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this family"
        )
    
    # Validate file
    if file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 50MB"
        )
    
    # Read file content
    content = await file.read()
    
    # Convert to base64 for storage
    file_content_base64 = base64.b64encode(content).decode('utf-8')
    
    db = get_database()
    
    # Create document record
    document = Document(
        filename=file.filename,
        original_filename=file.filename,
        file_size=len(content),
        content_type=file.content_type,
        document_type=DocumentType(document_type),
        family_id=family_id,
        uploaded_by=current_user.id,
        tags=tags.split(",") if tags else [],
        description=description
    )
    
    # Store document with base64 content
    document_dict = document.dict()
    document_dict["file_content"] = file_content_base64
    
    await db.documents.insert_one(document_dict)
    
    return DocumentResponse(**document.dict())

@app.get("/api/documents", response_model=List[DocumentResponse])
async def get_documents(
    family_id: Optional[str] = None,
    document_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get documents accessible to current user"""
    db = get_database()
    
    # Build query
    query = {}
    
    if family_id:
        # Check family access
        if not await check_family_access(current_user, family_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this family"
            )
        query["family_id"] = family_id
    
    if document_type:
        query["document_type"] = document_type
    
    # Get documents
    documents = await db.documents.find(query).to_list(length=None)
    
    # Filter by access permissions
    accessible_docs = []
    for doc in documents:
        if await check_document_access(current_user, doc):
            accessible_docs.append(DocumentResponse(**doc))
    
    return accessible_docs

@app.get("/api/documents/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download a document"""
    db = get_database()
    
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check access
    if not await check_document_access(current_user, document):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this document"
        )
    
    # Return base64 content
    return {
        "filename": document["original_filename"],
        "content_type": document["content_type"],
        "file_content": document["file_content"]
    }

# Meeting endpoints
@app.post("/api/meetings", response_model=Meeting)
async def create_meeting(
    meeting_data: MeetingCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new meeting"""
    # Check family access
    if not await check_family_access(current_user, meeting_data.family_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this family"
        )
    
    db = get_database()
    
    meeting = Meeting(
        title=meeting_data.title,
        description=meeting_data.description,
        start_time=meeting_data.start_time,
        end_time=meeting_data.end_time,
        family_id=meeting_data.family_id,
        advisor_id=meeting_data.advisor_id,
        attendees=meeting_data.attendees,
        meeting_link=meeting_data.meeting_link,
        created_by=current_user.id
    )
    
    await db.meetings.insert_one(meeting.dict())
    
    return meeting

@app.get("/api/meetings", response_model=List[Meeting])
async def get_meetings(
    family_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get meetings accessible to current user"""
    db = get_database()
    
    # Build query
    query = {}
    
    if family_id:
        # Check family access
        if not await check_family_access(current_user, family_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this family"
            )
        query["family_id"] = family_id
    
    if status:
        query["status"] = status
    
    # Add user-specific filters
    if current_user.role == UserRole.ADVISOR:
        query["advisor_id"] = current_user.id
    elif current_user.role == UserRole.FAMILY_MEMBER:
        query["family_id"] = current_user.family_id
    
    meetings = await db.meetings.find(query).to_list(length=None)
    
    return [Meeting(**m) for m in meetings]

# Message endpoints
@app.post("/api/messages", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Send a message"""
    # Check family access
    if not await check_family_access(current_user, message_data.family_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this family"
        )
    
    db = get_database()
    
    message = Message(
        content=message_data.content,
        message_type=message_data.message_type,
        sender_id=current_user.id,
        recipient_id=message_data.recipient_id,
        family_id=message_data.family_id,
        attachment_id=message_data.attachment_id
    )
    
    await db.messages.insert_one(message.dict())
    
    return MessageResponse(**message.dict())

@app.get("/api/messages", response_model=List[MessageResponse])
async def get_messages(
    family_id: Optional[str] = None,
    recipient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get messages accessible to current user"""
    db = get_database()
    
    # Build query
    query = {
        "$or": [
            {"sender_id": current_user.id},
            {"recipient_id": current_user.id}
        ]
    }
    
    if family_id:
        # Check family access
        if not await check_family_access(current_user, family_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this family"
            )
        query["family_id"] = family_id
    
    if recipient_id:
        query["$or"] = [
            {"sender_id": current_user.id, "recipient_id": recipient_id},
            {"sender_id": recipient_id, "recipient_id": current_user.id}
        ]
    
    messages = await db.messages.find(query).sort("created_at", -1).to_list(length=None)
    
    return [MessageResponse(**m) for m in messages]

# Utility functions
async def create_default_data():
    """Create default data for development"""
    db = get_database()
    
    # Create default family office
    existing_fo = await db.family_offices.find_one({"name": "Demo Family Office"})
    if not existing_fo:
        demo_fo = FamilyOffice(
            name="Demo Family Office",
            description="Demo family office for testing"
        )
        await db.family_offices.insert_one(demo_fo.dict())
        fo_id = demo_fo.id
    else:
        fo_id = existing_fo["id"]
    
    # Create default family
    existing_family = await db.families.find_one({"name": "Demo Family"})
    if not existing_family:
        demo_family = Family(
            name="Demo Family",
            family_office_id=fo_id
        )
        await db.families.insert_one(demo_family.dict())
        family_id = demo_family.id
    else:
        family_id = existing_family["id"]
    
    # Create default admin user
    existing_admin = await db.users.find_one({"email": "admin@demo.com"})
    if not existing_admin:
        admin_user = User(
            email="admin@demo.com",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            family_office_id=fo_id
        )
        admin_dict = admin_user.dict()
        admin_dict["password"] = get_password_hash("admin123")
        await db.users.insert_one(admin_dict)
    
    # Create default family member
    existing_member = await db.users.find_one({"email": "member@demo.com"})
    if not existing_member:
        member_user = User(
            email="member@demo.com",
            first_name="Family",
            last_name="Member",
            role=UserRole.FAMILY_MEMBER,
            family_office_id=fo_id,
            family_id=family_id
        )
        member_dict = member_user.dict()
        member_dict["password"] = get_password_hash("member123")
        await db.users.insert_one(member_dict)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)