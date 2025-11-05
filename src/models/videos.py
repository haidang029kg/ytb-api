from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Video(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	title: str = Field(
		max_length=255,
		description="Video title",
	)
	description: Optional[str] = Field(
		default=None,
		description="Video description",
	)
	thumbnail_url: Optional[str] = Field(
		default=None,
		description="Video thumbnail URL",
	)
	video_url: Optional[str] = Field(
		default=None,
		description="Video file URL (S3 or CDN)",
	)
	video_key: Optional[str] = Field(
		default=None,
		description="S3 object key for the video file",
	)
	duration: Optional[int] = Field(
		default=None,
		description="Video duration in seconds",
	)
	views: int = Field(
		default=0,
		description="Number of views",
	)
	likes: int = Field(
		default=0,
		description="Number of likes",
	)
	dislikes: int = Field(
		default=0,
		description="Number of dislikes",
	)
	user_id: int = Field(
		foreign_key="userindb.id",
		description="Owner user ID",
		index=True,
	)
	is_published: bool = Field(
		default=False,
		description="Whether the video is published",
	)
	created_at: datetime = Field(default_factory=datetime.now)
	updated_at: Optional[datetime] = Field(default=None)
