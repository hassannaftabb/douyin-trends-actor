import asyncio
import sys
import os
from apify import Actor
from playwright.async_api import async_playwright

from .models import InputModel, DouyinTrend, EngagementMetrics
from .scraper import DouyinScraper
from .hot_trends import fetch_hot_hashtags

sys.stdout.reconfigure(encoding="utf-8")


async def main():
    """Main entrypoint for Douyin trending scraper actor with persistent browser session."""
    async with Actor:
        input_data = await Actor.get_input() or {}
        cfg = InputModel(**input_data)

        Actor.log.info("Starting Douyin Trending Video Scraper")
        Actor.log.info(f"Max keywords: {getattr(cfg, 'max_hashtags', 3)}")
        Actor.log.info(f"Max videos per keyword: {getattr(cfg, 'max_posts_per_hashtag', 10)}")

        Actor.log.info("Fetching trending keywords from Douyin hot list…")
        trending_keywords = await fetch_hot_hashtags(limit=getattr(cfg, "max_hashtags", 3))
        Actor.log.info(f"Found {len(trending_keywords)} trending topics.")
        for i, kw in enumerate(trending_keywords, start=1):
            kw["rank"] = kw.get("rank", i)
            Actor.log.info(f"#{kw['rank']}: {kw['keyword']} (heat={kw.get('heat')})")

        all_results = []
        failed_keywords = []
        state_path = "douyin_storage_state.json"

        async with async_playwright() as p:
            Actor.log.info("[session] Launching single persistent Chromium browser…")
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--disable-web-security",
                    "--no-sandbox",
                    "--disable-gpu",
                ],
            )

            if os.path.exists(state_path):
                Actor.log.info("[session] Found existing storage state — reusing cookies.")
                context = await browser.new_context(
                    storage_state=state_path,
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36"
                    ),
                    locale="zh-CN",
                    viewport={"width": 1280, "height": 800},
                )
            else:
                Actor.log.info("[session] No storage state found — creating fresh context.")
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36"
                    ),
                    locale="zh-CN",
                    viewport={"width": 1280, "height": 800},
                )

                warm = await context.new_page()
                Actor.log.info("[session] Warming up Douyin homepage to establish cookies…")
                try:
                    await warm.goto("https://www.douyin.com", wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(5)
                except Exception as e:
                    Actor.log.warning(f"[session] Warm-up failed: {e}")
                await warm.close()
                await context.storage_state(path=state_path)
                Actor.log.info("[session] Storage state saved for reuse.")

            for keyword_info in trending_keywords:
                keyword = keyword_info["keyword"]
                rank = keyword_info["rank"]

                Actor.log.info(f"Scraping videos for '{keyword}' (rank {rank})")

                scraper = DouyinScraper(
                    keyword=keyword,
                    limit=getattr(cfg, "max_posts_per_hashtag", 10),
                    shared_context=context,
                )

                raw_data = await scraper.fetch_json()
                if not raw_data:
                    Actor.log.warning(f"No data for {keyword}")
                    failed_keywords.append(keyword_info)
                    continue

                structured = await scraper.extract_posts(raw_data)
                videos = structured.videos
                Actor.log.info(f"Collected {len(videos)} structured videos for '{keyword}'")

                if len(videos) == 0:
                    failed_keywords.append(keyword_info)
                    continue

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

                await asyncio.sleep(3 + (rank % 3))

            # 🔁 Retry failed keywords once
            if failed_keywords:
                Actor.log.info(f"[retry] Retrying {len(failed_keywords)} failed keywords after short delay...")
                await asyncio.sleep(30)
                for keyword_info in failed_keywords:
                    keyword = keyword_info["keyword"]
                    rank = keyword_info["rank"]

                    Actor.log.info(f"[retry] Retrying '{keyword}' (rank {rank})")

                    scraper = DouyinScraper(
                        keyword=keyword,
                        limit=getattr(cfg, "max_posts_per_hashtag", 10),
                        shared_context=context,
                    )

                    raw_data = await scraper.fetch_json()
                    if not raw_data:
                        Actor.log.warning(f"[retry] Still no data for {keyword}")
                        continue

                    structured = await scraper.extract_posts(raw_data)
                    videos = structured.videos
                    Actor.log.info(f"[retry] Collected {len(videos)} structured videos for '{keyword}'")

                    if len(videos) == 0:
                        Actor.log.warning(f"[retry] No videos again for '{keyword}'")
                        continue

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

                    await asyncio.sleep(3 + (rank % 3))

            Actor.log.info("[session] Closing persistent browser context.")
            await context.close()
            await browser.close()

        Actor.log.info(f"Completed scraping {len(all_results)} Douyin trends successfully.")


if __name__ == "__main__":
    asyncio.run(main())
