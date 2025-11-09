from datetime import datetime
from typing import Optional
from .models import VideoModel, AuthorModel, HashtagModel, MusicModel


def safe_get(obj, *keys, default=None):
    """Utility for nested dict lookups."""
    for k in keys:
        if isinstance(obj, dict):
            obj = obj.get(k, default)
        else:
            return default
    return obj


def calc_engagement_rate(likes, comments, shares, views) -> Optional[float]:
    """Compute engagement rate safely."""
    try:
        if views <= 0:
            engagement_rate = round((likes + comments + shares) / (likes + 1), 4)
        else:
            engagement_rate = round((likes + comments + shares) / views, 4)
        return engagement_rate
    except ZeroDivisionError:
        return None


def get_aspect_ratio(width: int, height: int) -> Optional[str]:
    if not width or not height:
        return None
    ratio = round(height / width, 2)
    if abs(ratio - 1.78) < 0.1:
        return "16:9"
    elif abs(ratio - 1.0) < 0.1:
        return "1:1"
    elif ratio > 1.3:
        return "9:16"
    return f"{width}:{height}"


def parse_douyin_video(aweme: dict) -> Optional[VideoModel]:
    """Parse a single Douyin aweme_info object into VideoModel."""
    if not aweme:
        return None

    author = aweme.get("author", {})
    stats = aweme.get("statistics", {})
    video = aweme.get("video", {})
    music = aweme.get("music", {})
    cover = safe_get(video, "cover", "url_list", 0)
    width = video.get("width")
    height = video.get("height")

    likes = stats.get("digg_count", 0)
    comments = stats.get("comment_count", 0)
    shares = stats.get("share_count", 0)
    views = stats.get("play_count", 0)

    hashtags = [
    HashtagModel(
        hashtag_id=h.get("hashtag_id"),
        hashtag_name=h.get("hashtag_name"),
        is_commerce=h.get("is_commerce", False),
    )
    for h in (aweme.get("text_extra") or [])
    if isinstance(h, dict) and h.get("hashtag_name")
]


    author_model = AuthorModel(
        author_id=author.get("uid", ""),
        author_name=author.get("nickname"),
        author_followers=author.get("follower_count", 0),
        author_avatar=safe_get(author, "avatar_thumb", "url_list", 0),
        author_verified=bool(author.get("custom_verify")),
    )

    music_model = MusicModel(
        music_id=music.get("id_str"),
        music_title=music.get("title"),
        music_author=music.get("author"),
        music_url=safe_get(music, "play_url", "uri"),
        duration=music.get("duration"),
        cover_image=safe_get(music, "cover_medium", "url_list", 0),
    )

    views = stats.get("play_count", 0)
    likes = stats.get("digg_count", 0)
    comments = stats.get("comment_count", 0)
    shares = stats.get("share_count", 0)
    return VideoModel(
        video_id=aweme.get("aweme_id"),
        video_url=safe_get(aweme, "share_info", "share_url"),
        title=aweme.get("desc"),
        thumbnail=cover,
        duration=music.get("duration"),
        publish_time=datetime.fromtimestamp(aweme.get("create_time", 0)),
        likes=likes,
        comments=comments,
        shares=shares,
        views=views,
        favorites=stats.get("collect_count", 0),
        engagement_rate=calc_engagement_rate(likes, comments, shares, views),
        author=author_model,
        hashtags=hashtags,
        music=music_model,
        aspect_ratio=get_aspect_ratio(width, height),
        video_quality="HD" if (width and width >= 720) else "SD",
    )
