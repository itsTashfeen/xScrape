from pymongo import MongoClient, ASCENDING
from pymongo.errors import ServerSelectionTimeoutError, PyMongoError
import sys
import logging
from datetime import datetime
from typing import List, Dict
import os

class DatabaseManager:
    def __init__(self):
        try:
            # Load environment variables
            self.client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=5000)
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client['twitter_scraper']
            
            # Initialize collections
            self.tweets = self.db['tweets']
            self.profiles = self.db['profiles']
            self.threads = self.db['threads']
            self.comments = self.db['comments']
            self.media = self.db['media']
            self.quote_tweets = self.db['quote_tweets']
            
            # Create indexes for better query performance
            self.setup_indexes()
            
            logging.info("Successfully connected to MongoDB")
            
        except PyMongoError as e:
            logging.error(f"MongoDB Error: {str(e)}")
            print("\nERROR: Could not connect to MongoDB. Please check your connection string and network connection.")
            sys.exit(1)
    
    def setup_indexes(self):
        # Create indexes if they don't exist
        self.tweets.create_index([('tweet_id', ASCENDING)], unique=True)
        except ConnectionError:
            logging.error("Could not connect to MongoDB. Is it running?")
            print("\nERROR: Could not connect to MongoDB. Please make sure MongoDB is running:")
            print("Windows: Check if MongoDB service is running in Services")
            print("Mac: Run 'brew services start mongodb-community'")
            print("Linux: Run 'sudo systemctl start mongod'")
            sys.exit(1)
            
        except ServerSelectionTimeoutError:
            logging.error("MongoDB server selection timeout. Is MongoDB running?")
            print("\nERROR: MongoDB server selection timeout. Please make sure MongoDB is running.")
            sys.exit(1)
    
    def setup_indexes(self):
        # Indexes for tweets collection
        self.tweets.create_index([('tweet_id', ASCENDING)], unique=True)
        self.tweets.create_index([('author.username', ASCENDING)])
        self.tweets.create_index([('timestamp', ASCENDING)])
        self.tweets.create_index([('thread_id', ASCENDING)])
        
        # Index for profiles
        self.profiles.create_index([('username', ASCENDING)], unique=True)
        
        # Add indexes for new collections
        self.comments.create_index([('tweet_id', ASCENDING)])
        self.comments.create_index([('parent_id', ASCENDING)])
        self.media.create_index([('tweet_id', ASCENDING)])
        self.quote_tweets.create_index([('tweet_id', ASCENDING)])
    
    def save_tweets(self, tweets: List[Dict], username: str) -> None:
        """Save tweets to MongoDB with proper formatting"""
        for tweet in tweets:
            tweet_doc = {
                'tweet_id': tweet.get('id'),
                'author': {
                    'username': username,
                },
                'content': tweet.get('text', ''),
                'timestamp': tweet.get('timestamp'),
                'metrics': {
                    'likes': int(tweet.get('likes', 0)),
                    'retweets': int(tweet.get('retweets', 0)),
                    'replies': int(tweet.get('replies', 0))
                },
                'scraped_at': datetime.now(),
                'is_thread': False,  # Will be updated when implementing thread detection
                'media': [],  # Will be populated when implementing media scraping
                'comments': []  # Will be populated when implementing comment scraping
            }
            
            # Use upsert to avoid duplicates
            self.tweets.update_one(
                {'tweet_id': tweet_doc['tweet_id']},
                {'$set': tweet_doc},
                upsert=True
            )
    
    def get_tweets_by_username(self, username: str, limit: int = 100):
        """Retrieve tweets for a specific username"""
        return list(self.tweets.find(
            {'author.username': username},
            {'_id': 0}  # Exclude MongoDB's _id field
        ).limit(limit))
    
    def get_tweets_by_date_range(self, start_date, end_date):
        """Retrieve tweets within a date range"""
        return list(self.tweets.find(
            {
                'timestamp': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            },
            {'_id': 0}
        ))

    def save_thread(self, thread_tweets: List[Dict]) -> None:
        """Save thread of tweets with proper relationships"""
        thread_id = thread_tweets[0]['id']
        
        for tweet in thread_tweets:
            tweet['thread_id'] = thread_id
            self.save_tweet(tweet)

    def save_comments(self, comments: List[Dict], parent_tweet_id: str) -> None:
        """Save comments/replies with reference to parent tweet"""
        for comment in comments:
            comment['parent_id'] = parent_tweet_id
            self.comments.update_one(
                {'id': comment['id']},
                {'$set': comment},
                upsert=True
            ) 