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
	video_url: Optional[str]
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
