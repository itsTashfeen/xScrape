from dotenv import load_dotenv
import os
from pymongo import MongoClient

def test_connection():
    # Load environment variables
    load_dotenv()
    
    # Get the connection string
    uri = os.getenv('MONGODB_URI')
    
    try:
        # Create a new client and connect to the server
        client = MongoClient(uri)
        
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        
        # Try to create a test collection and insert a document
        db = client.twitter_scraper
        test_collection = db.test
        
        result = test_collection.insert_one({"test": "connection"})
        print("✅ Successfully inserted test document!")
        
        # Clean up the test document
        test_collection.delete_one({"_id": result.inserted_id})
        print("✅ Successfully cleaned up test document!")
        
    except Exception as e:
        print("❌ Connection failed:", e)

if __name__ == "__main__":
    test_connection() 