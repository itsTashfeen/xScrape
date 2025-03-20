from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError
import os
import logging
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        try:
            self.client = MongoClient(os.getenv('MONGODB_URI'))
            self.client.admin.command('ping')
            self.db = self.client['twitter_scraper']
            self.tweets = self.db['tweets']
            self.profiles = self.db['profiles']
            self.threads = self.db['threads']
            self.comments = self.db['comments']
            self.media = self.db['media']
            self.quote_tweets = self.db['quote_tweets']
            self.setup_indexes()
            logging.info("Successfully connected to MongoDB")
        except PyMongoError as e:
            logging.error(f"MongoDB Error: {str(e)}")
            raise

    def setup_indexes(self):
        self.tweets.create_index([('tweet_id', ASCENDING)], unique=True)
        self.tweets.create_index([('author.username', ASCENDING)])
        self.tweets.create_index([('timestamp', ASCENDING)])
        self.tweets.create_index([('thread_id', ASCENDING)])
        self.profiles.create_index([('username', ASCENDING)], unique=True)
        self.comments.create_index([('tweet_id', ASCENDING)])
        self.comments.create_index([('parent_id', ASCENDING)])
        self.media.create_index([('tweet_id', ASCENDING)])
        self.quote_tweets.create_index([('tweet_id', ASCENDING)])

    def save_tweets(self, tweets: List[Dict], username: str) -> None:
        for tweet in tweets:
            tweet_doc = {
                'tweet_id': tweet.get('id'),
                'author': {'username': username},
                'content': tweet.get('text', ''),
                'metrics': {
                    'likes': int(tweet.get('likes', 0)),
                    'retweets': int(tweet.get('retweets', 0)),
                    'replies': int(tweet.get('replies', 0))
                },
                'is_thread': tweet.get('is_thread', False),
                'thread_tweets': tweet.get('thread_tweets', []),
                'comments': tweet.get('comments', []),
                'media': tweet.get('media', []),
                'scraped_at': datetime.now()
            }
            
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