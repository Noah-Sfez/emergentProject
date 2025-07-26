from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class UserRole(str, Enum):
    ADMIN = "admin"
    FAMILY_OFFICE_ADMIN = "family_office_admin"
    ADVISOR = "advisor"
    FAMILY_MEMBER = "family_member"

class DocumentType(str, Enum):
    CONTRACT = "contract"
    REPORT = "report"
    TAX_RETURN = "tax_return"
    INVESTMENT_DOCUMENT = "investment_document"
    MEETING_NOTES = "meeting_notes"
    OTHER = "other"

class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MessageType(str, Enum):
    TEXT = "text"
    DOCUMENT = "document"
    MEETING_REQUEST = "meeting_request"

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    first_name: str
    last_name: str
    role: UserRole
    family_office_id: str
    family_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    role: UserRole
    family_office_id: str
    family_id: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    family_office_id: str
    family_id: Optional[str] = None
    is_active: bool
    created_at: datetime

# Family Office Models
class FamilyOffice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FamilyOfficeCreate(BaseModel):
    name: str
    description: Optional[str] = None

# Family Models
class Family(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    family_office_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FamilyCreate(BaseModel):
    name: str
    family_office_id: str

# Document Models
class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    document_type: DocumentType
    family_id: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = []
    description: Optional[str] = None
    access_permissions: List[str] = []  # User IDs who can access
    is_active: bool = True

class DocumentCreate(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    document_type: DocumentType
    family_id: str
    tags: List[str] = []
    description: Optional[str] = None
    access_permissions: List[str] = []

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    document_type: DocumentType
    family_id: str
    uploaded_by: str
    uploaded_at: datetime
    tags: List[str]
    description: Optional[str]
    access_permissions: List[str]
    is_active: bool

# Meeting Models
class Meeting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    family_id: str
    advisor_id: str
    attendees: List[str] = []  # User IDs
    status: MeetingStatus = MeetingStatus.SCHEDULED
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    action_items: List[str] = []
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    family_id: str
    advisor_id: str
    attendees: List[str] = []
    meeting_link: Optional[str] = None

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[MeetingStatus] = None
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    action_items: Optional[List[str]] = None

# Message Models
class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    message_type: MessageType = MessageType.TEXT
    sender_id: str
    recipient_id: str
    family_id: str
    attachment_id: Optional[str] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MessageCreate(BaseModel):
    content: str
    message_type: MessageType = MessageType.TEXT
    recipient_id: str
    family_id: str
    attachment_id: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    content: str
    message_type: MessageType
    sender_id: str
    recipient_id: str
    family_id: str
    attachment_id: Optional[str]
    is_read: bool
    created_at: datetime

# Token Models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None