import os
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

class Database:
    client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

db = Database()

async def connect_to_mongo():
    """Create database connection"""
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/multifamily_office")
    
    try:
        db.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        db.db = db.client.get_default_database()
        
        # Test connection
        await db.client.admin.command('ping')
        print(f"✅ Connected to MongoDB at {mongo_url}")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        print("✅ Database connection closed")

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Users collection indexes
        await db.db.users.create_index("email", unique=True)
        await db.db.users.create_index("family_office_id")
        await db.db.users.create_index("family_id")
        await db.db.users.create_index([("family_office_id", 1), ("role", 1)])
        
        # Documents collection indexes
        await db.db.documents.create_index("family_id")
        await db.db.documents.create_index("uploaded_by")
        await db.db.documents.create_index("document_type")
        await db.db.documents.create_index([("family_id", 1), ("document_type", 1)])
        
        # Meetings collection indexes
        await db.db.meetings.create_index("family_id")
        await db.db.meetings.create_index("advisor_id")
        await db.db.meetings.create_index("start_time")
        await db.db.meetings.create_index([("family_id", 1), ("start_time", 1)])
        
        # Messages collection indexes
        await db.db.messages.create_index("sender_id")
        await db.db.messages.create_index("recipient_id")
        await db.db.messages.create_index("family_id")
        await db.db.messages.create_index([("family_id", 1), ("created_at", -1)])
        
        # Family offices collection indexes
        await db.db.family_offices.create_index("name")
        
        # Families collection indexes
        await db.db.families.create_index("family_office_id")
        await db.db.families.create_index([("family_office_id", 1), ("name", 1)])
        
        print("✅ Database indexes created successfully")
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db.db