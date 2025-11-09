DOUYIN_TTWID = "1%7CQ4om2uXmxZzSFPN5Dep4bEXgm-Vx4XBHUEX4rOCnRCg%7C1762630284%7C2c901c54f639f54c1b2d3973d9fe7bee0c3248276edb92535dfc215a33cdc9b4"

DOUYIN_BASE_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-PK,en-US;q=0.9,en-GB;q=0.8,en;q=0.7",
    "priority": "u=1, i",
    "referer": "https://www.douyin.com/search/%E7%BE%8E%E9%A3%9F",
    "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "uifid": "undefined",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    ),
}

def get_douyin_auth():
    """Return headers and cookies for Douyin API access."""
    return {
        "headers": DOUYIN_BASE_HEADERS,
        "cookies": {"ttwid": DOUYIN_TTWID},
    }