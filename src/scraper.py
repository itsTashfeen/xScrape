from playwright.sync_api import sync_playwright
import random
import time
import json
from datetime import datetime
import logging
from typing import Dict, List, Optional
from pathlib import Path
from .proxy_manager import ProxyManager
from ratelimit import limits, sleep_and_retry
from .db_manager import DatabaseManager

class TwitterScraper:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.db_manager = DatabaseManager()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        self.setup_logging()
        self.output_dir = Path("data")
        self.output_dir.mkdir(exist_ok=True)

    def setup_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "scraper.log"),
                logging.StreamHandler()
            ]
        )

    def random_delay(self, min_seconds: float = 3.0, max_seconds: float = 6.0):
        """Add a random delay between actions - adjusted for single proxy"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def simulate_human_scroll(self, page):
        """Simulate human-like scrolling behavior"""
        # Random scroll distance between 300 and 800 pixels
        scroll_distance = random.randint(300, 800)
        # Random scroll duration between 1 and 2 seconds
        scroll_duration = random.uniform(1000, 2000)
        
        page.mouse.wheel(0, scroll_distance)
        self.random_delay(1.0, 2.0)  # Random pause after scrolling

    def extract_tweet_data(self, tweet_element) -> Optional[Dict]:
        try:
            # Basic tweet data
            tweet_id = tweet_element.get_attribute('data-tweet-id')
            content = tweet_element.query_selector('[data-testid="tweetText"]').inner_text()
            
            # Get metrics
            metrics = {
                'likes': self._get_metric(tweet_element, 'like'),
                'retweets': self._get_metric(tweet_element, 'retweet'),
                'replies': self._get_metric(tweet_element, 'reply')
            }
            
            # Get media content
            media = self._extract_media(tweet_element)
            
            # Check if part of thread
            is_thread = bool(tweet_element.query_selector('[data-testid="conversationThread"]'))
            
            # Get quote tweet if exists
            quote_tweet = self._extract_quote_tweet(tweet_element)
            
            return {
                'id': tweet_id,
                'content': content,
                'metrics': metrics,
                'media': media,
                'is_thread': is_thread,
                'quote_tweet': quote_tweet,
                'timestamp': self._get_timestamp(tweet_element)
            }
        except Exception as e:
            logging.error(f"Error extracting tweet data: {str(e)}")
            return None

    def _extract_media(self, tweet_element) -> List[Dict]:
        """Extract media (images, videos) from tweet"""
        media = []
        media_container = tweet_element.query_selector('[data-testid="tweetPhoto"], [data-testid="tweetVideo"]')
        if media_container:
            if 'tweetPhoto' in media_container.get_attribute('data-testid'):
                images = media_container.query_selector_all('img')
                media.extend([{
                    'type': 'image',
                    'url': img.get_attribute('src')
                } for img in images])
            else:
                video = media_container.query_selector('video')
                if video:
                    media.append({
                        'type': 'video',
                        'url': video.get_attribute('src')
                    })
        return media

    async def scrape_thread(self, thread_id: str) -> List[Dict]:
        """Scrape entire thread of tweets"""
        thread_tweets = []
        page = self.context.new_page()
        
        try:
            await page.goto(f"https://twitter.com/i/web/status/{thread_id}")
            self.random_delay(3.0, 5.0)
            
            while True:
                tweets = page.query_selector_all('article[data-testid="tweet"]')
                for tweet in tweets:
                    tweet_data = self.extract_tweet_data(tweet)
                    if tweet_data:
                        thread_tweets.append(tweet_data)
                
                if not self.simulate_human_scroll(page):
                    break
                    
            return thread_tweets
            
        finally:
            await page.close()

    async def scrape_comments(self, tweet_id: str, limit: int = 100) -> List[Dict]:
        """Scrape comments/replies to a tweet"""
        comments = []
        page = self.context.new_page()
        
        try:
            await page.goto(f"https://twitter.com/i/web/status/{tweet_id}")
            self.random_delay(3.0, 5.0)
            
            while len(comments) < limit:
                comment_elements = page.query_selector_all('article[data-testid="tweet"]')
                for comment in comment_elements[1:]:  # Skip first tweet (original)
                    comment_data = self.extract_tweet_data(comment)
                    if comment_data:
                        comments.append(comment_data)
                        
                if len(comments) >= limit:
                    break
                    
                if not self.simulate_human_scroll(page):
                    break
                    
            return comments
            
        finally:
            await page.close()

    @sleep_and_retry
    @limits(calls=1, period=6)  # One request every 6 seconds
    def scrape_profile(self, username: str, tweet_limit: Optional[int] = 10) -> List[Dict]:
        tweets = []
        
        with sync_playwright() as p:
            try:
                proxy = self.proxy_manager.get_proxy()
                browser = p.chromium.launch(
                    proxy=proxy,
                    headless=True
                )
                
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=random.choice(self.user_agents)
                )
                
                page = context.new_page()
                page.goto(f"https://twitter.com/{username}")
                time.sleep(random.uniform(3, 5))
                
                while len(tweets) < tweet_limit:
                    tweet_elements = page.query_selector_all('article[data-testid="tweet"]')
                    
                    for tweet in tweet_elements:
                        tweet_data = self.extract_tweet_data(tweet)
                        if tweet_data:
                            tweets.append(tweet_data)
                            if len(tweets) >= tweet_limit:
                                break
                    
                    if not self._scroll_down(page):
                        break

            except Exception as e:
                logging.error(f"Error scraping profile {username}: {str(e)}")
                raise
            finally:
                if 'browser' in locals():
                    browser.close()

        self.db_manager.save_tweets(tweets, username)
        return tweets

    def _get_metric(self, tweet_element, metric_type: str) -> int:
        try:
            metric = tweet_element.query_selector(f'[data-testid="{metric_type}"]')
            return int(metric.inner_text() or 0)
        except:
            return 0

    def _scroll_down(self, page) -> bool:
        previous_height = page.evaluate('document.documentElement.scrollHeight')
        page.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
        time.sleep(random.uniform(1, 2))
        new_height = page.evaluate('document.documentElement.scrollHeight')
        return new_height > previous_height

    def save_tweets(self, tweets: List[Dict], username: str) -> None:
        filename = self.output_dir / f"tweets_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(tweets, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved {len(tweets)} tweets to {filename}")
        except Exception as e:
            logging.error(f"Error saving tweets: {str(e)}")
            raise