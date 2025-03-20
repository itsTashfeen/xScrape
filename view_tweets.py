from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime

def view_stored_tweets():
    # Load environment variables
    load_dotenv()
    
    # Connect to MongoDB Atlas
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['twitter_scraper']
    tweets_collection = db['tweets']
    
    # Get all tweets
    tweets = list(tweets_collection.find({}, {'_id': 0}))
    
    print(f"\nFound {len(tweets)} tweets in database:")
    print("-" * 50)
    
    # Group tweets by username
    tweets_by_user = {}
    for tweet in tweets:
        username = tweet['author']['username']
        if username not in tweets_by_user:
            tweets_by_user[username] = []
        tweets_by_user[username].append(tweet)
    
    # Display tweets grouped by username
    for username, user_tweets in tweets_by_user.items():
        print(f"\nTweets from @{username}:")
        print("=" * 50)
        
        for i, tweet in enumerate(user_tweets, 1):
            print(f"\nTweet {i}:")
            print("-" * 50)
            print("Content:")
            print(tweet.get('content', 'No content'))  # Show full content without truncation
            print("\nMetrics:")
            for metric, value in tweet.get('metrics', {}).items():
                print(f"  {metric.capitalize()}: {value}")
            
            if tweet.get('is_thread'):
                print("\nThis is a thread")
                thread_tweets = tweet.get('thread_tweets', [])
                if thread_tweets:
                    print(f"  Contains {len(thread_tweets)} additional tweets")
            
            comments = tweet.get('comments', [])
            if comments:
                print(f"\nHas {len(comments)} comments")
            
            media = tweet.get('media', [])
            if media:
                print(f"\nContains {len(media)} media items")
                for item in media:
                    print(f"  Type: {item.get('type')}")
                    print(f"  URL: {item.get('url')}")
            
            print(f"\nScraped at: {tweet.get('scraped_at', 'Unknown')}")
            print("-" * 50)

if __name__ == "__main__":
    view_stored_tweets() 