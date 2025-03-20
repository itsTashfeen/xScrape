from src.scraper import TwitterScraper
import logging

def main():
    try:
        # Initialize the scraper
        scraper = TwitterScraper()
        
        # Test parameters
        username = "TheShortBear"  # Changed to TheShortBear
        tweet_limit = 5  # small number for testing
        
        print(f"\nStarting test scrape of {username}'s profile...")
        print(f"Will attempt to fetch {tweet_limit} tweets\n")
        
        # Perform the scrape
        tweets = scraper.scrape_profile(username, tweet_limit=tweet_limit)
        
        # Print results
        print(f"\n✅ Successfully scraped {len(tweets)} tweets!")
        
        # Show sample of tweets
        for i, tweet in enumerate(tweets, 1):
            print(f"\nTweet {i}:")
            print("-" * 50)
            print(f"Content: {tweet.get('text', 'No content')[:100]}...")
            print(f"Likes: {tweet.get('likes', 0)}")
            print(f"Retweets: {tweet.get('retweets', 0)}")
            print(f"Replies: {tweet.get('replies', 0)}")
            if tweet.get('is_thread'):
                print("This is a thread")
            if tweet.get('comments'):
                print(f"Has {len(tweet['comments'])} comments")
            print("-" * 50)
            
    except Exception as e:
        print(f"\n❌ Error during scraping: {str(e)}")
        logging.error(f"Scraping error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 