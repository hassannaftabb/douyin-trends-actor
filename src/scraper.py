import json
import aiohttp
import asyncio
from typing import Optional, Any
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from apify import Actor
from .auth import get_douyin_auth
from .models import DouyinResponseModel
from .utils import parse_douyin_video


class DouyinScraper:
    """Lightweight Douyin search scraper that supports pagination and structured extraction."""

    BASE_URL = (
        "https://www.douyin.com/aweme/v1/web/general/search/single/"
        "?device_platform=webapp&aid=6383&channel=channel_pc_web&search_channel=aweme_general"
        "&enable_history=1&search_source=normal_search&query_correct_type=1&is_filter_search=0"
        "&from_group_id=&disable_rs=1&need_filter_settings=0&list_type=single"
        "&update_version_code=170400&pc_client_type=1&pc_libra_divert=Windows&support_h265=1"
        "&support_dash=1&cpu_core_num=24&version_code=190600&version_name=19.6.0"
        "&cookie_enabled=true&screen_width=1920&screen_height=1080"
        "&browser_language=en-PK&browser_platform=Win32&browser_name=Chrome"
        "&browser_version=142.0.0.0&browser_online=true&engine_name=Blink"
        "&engine_version=142.0.0.0&os_name=Windows&os_version=10"
        "&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=100"
    )

    def __init__(self, keyword: str, limit: int = 30, count_per_page: int = 10):
        self.keyword = keyword
        self.limit = limit
        self.count = count_per_page
        creds = get_douyin_auth()
        self.headers = creds["headers"]
        self.cookies = creds["cookies"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(3),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    )
    async def _fetch_page(self, session, offset: int) -> Optional[Any]:
        """Fetch a single Douyin JSON page based on offset."""
        url = f"{self.BASE_URL}&keyword={self.keyword}&offset={offset}&count={self.count}"
        Actor.log.info(f"[douyin] Fetching offset={offset} ...")

        async with session.get(url, headers=self.headers, cookies=self.cookies) as resp:
            Actor.log.info(
                f"Status {resp.status} | Content-Type: {resp.headers.get('Content-Type')}"
            )
            if resp.status != 200:
                Actor.log.warning(f"[douyin] Non-200 response at offset {offset}")
                return None

            if "application/json" not in resp.headers.get("Content-Type", ""):
                Actor.log.warning(f"[douyin] Non-JSON response at offset {offset}")
                return None

            return await resp.json(content_type=None)

    async def fetch_json(self) -> Optional[Any]:
        """Fetch multiple pages up to the specified limit."""
        timeout = aiohttp.ClientTimeout(total=30)
        all_data = []
        offset = 0
        fetched = 0

        async with aiohttp.ClientSession(timeout=timeout) as session:
            while fetched < self.limit:
                data = await self._fetch_page(session, offset)
                if not data:
                    break

                raw_data = data.get("data", [])
                page_items = raw_data.get("data", []) if isinstance(raw_data, dict) else raw_data
                if not page_items:
                    break

                all_data.extend(page_items)
                fetched += len(page_items)
                offset += self.count

                await asyncio.sleep(1.5)

        Actor.log.info(f"[douyin] ✅ Collected total {len(all_data)} items across pages.")
        return {"data": all_data}

    async def extract_posts(self, data) -> DouyinResponseModel:
        """Convert raw JSON data into structured Pydantic models."""
        raw_data = data.get("data", [])
        aweme_list = raw_data.get("data", []) if isinstance(raw_data, dict) else raw_data

        videos = []
        for item in aweme_list:
            aweme = item.get("aweme_info") if isinstance(item, dict) else None
            if not aweme:
                continue
            parsed = parse_douyin_video(aweme)
            if parsed:
                videos.append(parsed)

        Actor.log.info(f"[douyin] Parsed {len(videos)} structured videos.")
        return DouyinResponseModel(
            keyword=self.keyword,
            total_results=len(videos),
            videos=videos,
        )
