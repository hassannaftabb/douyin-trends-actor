import asyncio
import json
import re
import time
import gzip
from typing import Any, List
from apify import Actor
from playwright.async_api import async_playwright
from .models import DouyinResponseModel
from .utils import parse_douyin_video

class DouyinScraper:
    """Headless Playwright scraper for Douyin search capturing /stream/ + /single/ requests dynamically."""

    TARGET_API_PREFIXES = [
        "https://www.douyin.com/aweme/v1/web/general/search/stream/",
        "https://www.douyin.com/aweme/v1/web/general/search/single/",
    ]

    def __init__(self, keyword: str, limit: int = 25):
        self.keyword = keyword
        self.limit = limit
        self.collected_chunks: List[dict] = []
        self.videos_flat: List[dict] = []
        self.last_request_time = time.time()
        self.stop_event = asyncio.Event()

    @staticmethod
    def clean_chunked_body(raw_bytes: bytes) -> str:
        """Remove HTTP chunked encoding markers and clean up."""
        text = raw_bytes.decode("utf-8", errors="ignore")
        text = re.sub(r"(?mi)^[0-9a-f]+\r?\n", "", text)
        text = text.replace("\r", "").replace("\n", "")
        return text.strip("\x00\t ")

    @staticmethod
    def extract_json_chunks(raw_text: str) -> List[Any]:
        """Extract multiple JSON objects from chunked /stream/ body."""
        potential_objs = re.findall(r"(\{.*?\})(?=\s*\{|\s*$)", raw_text, re.DOTALL)
        parsed = []
        for chunk in potential_objs:
            try:
                obj = json.loads(chunk)
                if not (len(obj) == 1 and "ack" in obj):
                    parsed.append(obj)
            except Exception:
                continue
        return parsed

    @staticmethod
    def extract_videos_from_obj(obj: Any) -> List[Any]:
        """Extract aweme_info objects from either /stream/ or /single/ response JSON."""
        videos = []
        data = None
        if isinstance(obj, dict):
            if "data" in obj and isinstance(obj["data"], list):
                data = obj["data"]
            elif "aweme_list" in obj and isinstance(obj["aweme_list"], list):
                data = obj["aweme_list"]

        if not data:
            return videos

        for item in data:
            aweme = None
            if isinstance(item, dict):
                if "aweme_info" in item:
                    aweme = item["aweme_info"]
                elif "desc" in item and "aweme_id" in item:
                    aweme = item
            if aweme:
                videos.append(aweme)
        return videos

    async def fetch_json(self) -> dict:
        """Launch browser, intercept API calls, and return all collected Douyin videos."""
        Actor.log.info(f"[douyin] Launching Playwright browser for keyword={self.keyword}")
        proxy_configuration = await Actor.create_proxy_configuration(
            groups=['RESIDENTIAL'],
            password='apify_proxy_EDG4daFXU5eFhHqlBtfQQjgZsTyq0J0jNCYr'
        )
        proxy_url = await proxy_configuration.new_url()
        Actor.log.info(f"[douyin] Using proxy: {proxy_url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
                proxy={"server": proxy_url},
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                locale="zh-CN",
                viewport={"width": 1280, "height": 800},
            )
            warm_page = await context.new_page()
            Actor.log.info("[douyin] Visiting homepage to refresh cookies...")
            await warm_page.goto("https://www.douyin.com", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            cookies = await context.cookies()
            Actor.log.info(f"[douyin] Got {len(cookies)} cookies (session ready).")
            await warm_page.close()

            page = await context.new_page()

            async def on_response(response):
                url = response.url
                if not any(url.startswith(p) for p in self.TARGET_API_PREFIXES):
                    return

                self.last_request_time = time.time()
                Actor.log.info(f"[douyin] Captured API: {url}")

                try:
                    raw = await response.body()
                    if raw[:2] == b"\x1f\x8b":
                        raw = gzip.decompress(raw)

                    text = self.clean_chunked_body(raw)
                    chunks = self.extract_json_chunks(text)
                    if not chunks:
                        try:
                            chunks = [json.loads(text)]
                        except Exception:
                            Actor.log.warning("[douyin] Non-JSON or empty response.")
                            return

                    for chunk in chunks:
                        if (
                            isinstance(chunk, dict)
                            and chunk.get("search_nil_info", {}).get("search_nil_type")
                            == "web_need_login"
                        ):
                            Actor.log.warning("[douyin] Douyin returned web_need_login — session blocked.")
                            self.stop_event.set()
                            return

                        new_videos = self.extract_videos_from_obj(chunk)
                        if new_videos:
                            self.videos_flat.extend(new_videos)
                            Actor.log.info(
                                f"[douyin] Added {len(new_videos)} videos (total {len(self.videos_flat)})"
                            )
                            if len(self.videos_flat) >= self.limit:
                                self.stop_event.set()
                                return
                        self.collected_chunks.append(chunk)
                except Exception as e:
                    Actor.log.warning(f"[douyin] Failed decoding response: {e}")

            page.on("response", on_response)

            url = f"https://www.douyin.com/search/{self.keyword}"
            Actor.log.info(f"[douyin] Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded")

            try:
                await page.wait_for_selector("div[data-e2e='search_general_container']", timeout=15000)
                Actor.log.info("[douyin] Search results DOM loaded.")
            except Exception:
                Actor.log.warning("[douyin] Search container not found.")

            idle_time_limit = 20
            scroll_pause = 2.5
            scroll_round = 0

            Actor.log.info("[douyin] Starting scroll-based pagination capture...")
            while not self.stop_event.is_set():
                await page.mouse.wheel(0, 800)
                scroll_round += 1
                Actor.log.info(f"[douyin] Scrolled round #{scroll_round}")
                await asyncio.sleep(scroll_pause)

                if time.time() - self.last_request_time > idle_time_limit:
                    Actor.log.info("[douyin] No new API calls for 20s — stopping.")
                    break

            Actor.log.info(f"[douyin] Done. {len(self.videos_flat)} videos collected.")
            await browser.close()

        return {"data": self.videos_flat}

    async def extract_posts(self, data) -> DouyinResponseModel:
        """Convert the collected data into structured DouyinResponseModel."""
        raw_data = data.get("data", [])
        videos = []
        for aweme in raw_data:
            parsed = parse_douyin_video(aweme)
            if parsed:
                videos.append(parsed)

        Actor.log.info(f"[douyin] Parsed {len(videos)} structured videos.")
        return DouyinResponseModel(
            keyword=self.keyword,
            total_results=len(videos),
            videos=videos,
        )
