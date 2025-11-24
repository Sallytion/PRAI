"""
MongoDB Database Configuration
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import get_settings

settings = get_settings()

# Global MongoDB client
mongodb_client: AsyncIOMotorClient = None


async def connect_to_mongo():
    """Connect to MongoDB and initialize Beanie ODM"""
    global mongodb_client
    
    mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # Import all document models
    from app.models.user import User
    from app.models.repository import Repository
    from app.models.pull_request import PullRequest
    from app.models.review import Review
    
    # Initialize beanie with the database and document models
    await init_beanie(
        database=mongodb_client[settings.MONGODB_DB_NAME],
        document_models=[User, Repository, PullRequest, Review]
    )
    
    print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("✅ Closed MongoDB connection")


def get_database():
    """Get MongoDB database instance"""
    return mongodb_client[settings.MONGODB_DB_NAME]
