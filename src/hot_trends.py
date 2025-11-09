import aiohttp

DOUYIN_HOT_API = (
    "https://www.douyin.com/aweme/v1/web/hot/search/list/"
    "?device_platform=webapp&aid=6383&channel=channel_pc_web&detail_list=1"
    "&count=50&pc_client_type=1&version_code=190600&version_name=19.6.0"
    "&cookie_enabled=true&screen_width=1920&screen_height=1080"
    "&browser_language=zh-CN&browser_platform=Win32"
    "&browser_name=Chrome&browser_version=142.0.0.0"
    "&browser_online=true&engine_name=Blink&engine_version=142.0.0.0"
    "&os_name=Windows&os_version=10&device_memory=8&platform=PC"
)

async def fetch_hot_hashtags(limit: int = 10):
    """Fetch trending Douyin hashtags directly from the official hot search API."""
    print("[apify] INFO  Fetching trending hashtags via Douyin hot search API...")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.douyin.com/hot",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(DOUYIN_HOT_API, timeout=30) as resp:
            print(f"[douyin] Status: {resp.status} | Content-Type: {resp.headers.get('Content-Type')}")
            if resp.status != 200:
                print("[WARN] Non-200 response; unable to fetch Douyin hot list.")
                return []
            data = await resp.json(content_type=None)

    data = data.get("data", {})
    trending_list = data.get("trending_list", [])
    word_list = data.get("word_list", [])
    all_items = trending_list + word_list

    if not all_items:
        print("[WARN] No trending items found in Douyin API response.")
        return []

    trends = []
    for i, item in enumerate(all_items[:limit]):
        word = item.get("word") or item.get("challenge_info", {}).get("cha_name") or "No name"
        heat = item.get("hot_value") or item.get("video_count")
        sentence = item.get("sentence") or item.get("challenge_info", {}).get("desc", "")
        trends.append({
            "rank": i + 1,
            "keyword": word,
            "heat": heat,
            "description": sentence,
            "url": f"https://www.douyin.com/search/{word}",
        })

    print(f"[INFO] Extracted {len(trends)} trending hashtags from Douyin API.")
    for t in trends:
        print(f"#{t['rank']}: {t['keyword']} ({t['heat']})")

    return trends
