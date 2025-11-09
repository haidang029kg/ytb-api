from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VideoCreateReq(BaseModel):
    title: str = Field(max_length=255, description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    duration: Optional[int] = Field(None, description="Video duration in seconds")


class VideoUpdateReq(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    duration: Optional[int] = Field(None, description="Video duration in seconds")
    is_published: Optional[bool] = Field(None, description="Publish status")


class VideoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    raw_video_url: Optional[str]
    video_url: Optional[str]
    processed_video_url: Optional[str]
    processing_status: str
    processing_error: Optional[str]
    available_qualities: Optional[dict]
    duration: Optional[int]
    views: int
    likes: int
    dislikes: int
    user_id: int
    is_published: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    videos: list[VideoResponse]
    total: int
    page: int
    page_size: int


class PresignedUrlResponse(BaseModel):
    upload_url: str
    video_key: str
    expires_in: int


# Schemas for video processing


class VideoProcessingRequest(BaseModel):
    """Request to go-api to process video."""

    video_id: int
    raw_video_url: str
    callback_url: str
    qualities: list[str] = Field(
        default=["360p", "480p", "720p", "1080p"], description="Desired output qualities"
    )


class VideoProcessingWebhookReq(BaseModel):
    """Webhook payload from go-api when processing is complete."""

    video_id: int
    status: str  # "completed" or "failed"
    processed_video_url: Optional[str] = Field(None, description="HLS master playlist URL")
    available_qualities: Optional[dict] = Field(
        None, description="Map of quality to URL (e.g., {'360p': 'url', '720p': 'url'})"
    )
    error: Optional[str] = Field(None, description="Error message if failed")
    duration: Optional[int] = Field(None, description="Video duration in seconds")
