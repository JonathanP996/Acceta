"""Test MongoDB connection"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

uri = os.getenv("MONGODB_URI")
print(f"MONGODB_URI: {uri[:50]}..." if uri else "MONGODB_URI: None")

if not uri:
    print("ERROR: MONGODB_URI not found in .env file")
    exit(1)

async def test_connection():
    try:
        print("Attempting to connect...")
        client = AsyncIOMotorClient(uri, tlsAllowInvalidCertificates=True)
        await client.admin.command('ping')
        print("Connection successful!")
        
        db_name = os.getenv("MONGODB_DB_NAME", "accenta")
        db = client[db_name]
        print(f"Database '{db_name}' accessible")
        
        client.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    exit(0 if result else 1)

