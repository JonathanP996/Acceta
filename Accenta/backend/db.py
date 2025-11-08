"""
MongoDB Database Connection and Operations
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    """MongoDB database connection manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    db = None
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB Atlas"""
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        try:
            # Configure SSL for MongoDB Atlas
            import ssl
            cls.client = AsyncIOMotorClient(
                mongodb_uri,
                tlsAllowInvalidCertificates=True  # For development - use proper certs in production
            )
            # Test connection
            await cls.client.admin.command('ping')
            db_name = os.getenv("MONGODB_DB_NAME", "accenta")
            cls.db = cls.client[db_name]
            
            # Create indexes
            await cls._create_indexes()
            
            logger.info(f"Connected to MongoDB: {db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB"""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    async def _create_indexes(cls):
        """Create database indexes for performance"""
        if cls.db is None:
            return
        
        # Users collection
        await cls.db.users.create_index("user_id", unique=True)
        await cls.db.users.create_index("email", unique=True)
        
        # Sessions collection
        await cls.db.sessions.create_index([("user_id", 1), ("timestamp", -1)])
        await cls.db.sessions.create_index("session_id", unique=True)
        
        # Profiles collection
        await cls.db.profiles.create_index([("user_id", 1), ("language", 1), ("accent", 1)], unique=True)
        
        # Feedback collection
        await cls.db.feedback.create_index([("user_id", 1), ("generated_at", -1)])
        
        # Voice baselines collection (for onboarding)
        await cls.db.voice_baselines.create_index([("user_id", 1), ("language", 1), ("target_accent", 1)], unique=True)
        
        logger.info("Database indexes created")
    
    @classmethod
    def get_collection(cls, collection_name: str):
        """Get a collection by name"""
        if cls.db is None:
            raise RuntimeError("Database not connected. Call Database.connect() first.")
        return cls.db[collection_name]

