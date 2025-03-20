from src.scraper import TwitterScraper
import time

def test_scrape():
    try:
        # Initialize the scraper
        scraper = TwitterScraper()
        
        # Test with a small number of tweets first
        username = "TheShortBear"  # or any other public Twitter account
        tweet_limit = 5  # start with just 5 tweets for testing
        
        print(f"Starting to scrape {username}'s tweets...")
        print("(Limited to first 5 tweets for testing)")
        
        tweets = scraper.scrape_profile(username, tweet_limit=tweet_limit)
        
        print(f"\n✅ Successfully scraped {len(tweets)} tweets!")
        
        # Print the tweets to verify content
        for i, tweet in enumerate(tweets, 1):
            print(f"\nTweet {i}:")
            print("-" * 50)
            print(f"Content: {tweet.get('content', 'No content')[:100]}...")
            print(f"Likes: {tweet.get('metrics', {}).get('likes', 0)}")
            print(f"Retweets: {tweet.get('metrics', {}).get('retweets', 0)}")
            print(f"Replies: {tweet.get('metrics', {}).get('replies', 0)}")
            print("-" * 50)
            time.sleep(1)  # Small delay between printing tweets
            
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")

if __name__ == "__main__":
    test_scrape() 