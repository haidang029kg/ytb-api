from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Column, Field, SQLModel
from sqlalchemy import JSON


class VideoProcessingStatus(str, Enum):
	"""Video processing status enum."""

	PENDING = "pending"  # Raw video uploaded, waiting for processing
	PROCESSING = "processing"  # Video is being converted to HLS
	COMPLETED = "completed"  # Processing completed successfully
	FAILED = "failed"  # Processing failed


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

	# Raw video fields
	raw_video_url: Optional[str] = Field(
		default=None,
		description="Raw video URL (original upload from S3)",
	)
	raw_video_key: Optional[str] = Field(
		default=None,
		description="S3 object key for raw video file",
	)

	# Processed video fields
	video_url: Optional[str] = Field(
		default=None,
		description="Processed video URL (HLS master playlist)",
	)
	video_key: Optional[str] = Field(
		default=None,
		description="S3 object key for processed video (deprecated, kept for compatibility)",
	)
	processed_video_url: Optional[str] = Field(
		default=None,
		description="HLS master playlist URL (.m3u8)",
	)

	# Processing status
	processing_status: str = Field(
		default=VideoProcessingStatus.PENDING.value,
		description="Video processing status",
	)
	processing_error: Optional[str] = Field(
		default=None,
		description="Error message if processing failed",
	)

	# Available qualities (JSON array of quality levels)
	available_qualities: Optional[dict] = Field(
		default=None,
		sa_column=Column(JSON),
		description="Available video qualities (e.g., {'360p': 'url', '720p': 'url', '1080p': 'url'})",
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
