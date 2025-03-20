from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_connection():
    try:
        # Get the connection string from environment variable
        uri = os.getenv('MONGODB_URI')
        
        # Create a new client and connect to the server
        client = MongoClient(uri)
        
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        
        print("✅ Successfully connected to MongoDB!")
        return True
    except Exception as e:
        print("❌ Connection failed:", e)
        return False

if __name__ == "__main__":
    test_connection() 