from dotenv import load_dotenv
from pymongo import MongoClient
import os

def test_mongodb_connection():
    try:
        # Load the .env file
        load_dotenv()
        
        # Get connection string from environment variable
        uri = os.getenv('MONGODB_URI')
        
        # Connect to MongoDB
        client = MongoClient(uri)
        
        # Test the connection
        client.admin.command('ping')
        
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # Create a test document
        db = client['twitter_scraper']
        test_collection = db['test']
        
        result = test_collection.insert_one({"test": "Hello MongoDB!"})
        test_collection.delete_one({"_id": result.inserted_id})
        
        print("✅ Successfully tested database operations!")
        return True
        
    except Exception as e:
        print("❌ Connection failed!")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_mongodb_connection() 