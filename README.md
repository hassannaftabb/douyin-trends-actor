# Douyin Trending Videos & Hashtags Scraper

This Apify Actor scrapes **trending videos, hashtags, and engagement data** from [Douyin (抖音)](https://www.douyin.com), China’s most popular short-video platform.
It collects **structured, analysis-ready UGC (User-Generated Content)** to help identify emerging lifestyle, entertainment, and social media trends.

---

## Features

- Collects **real-time Douyin trending hashtags and videos** from the Douyin Hot and Search APIs.

- Automatically paginates and aggregates multiple result pages.

- Extracts detailed **video-level metadata**, including:

  - Video ID, title, description, duration, and publish time
  - Author details (ID, nickname, verification, followers, avatar)
  - Engagement metrics (likes, comments, shares, favorites)
  - Associated hashtags and background music info

- Calculates **derived analytics**, such as engagement rates.

- Returns fully validated data using **Pydantic models** for reliability.

- Ready-to-analyze JSON output stored directly in your **Apify dataset**.

---

## Tech Stack

| Component                       | Purpose                                    |
| ------------------------------- | ------------------------------------------ |
| **Python 3.13 (Apify runtime)** | Base environment                           |
| **aiohttp**                     | Asynchronous API requests                  |
| **Playwright**                  | Fetches Douyin hot search data dynamically |
| **Pydantic v2**                 | Schema validation and structured output    |
| **Tenacity**                    | Automatic retry handling                   |
| **Apify SDK**                   | Actor runtime and dataset management       |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Chromium (for Douyin Hot Trends)

```bash
playwright install --with-deps chromium
```

### 3. Run locally

```bash
apify run
```

### 4. Deploy to Apify Cloud

```bash
apify push
```

Apify will automatically package, build, and deploy your actor with all dependencies.

---

## 🐳 Dockerfile (Prebuilt Chromium)

Your Dockerfile already includes:

```dockerfile
FROM apify/actor-python:3.13
RUN playwright install --with-deps chromium
```

This ensures the actor can access Douyin’s hot trends page using a full Chromium environment.

---

## Input Configuration

You can configure the scraper via the Apify UI or `INPUT.json`:

```json
{
  "max_keywords": 10,
  "max_videos_per_keyword": 10,
  "max_pages": 2,
  "concurrency": 5,
  "request_delay": 1.5
}
```

| Field                    | Description                                      | Default |
| ------------------------ | ------------------------------------------------ | ------- |
| `max_keywords`           | Number of trending topics to scrape              | 10      |
| `max_videos_per_keyword` | Max number of videos per hashtag/topic           | 10      |
| `max_pages`              | Number of paginated results per keyword to fetch | 2       |
| `concurrency`            | Parallel keyword scraping limit                  | 5       |
| `request_delay`          | Delay (in seconds) between page requests         | 1.5     |

---

## Output Schema

Each record in your dataset follows this format:

```json
{
  "video_id": "7552090238508649755",
  "video_url": "https://www.iesdouyin.com/share/video/7552090238508649755",
  "title": "不知道吃什么的时候来看看 #抖音美食创作者 #懒人美食",
  "description": null,
  "thumbnail": null,
  "duration": 37,
  "publish_time": "2025-09-20 13:47:16",
  "video_type": "regular",
  "likes": 857221,
  "comments": 17537,
  "shares": 453052,
  "favorites": 260216,
  "engagement_rate": 0.45,
  "author": {
    "author_id": "1640939144617182",
    "author_name": "栗子日食记",
    "author_followers": 2500000,
    "author_verified": true,
    "author_avatar": "https://p3.douyinpic.com/img/avatar.jpg"
  },
  "hashtags": [
    {
      "hashtag_id": "1582588874644493",
      "hashtag_name": "懒人美食",
      "is_commerce": false
    }
  ],
  "music": {
    "music_id": "7552090206428105487",
    "music_title": "@栗子日食记创作的原声",
    "music_author": "栗子日食记",
    "music_url": "https://sf5-hl-cdn-tos.douyinstatic.com/obj/ies-music/6989446629665360671.mp3",
    "duration": 37
  },
  "aspect_ratio": "16:9",
  "video_quality": "HD",
  "trend_velocity": null,
  "trend_direction": null
}
```

---

## Output Views

After the run, you’ll have multiple dataset views in Apify:

| View                | Description                                            |
| ------------------- | ------------------------------------------------------ |
| `trending_videos`   | Full structured data per video with engagement metrics |
| `trending_hashtags` | Hashtag-level summary with ranks and heat values       |
| `authors`           | Top creators by engagement or follower count           |
| `engagement_stats`  | Aggregated engagement and rate calculations            |

---

## Research & AI Use Cases

Ideal for **data analysts, social researchers, and AI engineers** studying viral content and short-form media dynamics.

**Use cases include:**

- Trend and virality prediction
- Engagement optimization & content analytics
- Creator/influencer performance analysis
- Multimodal AI training (video-text-music datasets)
- Chinese digital culture tracking

---

## Notes

- Some videos may return limited engagement stats (e.g., play count = 0).
- Douyin frequently rotates API signatures — actor refresh logic mitigates that.
- Avoid scraping excessive pages per keyword; rate-limited for stability.
- Always comply with Douyin’s Terms of Service and Apify’s usage policies.

---

## Summary

This actor helps you track **what’s trending right now in China’s short-video ecosystem**, giving you structured, reliable, and ready-to-analyze data from Douyin’s public web endpoints — ideal for market research, AI data gathering, and cultural insights.
