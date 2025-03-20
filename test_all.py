from dotenv import load_dotenv
import os
from pymongo import MongoClient
from src.scraper import TwitterScraper

def test_database():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get MongoDB connection string
        uri = os.getenv('MONGODB_URI')
        client = MongoClient(uri)
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB Connection: SUCCESS")
        return True
    except Exception as e:
        print("❌ MongoDB Connection: FAILED")
        print(f"Error: {str(e)}")
        return False

def test_proxy():
    try:
        scraper = TwitterScraper()
        # Test a simple request with the proxy
        print("Testing proxy connection...")
        result = scraper.test_proxy()
        if result:
            print("✅ Proxy Connection: SUCCESS")
            return True
        else:
            print("❌ Proxy Connection: FAILED")
            return False
    except Exception as e:
        print("❌ Proxy Connection: FAILED")
        print(f"Error: {str(e)}")
        return False

def test_scrape():
    try:
        scraper = TwitterScraper()
        # Test scrape with a small number of tweets
        username = "elonmusk"  # test account
        print(f"Testing scrape for user {username} (first 3 tweets)...")
        tweets = scraper.scrape_profile(username, tweet_limit=3)
        
        if tweets and len(tweets) > 0:
            print("✅ Scraping Test: SUCCESS")
            print(f"Retrieved {len(tweets)} tweets")
            # Print first tweet as sample
            print("\nSample tweet:")
            print(f"Content: {tweets[0].get('content', 'No content')[:100]}...")
            print(f"Likes: {tweets[0].get('metrics', {}).get('likes', 0)}")
            return True
        else:
            print("❌ Scraping Test: FAILED")
            return False
    except Exception as e:
        print("❌ Scraping Test: FAILED")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Starting Tests...\n")
    
    # Test database connection
    print("1. Testing MongoDB Connection...")
    db_success = test_database()
    print()
    
    # Test proxy connection
    print("2. Testing Proxy Connection...")
    proxy_success = test_proxy()
    print()
    
    # Test scraping
    print("3. Testing Tweet Scraping...")
    if db_success and proxy_success:
        scrape_success = test_scrape()
    else:
        print("❌ Skipping scrape test due to previous failures")
        scrape_success = False
    
    print("\n📊 Test Summary:")
    print(f"Database Connection: {'✅' if db_success else '❌'}")
    print(f"Proxy Connection: {'✅' if proxy_success else '❌'}")
    print(f"Tweet Scraping: {'✅' if scrape_success else '❌'}") 