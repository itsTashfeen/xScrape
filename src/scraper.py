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
        self.db_manager = DatabaseManager()
        self.proxy_manager = ProxyManager()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
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

    def extract_tweet_data(self, tweet_element, context=None) -> Optional[Dict]:
        try:
            # Get tweet ID and URL
            tweet_url = None
            tweet_link = tweet_element.query_selector('a[href*="/status/"]')
            if tweet_link:
                tweet_url = tweet_link.get_attribute('href')
                tweet_id = tweet_url.split('/status/')[1]
            else:
                tweet_id = (
                    tweet_element.get_attribute('data-tweet-id') or
                    tweet_element.get_attribute('data-item-id')
                )
            
            if not tweet_id:
                logging.warning("Could not extract tweet ID")
                return None
                
            # Get full tweet content by visiting the tweet URL
            full_content = None
            if tweet_url and context:
                try:
                    tweet_page = context.new_page()
                    tweet_page.goto(f"https://twitter.com{tweet_url}")
                    self.random_delay(2, 3)
                    
                    # Try to expand the tweet content
                    try:
                        show_more = tweet_page.query_selector('[data-testid="tweet-text-show-more-link"]')
                        if show_more:
                            show_more.click()
                            time.sleep(1)
                    except:
                        pass
                    
                    # Get the full tweet text
                    text_element = tweet_page.query_selector('[data-testid="tweetText"]')
                    if text_element:
                        full_content = text_element.evaluate('''(element) => {
                            const walk = document.createTreeWalker(
                                element,
                                NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
                                null,
                                false
                            );
                            
                            let text = '';
                            let node;
                            
                            while (node = walk.nextNode()) {
                                if (node.nodeType === Node.TEXT_NODE) {
                                    text += node.textContent;
                                } else if (node.tagName === 'BR') {
                                    text += '\\n';
                                } else if (node.nodeType === Node.ELEMENT_NODE) {
                                    const style = window.getComputedStyle(node);
                                    if (style.display === 'block') {
                                        text += '\\n';
                                    }
                                    if (node.textContent) {
                                        text += node.textContent;
                                    }
                                }
                            }
                            
                            return text;
                        }''')
                    
                    tweet_page.close()
                except Exception as e:
                    logging.error(f"Error getting full tweet content: {str(e)}")
            
            # If we couldn't get the full content, fall back to the preview content
            if not full_content:
                text_element = tweet_element.query_selector('[data-testid="tweetText"]')
                if text_element:
                    full_content = text_element.evaluate('''(element) => {
                        const walk = document.createTreeWalker(
                            element,
                            NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
                            null,
                            false
                        );
                        
                        let text = '';
                        let node;
                        
                        while (node = walk.nextNode()) {
                            if (node.nodeType === Node.TEXT_NODE) {
                                text += node.textContent;
                            } else if (node.tagName === 'BR') {
                                text += '\\n';
                            } else if (node.nodeType === Node.ELEMENT_NODE) {
                                const style = window.getComputedStyle(node);
                                if (style.display === 'block') {
                                    text += '\\n';
                                }
                                if (node.textContent) {
                                    text += node.textContent;
                                }
                            }
                        }
                        
                        return text;
                    }''')
            
            if not full_content:
                return None
                
            return {
                'id': tweet_id,
                'text': full_content.strip(),
                'likes': self._get_metric(tweet_element, 'like'),
                'retweets': self._get_metric(tweet_element, 'retweet'),
                'replies': self._get_metric(tweet_element, 'reply')
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

    @sleep_and_retry
    @limits(calls=1, period=6)
    def scrape_profile(self, username: str, tweet_limit: Optional[int] = 10) -> List[Dict]:
        tweets = []
        tweets_seen = set()
        
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
                
                # Go to profile page
                logging.info(f"Navigating to https://twitter.com/{username}")
                page.goto(f"https://twitter.com/{username}")
                
                # Wait for page to load and check its state
                try:
                    # Wait for any of these elements to appear
                    page.wait_for_selector('[data-testid="primaryColumn"], [data-testid="emptyState"], [data-testid="error"]', timeout=15000)
                    
                    # Check for various page states
                    if page.query_selector('[data-testid="emptyState"]'):
                        logging.warning(f"Account @{username} appears to be private")
                        return []
                    
                    if page.query_selector('[data-testid="error"]'):
                        logging.error("Twitter returned an error page")
                        return []
                    
                    # Check if we're on the login page
                    if page.query_selector('text="Log in to Twitter"'):
                        logging.error("Twitter is requesting login")
                        return []
                    
                    # Check for rate limiting
                    if page.query_selector('text="Rate limit exceeded"'):
                        logging.error("Twitter rate limit exceeded")
                        return []
                    
                    logging.info("Page loaded successfully")
                    
                except Exception as e:
                    logging.error(f"Error waiting for page elements: {str(e)}")
                    return []
                
                self.random_delay(3, 5)
                
                scroll_attempts = 0
                max_scroll_attempts = 10
                last_tweets_count = 0
                
                while len(tweets) < tweet_limit and scroll_attempts < max_scroll_attempts:
                    try:
                        # Try different selectors for tweets
                        tweet_elements = page.query_selector_all('article[data-testid="tweet"], div[data-testid="tweet"]')
                        current_tweets_count = len(tweet_elements)
                        
                        logging.info(f"Found {current_tweets_count} tweets on page")
                        
                        # If we're not getting new tweets after scrolling, increment attempts
                        if current_tweets_count == last_tweets_count:
                            scroll_attempts += 1
                            logging.info(f"No new tweets found after scroll. Attempt {scroll_attempts}/{max_scroll_attempts}")
                        else:
                            scroll_attempts = 0
                            last_tweets_count = current_tweets_count
                        
                        for tweet in tweet_elements:
                            try:
                                # Try different ways to get the tweet ID
                                tweet_id = (
                                    tweet.get_attribute('data-tweet-id') or
                                    tweet.get_attribute('data-item-id') or
                                    tweet.query_selector('a[href*="/status/"]').get_attribute('href').split('/status/')[1]
                                )
                                
                                if not tweet_id or tweet_id in tweets_seen:
                                    continue
                                    
                                tweets_seen.add(tweet_id)
                                logging.info(f"Processing tweet {tweet_id}")
                                
                                tweet_data = self.extract_tweet_data(tweet, context)
                                if tweet_data:
                                    # Check if it's part of a thread
                                    thread_indicator = tweet.query_selector('[data-testid="conversationThread"]')
                                    if thread_indicator:
                                        logging.info(f"Tweet {tweet_id} is part of a thread")
                                        thread_tweets = self.scrape_thread(tweet_id, context)
                                        tweet_data['is_thread'] = True
                                        tweet_data['thread_tweets'] = thread_tweets
                                    else:
                                        tweet_data['is_thread'] = False
                                        tweet_data['thread_tweets'] = []
                                    
                                    # Get comments
                                    tweet_data['comments'] = self.scrape_comments(tweet_id, context)
                                    
                                    # Get media
                                    tweet_data['media'] = self._extract_media(tweet)
                                    
                                    tweets.append(tweet_data)
                                    logging.info(f"Successfully scraped tweet {len(tweets)}/{tweet_limit}")
                                    
                                    if len(tweets) >= tweet_limit:
                                        break
                            except Exception as e:
                                logging.error(f"Error processing tweet: {str(e)}")
                                continue
                        
                        if len(tweets) < tweet_limit:
                            # Scroll and wait for new content
                            if self._scroll_down(page):
                                logging.info("Successfully scrolled down")
                                page.wait_for_timeout(2000)  # Wait for new tweets to load
                            else:
                                scroll_attempts += 1
                                logging.info(f"Failed to scroll down. Attempt {scroll_attempts}/{max_scroll_attempts}")
                                
                            # Try to click "Show more tweets" if present
                            try:
                                show_more = page.query_selector('span:has-text("Show more")')
                                if show_more:
                                    show_more.click()
                                    logging.info("Clicked 'Show more' button")
                                    self.random_delay(2, 3)
                            except Exception as e:
                                logging.debug(f"No 'Show more' button found: {str(e)}")
                                
                    except Exception as e:
                        logging.error(f"Error during tweet collection: {str(e)}")
                        scroll_attempts += 1

            except Exception as e:
                logging.error(f"Error during profile scrape: {str(e)}")
            finally:
                if 'browser' in locals():
                    browser.close()

        self.db_manager.save_tweets(tweets, username)
        return tweets

    def scrape_thread(self, tweet_id: str, context) -> List[Dict]:
        """Scrape entire thread of tweets"""
        thread_tweets = []
        page = context.new_page()
        
        try:
            page.goto(f"https://twitter.com/i/web/status/{tweet_id}")
            self.random_delay(3.0, 5.0)
            
            while True:
                tweets = page.query_selector_all('article[data-testid="tweet"]')
                for tweet in tweets:
                    tweet_data = self.extract_tweet_data(tweet)
                    if tweet_data:
                        thread_tweets.append(tweet_data)
                
                if not self._scroll_down(page):
                    break
                    
            return thread_tweets
            
        finally:
            page.close()

    def scrape_comments(self, tweet_id: str, context, limit: int = 5) -> List[Dict]:
        """Scrape comments/replies to a tweet"""
        comments = []
        page = context.new_page()
        
        try:
            page.goto(f"https://twitter.com/i/web/status/{tweet_id}")
            self.random_delay(3.0, 5.0)
            
            while len(comments) < limit:
                comment_elements = page.query_selector_all('article[data-testid="tweet"]')
                for comment in comment_elements[1:]:  # Skip first tweet (original)
                    comment_data = self.extract_tweet_data(comment)
                    if comment_data:
                        comment_data['media'] = self._extract_media(comment)
                        comments.append(comment_data)
                        
                if len(comments) >= limit:
                    break
                    
                if not self._scroll_down(page):
                    break
                    
            return comments
            
        finally:
            page.close()

    def _get_metric(self, tweet_element, metric_type: str) -> int:
        try:
            # First try to find the group element
            group = tweet_element.query_selector(f'[data-testid="{metric_type}"]')
            if not group:
                return 0
                
            # Look for the actual number within the group
            metric_text = group.query_selector('[data-testid="app-text-transition-container"]')
            if not metric_text:
                return 0
                
            text = metric_text.inner_text().strip()
            if not text:
                return 0
                
            # Handle K/M suffixes
            if 'K' in text:
                return int(float(text.replace('K', '')) * 1000)
            elif 'M' in text:
                return int(float(text.replace('M', '')) * 1000000)
            return int(text) if text.isdigit() else 0
        except Exception as e:
            logging.error(f"Error getting metric {metric_type}: {str(e)}")
            return 0

    def _scroll_down(self, page) -> bool:
        """Scroll down and wait for new content to load"""
        try:
            previous_height = page.evaluate('document.documentElement.scrollHeight')
            page.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
            self.random_delay(2, 3)  # Wait longer for content to load
            
            # Wait for possible dynamic content loading
            page.wait_for_timeout(1000)  # Additional 1 second wait
            
            # Try to find the "Show more tweets" button and click it if present
            show_more = page.query_selector('span:has-text("Show more tweets")')
            if show_more:
                show_more.click()
                self.random_delay(2, 3)
            
            new_height = page.evaluate('document.documentElement.scrollHeight')
            return new_height > previous_height
        except Exception as e:
            logging.error(f"Error during scroll: {str(e)}")
            return False

    def save_tweets(self, tweets: List[Dict], username: str) -> None:
        filename = self.output_dir / f"tweets_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(tweets, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved {len(tweets)} tweets to {filename}")
        except Exception as e:
            logging.error(f"Error saving tweets: {str(e)}")
            raise