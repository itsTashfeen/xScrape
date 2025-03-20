from pymongo import MongoClient
from dotenv import load_dotenv
import os

def view_stored_tweets():
    # Load environment variables
    load_dotenv()
    
    # Connect to MongoDB Atlas
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['twitter_scraper']
    tweets = db['tweets']
    
    # Get all tweets
    stored_tweets = list(tweets.find({}, {'_id': 0}))  # Exclude MongoDB _id field
    
    print(f"\nFound {len(stored_tweets)} tweets in database:")
    print("-" * 50)
    
    for i, tweet in enumerate(stored_tweets, 1):
        print(f"\nTweet {i}:")
        print(f"Author: @{tweet['author']['username']}")
        print(f"Content: {tweet['content'][:100]}...")
        print(f"Metrics: {tweet['metrics']}")
        print(f"Scraped at: {tweet['scraped_at']}")
        print("-" * 50)

if __name__ == "__main__":
    view_stored_tweets() 