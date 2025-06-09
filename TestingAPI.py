import asyncio
from src.fetchers.twitter import TwitterFetcher # Adjust import path as needed

async def test_twitter_fetcher():
    fetcher = TwitterFetcher()
    # No explicit authentication check needed here anymore
    posts = await fetcher.fetch_posts("POTUS")
    print(f"Found {len(posts)} posts")
    if posts:
        print(f"First post: {posts[0]}")

if __name__ == "__main__":
    asyncio.run(test_twitter_fetcher())