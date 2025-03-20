import requests
from scraper import TwitterScraper
from proxy_manager import ProxyManager

def test_proxy():
    proxy_manager = ProxyManager()
    proxy = proxy_manager.get_proxy()
    
    proxies = {
        'http': f"http://{proxy['username']}:{proxy['password']}@{proxy['server'].replace('http://', '')}",
        'https': f"http://{proxy['username']}:{proxy['password']}@{proxy['server'].replace('http://', '')}"
    }
    
    try:
        response = requests.get(
            'https://geo.brdtest.com/welcome.txt?product=isp&method=native',
            proxies=proxies
        )
        print(f"Proxy Test Response: {response.text}")
        return True
    except Exception as e:
        print(f"Proxy Test Failed: {str(e)}")
        return False

def main():
    if test_proxy():
        scraper = TwitterScraper()
        username = "elonmusk"  # example username
        tweets = scraper.scrape_profile(username, tweet_limit=100)
        scraper.save_tweets(tweets, username)
    else:
        print("Please check your proxy configuration")

if __name__ == "__main__":
    main() 