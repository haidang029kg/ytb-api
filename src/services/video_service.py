from datetime import datetime
from typing import Annotated, Optional

from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.logger import logger
from src.db import get_async_session
from src.models.videos import Video
from src.schemas.videos import VideoCreateReq, VideoUpdateReq


async def create_video(
	video_data: VideoCreateReq,
	user_id: int,
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Video:
	"""Create a new video entry in the database."""
	video = Video(
		title=video_data.title,
		description=video_data.description,
		thumbnail_url=video_data.thumbnail_url,
		duration=video_data.duration,
		user_id=user_id,
	)

	db_session.add(video)
	await db_session.commit()
	await db_session.refresh(video)

	logger.info(f"Created video {video.id} for user {user_id}")
	return video


async def get_video(
	video_id: int,
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Optional[Video]:
	"""Get a video by ID."""
	result = await db_session.exec(select(Video).where(Video.id == video_id))
	video = result.first()
	return video


async def get_video_by_user(
	video_id: int,
	user_id: int,
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Optional[Video]:
	"""Get a video by ID and user ID (ownership check)."""
	result = await db_session.exec(
		select(Video).where(Video.id == video_id, Video.user_id == user_id)
	)
	video = result.first()
	return video


async def get_videos_by_user(
	user_id: int,
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
	skip: int = 0,
	limit: int = 10,
) -> tuple[list[Video], int]:
	"""Get all videos for a user with pagination."""
	# Get total count
	count_result = await db_session.exec(select(Video).where(Video.user_id == user_id))
	total = len(count_result.all())

	# Get paginated results
	result = await db_session.exec(
		select(Video).where(Video.user_id == user_id).offset(skip).limit(limit)
	)
	videos = result.all()

	return videos, total


async def get_all_videos(
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
	skip: int = 0,
	limit: int = 10,
	published_only: bool = True,
) -> tuple[list[Video], int]:
	"""Get all videos with pagination."""
	# Build query
	query = select(Video)
	if published_only:
		query = query.where(Video.is_published == True)

	# Get total count
	count_result = await db_session.exec(query)
	total = len(count_result.all())

	# Get paginated results
	result = await db_session.exec(query.offset(skip).limit(limit))
	videos = result.all()

	return videos, total


async def update_video(
	video_id: int,
	user_id: int,
	video_data: VideoUpdateReq,
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Optional[Video]:
	"""Update a video (only by owner)."""
	# Get video and check ownership
	video = await get_video_by_user(video_id, user_id, db_session)
	if not video:
		return None

	# Update fields if provided
	if video_data.title is not None:
		video.title = video_data.title
	if video_data.description is not None:
		video.description = video_data.description
	if video_data.thumbnail_url is not None:
		video.thumbnail_url = video_data.thumbnail_url
	if video_data.duration is not None:
		video.duration = video_data.duration
	if video_data.is_published is not None:
		video.is_published = video_data.is_published

	video.updated_at = datetime.now()

	db_session.add(video)
	await db_session.commit()
	await db_session.refresh(video)

	logger.info(f"Updated video {video_id} by user {user_id}")
	return video


async def update_video_url(
	video_id: int,
	user_id: int,
	video_url: str,
	video_key: str,
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Optional[Video]:
	"""Update video URL and key after upload (only by owner)."""
	video = await get_video_by_user(video_id, user_id, db_session)
	if not video:
		return None

	video.video_url = video_url
	video.video_key = video_key
	video.updated_at = datetime.now()

	db_session.add(video)
	await db_session.commit()
	await db_session.refresh(video)

	logger.info(f"Updated video URL for video {video_id}")
	return video


async def delete_video(
	video_id: int,
	user_id: int,
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> bool:
	"""Delete a video (only by owner)."""
	video = await get_video_by_user(video_id, user_id, db_session)
	if not video:
		return False

	await db_session.delete(video)
	await db_session.commit()

	logger.info(f"Deleted video {video_id} by user {user_id}")
	return True


async def increment_views(
	video_id: int,
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Optional[Video]:
	"""Increment video view count."""
	video = await get_video(video_id, db_session)
	if not video:
		return None

	video.views += 1
	db_session.add(video)
	await db_session.commit()
	await db_session.refresh(video)

	return video
