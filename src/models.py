from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
class InputModel(BaseModel):
    max_hashtags: int = Field(default=3, ge=1, le=50, description="How many trending hashtags to fetch")
    max_posts_per_hashtag: int = Field(default=10, ge=1, le=50, description="How many posts to scrape per hashtag")
    max_pages: int = Field(default=3, ge=1, le=10, description="How many pages per hashtag to scrape")
    concurrency: int = Field(default=5, ge=1, le=20, description="Concurrent scraping threads")

class EngagementMetrics(BaseModel):
    total_likes: int = Field(..., description="Total likes across all posts for a hashtag")
    total_comments: int = Field(..., description="Total comments across all posts for a hashtag")
    total_reposts: int = Field(..., description="Total reposts across all posts for a hashtag")
    avg_engagement_rate: float = Field(..., description="Average engagement rate per post")
class AuthorModel(BaseModel):
    author_id: str = Field(..., description="Unique user ID")
    author_name: Optional[str]
    author_followers: Optional[int]
    author_following: Optional[int] = None
    author_verified: Optional[bool] = False
    author_avatar: Optional[str]
    author_signature: Optional[str] = None

class MusicModel(BaseModel):
    music_id: Optional[str]
    music_title: Optional[str]
    music_author: Optional[str]
    music_url: Optional[str] = None
    duration: Optional[int] = None
    cover_image: Optional[str] = None
class HashtagModel(BaseModel):
    hashtag_id: Optional[str]
    hashtag_name: Optional[str]
    is_commerce: Optional[bool] = False

class VideoModel(BaseModel):
    video_id: str = Field(..., description="aweme_id")
    video_url: Optional[str]
    title: Optional[str]
    description: Optional[str] = None
    thumbnail: Optional[str]
    duration: Optional[int]
    publish_time: Optional[datetime]
    video_type: Optional[str] = "regular"

    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    favorites: int = 0
    engagement_rate: Optional[float] = None

    author: Optional[AuthorModel]

    hashtags: List[HashtagModel] = []
    music: Optional[MusicModel] = None
    challenge_name: Optional[str] = None
    challenge_id: Optional[str] = None
    trending_rank: Optional[int] = None

    category: Optional[str] = None
    tags: Optional[List[str]] = None
    effects: Optional[List[str]] = None

    aspect_ratio: Optional[str] = None
    video_quality: Optional[str] = None
    has_transitions: Optional[bool] = None
    has_effects: Optional[bool] = None
    caption_style: Optional[str] = None

    time_since_publish: Optional[float] = None
    trend_velocity: Optional[float] = None
    trend_direction: Optional[str] = None
    peak_time: Optional[datetime] = None

    class Config:
        orm_mode = True
class HashtagAggregateModel(BaseModel):
    hashtag_name: str
    hashtag_heat: Optional[float]
    total_videos: Optional[int]
    total_views: Optional[int]
    total_engagement: Optional[int]
    avg_engagement_rate: Optional[float]
    top_creators: Optional[List[AuthorModel]] = []

class DouyinResponseModel(BaseModel):
    keyword: Optional[str]
    total_results: Optional[int]
    videos: List[VideoModel]
    aggregated_hashtags: Optional[List[HashtagAggregateModel]] = []
class DouyinTrend(BaseModel):
    keyword: str
    rank: int
    heat: Optional[int] = None
    total_videos: int
    engagement_metrics: "EngagementMetrics"
    videos: List["VideoModel"]
    scraped_at: datetime = datetime.now(timezone.utc)