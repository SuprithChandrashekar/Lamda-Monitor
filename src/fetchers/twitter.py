import httpx
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from .base import SocialMediaFetcher
from ..config import settings
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TwitterFetcher(SocialMediaFetcher):
    def __init__(self):
        super().__init__(settings.SCRAPE_CREATORS_API_KEY, None)
        self.base_url = "https://api.scrapecreators.com/v1/twitter/user-tweets"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": settings.SCRAPE_CREATORS_API_KEY,
                "Content-Type": "application/json"
            }
        )
        self.retry_delay = 60  # seconds
        self.max_retries = 3

    async def authenticate(self) -> bool:
        """Implement the abstract authenticate method"""
        # No authentication needed beyond API key which is handled in the constructor
        return True

    async def fetch_posts(self, username: str, since: datetime = None, use_selenium: bool = False) -> List[Dict[str, Any]]:
        """Fetch posts using ScrapeCreators API with fallback to Selenium"""
        for attempt in range(self.max_retries):
            try:
                params = {
                    "handle": username,
                    "count": 20
                }
                if since:
                    params["start_time"] = since.isoformat()
                
                logger.debug(f"Fetching tweets for {username} with params: {params}")
                response = await self.client.get("", params=params)

                if response.status_code != 200:
                    logger.error(f"API Error: {response.status_code} - {response.text}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    elif use_selenium:
                        logger.warning(f"API failed for {username}, falling back to Selenium.")
                        return await self._fetch_via_selenium(username)
                    return []

                data = response.json()
                logger.debug(f"API Response structure: {data.keys()}")
                
                # Get tweets directly from the response and filter out None values
                tweets = [t for t in data.get('tweets', []) if t is not None]
                logger.debug(f"Found {len(tweets)} valid tweets in response")
                
                extracted_tweets = []
                for tweet in tweets:
                    try:
                        if not isinstance(tweet, dict):
                            logger.warning(f"Skipping invalid tweet format: {type(tweet)}")
                            continue

                        # Get the core tweet data
                        tweet_id = tweet.get('rest_id')
                        legacy_data = tweet.get('legacy', {})
                        
                        # Handle retweets
                        if 'retweeted_status_result' in tweet and tweet['retweeted_status_result'] and tweet['retweeted_status_result'].get('result'):
                            retweet_data = tweet['retweeted_status_result']['result']
                            legacy_data = retweet_data.get('legacy', legacy_data)
                        
                        # Extract tweet content and metadata
                        content = legacy_data.get('full_text', '')
                        posted_at_str = legacy_data.get('created_at')
                        
                        # Only process valid tweets
                        if content and tweet_id:
                            posted_at = None
                            if posted_at_str:
                                try:
                                    posted_at = datetime.strptime(posted_at_str, '%a %b %d %H:%M:%S %z %Y')
                                except ValueError as e:
                                    logger.warning(f"Could not parse datetime string '{posted_at_str}': {e}")

                            extracted_tweets.append({
                                'platform_post_id': str(tweet_id),
                                'content': content,
                                'posted_at': posted_at,
                                'metrics': {
                                    'likes': legacy_data.get('favorite_count', 0),
                                    'retweets': legacy_data.get('retweet_count', 0),
                                    'replies': legacy_data.get('reply_count', 0)
                                }
                            })
                    except Exception as e:
                        logger.warning(f"Error parsing tweet {tweet.get('rest_id', 'unknown')}: {str(e)}")
                        continue

                return extracted_tweets

            except Exception as e:
                logger.error(f"Error fetching tweets: {e}", exc_info=True)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                elif use_selenium:
                    logger.warning(f"An error occurred for {username}, falling back to Selenium.")
                    return await self._fetch_via_selenium(username)
                return []

    async def _fetch_via_selenium(self, username: str) -> List[Dict[str, Any]]:
        """Fallback method to fetch posts using Selenium browser automation"""
        logger.info(f"Attempting to fetch posts for {username} via Selenium.")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=chrome_options)
        posts = []

        try:
            driver.get(f"https://twitter.com/{username}")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='tweet']"))
            )

            tweets = driver.find_elements(By.CSS_SELECTOR, "[data-testid='tweet']")
            for tweet in tweets[:10]:
                try:
                    content_element = tweet.find_element(By.CSS_SELECTOR, "[data-testid='tweetText']")
                    content = content_element.text
                    time_element = tweet.find_element(By.CSS_SELECTOR, "time")
                    posted_at = datetime.fromisoformat(time_element.get_attribute("datetime"))
                    tweet_id = tweet.get_attribute("data-testid")

                    posts.append({
                        'platform_post_id': tweet_id,
                        'content': content,
                        'posted_at': posted_at,
                        'metrics': {
                            'likes': 0,
                            'retweets': 0,
                            'replies': 0
                        }
                    })
                except Exception as e:
                    logger.warning(f"Error parsing tweet via Selenium: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error during Selenium fetching for {username}: {e}", exc_info=True)
        finally:
            driver.quit()

        return posts

    async def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get user information using ScrapeCreators API"""
        try:
            # THIS IS ALSO A CRITICAL CHANGE: Use 'handle' instead of 'username'
            params = {"handle": username}
            response = await self.client.get("/twitter/user-profile", params=params)
            
            if response.status_code == 200:
                data = response.json()
                user = data.get("user", {})
                user_result = user.get('core', {}).get('user_results', {}).get('result', {})
                user_legacy = user_result.get('legacy', {})

                return {
                    'id': str(user_result.get('rest_id')),
                    'name': user_legacy.get('name'),
                    'username': user_legacy.get('screen_name'),
                    'followers_count': user_legacy.get('followers_count'),
                    'following_count': user_legacy.get('friends_count')
                }
            logger.error(f"Failed to fetch user info for {username}: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error fetching user info for {username}: {e}", exc_info=True)
        
        return None