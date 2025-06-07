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

class TwitterFetcher(SocialMediaFetcher):
    def __init__(self):
        super().__init__(settings.SCRAPE_CREATORS_API_KEY, None)
        self.base_url = "https://api.scrapecreators.com/v1"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {settings.SCRAPE_CREATORS_API_KEY}",
                "Accept": "application/json"
            }
        )
        self.retry_delay = 60  # seconds
        self.max_retries = 3

    async def authenticate(self) -> bool:
        """Verify authentication with ScrapeCreators API"""
        try:
            response = await self.client.get("/credits")
            return response.status_code == 200
        except Exception:
            return False

    async def fetch_posts(self, username: str, since: datetime = None, use_selenium: bool = False) -> List[Dict[str, Any]]:
        """Fetch posts using ScrapeCreators API with fallback to Selenium"""
        for attempt in range(self.max_retries):
            try:
                params = {
                    "username": username,
                    "count": 20  # Limiting to conserve credits
                }
                
                response = await self.client.get("/twitter/user-tweets", params=params)
                if response.status_code != 200:
                    print(f"API Error: {response.status_code} - {response.text}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    elif use_selenium:
                        return await self._fetch_via_selenium(username)
                    return []

                data = response.json()
                tweets = data.get("tweets", [])
                
                return [{
                    'platform_post_id': str(tweet.get('id')),
                    'content': tweet.get('text', ''),
                    'posted_at': datetime.fromisoformat(tweet.get('created_at').replace('Z', '+00:00')),
                    'metrics': {
                        'likes': tweet.get('likes', 0),
                        'retweets': tweet.get('retweets', 0),
                        'replies': tweet.get('replies', 0)
                    }
                } for tweet in tweets if tweet.get('text')]

            except Exception as e:
                print(f"Error fetching tweets: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                elif use_selenium:
                    return await self._fetch_via_selenium(username)
                return []

    async def _fetch_via_selenium(self, username: str) -> List[Dict[str, Any]]:
        """Fallback method to fetch posts using Selenium browser automation"""
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
            for tweet in tweets[:10]:  # Limit to last 10 tweets
                try:
                    content = tweet.find_element(By.CSS_SELECTOR, "[data-testid='tweetText']").text
                    time_element = tweet.find_element(By.CSS_SELECTOR, "time")
                    posted_at = datetime.fromisoformat(time_element.get_attribute("datetime"))
                    tweet_id = tweet.get_attribute("data-tweet-id")

                    posts.append({
                        'platform_post_id': tweet_id,
                        'content': content,
                        'posted_at': posted_at,
                    })
                except Exception as e:
                    print(f"Error parsing tweet: {e}")
                    continue

        finally:
            driver.quit()

        return posts

    async def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get user information using ScrapeCreators API"""
        try:
            params = {"username": username}
            response = await self.client.get("/twitter/user-profile", params=params)
            
            if response.status_code == 200:
                data = response.json()
                user = data.get("user", {})
                return {
                    'id': str(user.get('id')),
                    'name': user.get('name'),
                    'username': user.get('username'),
                    'followers_count': user.get('followers_count'),
                    'following_count': user.get('following_count')
                }
        except Exception as e:
            print(f"Error fetching user info: {e}")
        
        return None