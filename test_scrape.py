from src.scraper import TwitterScraper

def main():
    try:
        scraper = TwitterScraper()
        username = "elonmusk"  # test account
        tweet_limit = 5  # start small for testing
        
        print(f"Starting to scrape {username}'s tweets...")
        tweets = scraper.scrape_profile(username, tweet_limit=tweet_limit)
        
        print(f"\nSuccessfully scraped {len(tweets)} tweets!")
        
        # Print the tweets
        for i, tweet in enumerate(tweets, 1):
            print(f"\nTweet {i}:")
            print("-" * 50)
            print(f"Content: {tweet.get('text', 'No content')[:100]}...")
            print(f"Likes: {tweet.get('likes', 0)}")
            print(f"Retweets: {tweet.get('retweets', 0)}")
            print(f"Replies: {tweet.get('replies', 0)}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error during scraping: {str(e)}")

if __name__ == "__main__":
    main() 