import asyncio
import sys
from apify import Actor

from .models import InputModel, DouyinTrend, EngagementMetrics
from .scraper import DouyinScraper
from .hot_trends import fetch_hot_hashtags

sys.stdout.reconfigure(encoding='utf-8')


async def main():
    """Main entrypoint for Douyin trending scraper actor."""
    async with Actor:
        input_data = await Actor.get_input() or {}
        cfg = InputModel(**input_data)

        Actor.log.info("Starting Douyin Trending Video Scraper")
        Actor.log.info(f"Max keywords: {getattr(cfg, 'max_hashtags', 10)}")
        Actor.log.info(f"Max videos per keyword: {getattr(cfg, 'max_posts_per_hashtag', 10)}")

        Actor.log.info("Fetching trending keywords from Douyin hot list…")
        trending_keywords = await fetch_hot_hashtags(limit=getattr(cfg, 'max_hashtags', 10))

        Actor.log.info(f"Found {len(trending_keywords)} trending topics.")
        for i, kw in enumerate(trending_keywords, start=1):
            kw["rank"] = kw.get("rank", i)
            Actor.log.info(f"#{kw['rank']}: {kw['keyword']} (heat={kw.get('heat')})")

        all_results = []

        for keyword_info in trending_keywords:
            keyword = keyword_info["keyword"]
            rank = keyword_info["rank"]

            Actor.log.info(f"Scraping videos for '{keyword}' (rank {rank})")
            scraper = DouyinScraper(keyword)

            raw_data = await scraper.fetch_json()
            if not raw_data:
                Actor.log.warning(f"No data for {keyword}")
                continue

            structured = await scraper.extract_posts(raw_data)
            videos = structured.videos[: getattr(cfg, "max_posts_per_hashtag", 10)]
            Actor.log.info(f"Collected {len(videos)} structured videos for '{keyword}'")

            total_likes = sum(v.likes or 0 for v in videos)
            total_comments = sum(v.comments or 0 for v in videos)
            total_shares = sum(v.shares or 0 for v in videos)
            avg_engagement_rate = round(
                sum((v.likes or 0) + (v.comments or 0) + (v.shares or 0) for v in videos)
                / max(1, len(videos)),
                2,
            )

            engagement = EngagementMetrics(
                total_likes=total_likes,
                total_comments=total_comments,
                total_reposts=total_shares,
                avg_engagement_rate=avg_engagement_rate,
            )

            trend_data = DouyinTrend(
            keyword=keyword,
    rank=rank,
    heat=keyword_info.get("heat"),
    total_videos=len(videos),
    engagement_metrics=engagement,
    videos=videos,
)

            await Actor.push_data(trend_data.model_dump())
            all_results.append(trend_data.model_dump())

        Actor.log.info(f"Completed scraping {len(all_results)} Douyin trends successfully.")


if __name__ == "__main__":
    asyncio.run(main())
