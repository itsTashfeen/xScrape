from db_manager import DatabaseManager
from datetime import datetime, timedelta

class TweetAnalyzer:
    def __init__(self):
        self.db = DatabaseManager()
    
    def get_user_stats(self, username: str):
        """Get basic stats for a user's tweets"""
        tweets = self.db.get_tweets_by_username(username)
        
        if not tweets:
            return None
            
        total_likes = sum(t['metrics']['likes'] for t in tweets)
        total_retweets = sum(t['metrics']['retweets'] for t in tweets)
        total_replies = sum(t['metrics']['replies'] for t in tweets)
        
        return {
            'username': username,
            'tweet_count': len(tweets),
            'avg_likes': total_likes / len(tweets),
            'avg_retweets': total_retweets / len(tweets),
            'avg_replies': total_replies / len(tweets),
            'total_engagement': total_likes + total_retweets + total_replies
        }
    
    def get_recent_activity(self, days: int = 7):
        """Get tweet activity for the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.db.get_tweets_by_date_range(start_date, end_date) 