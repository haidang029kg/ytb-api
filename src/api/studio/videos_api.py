from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.logger import logger
from src.db import get_async_session
from src.models.users import User
from src.schemas.videos import (
	PresignedUrlResponse,
	VideoCreateReq,
	VideoListResponse,
	VideoProcessingWebhookReq,
	VideoResponse,
	VideoUpdateReq,
)
from src.services import video_service
from src.services.authentication import get_authenticated_user
from src.services import s3_service

video_routes = APIRouter(prefix="/videos", tags=["Videos"])


@video_routes.post("", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def create_video(
	video_data: VideoCreateReq,
	user: Annotated[User, Depends(get_authenticated_user)],
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> VideoResponse:
	"""Create a new video entry."""
	video = await video_service.create_video(video_data, user.id, db_session)
	return VideoResponse.model_validate(video)


@video_routes.get("/presigned-upload-url", response_model=PresignedUrlResponse)
async def get_presigned_upload_url(
	user: Annotated[User, Depends(get_authenticated_user)],
	file_extension: str = Query(default="mp4", description="File extension (mp4, mov, etc.)"),
	content_type: str = Query(default="video/mp4", description="MIME type"),
) -> PresignedUrlResponse:
	"""Get a presigned URL for uploading a video to S3."""
	result = await s3_service.generate_presigned_upload_url(
		file_extension=file_extension, content_type=content_type
	)

	if not result:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="S3 service is not configured or unavailable",
		)

	from src.core.settings import settings

	return PresignedUrlResponse(
		upload_url=result["upload_url"],
		video_key=result["video_key"],
		expires_in=settings.S3_PRESIGNED_URL_EXPIRATION,
	)


@video_routes.get("", response_model=VideoListResponse)
async def list_videos(
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
	page: int = Query(default=1, ge=1, description="Page number"),
	page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
) -> VideoListResponse:
	"""List all published videos with pagination. Public endpoint."""
	skip = (page - 1) * page_size
	videos, total = await video_service.get_all_videos(
		db_session, skip=skip, limit=page_size, published_only=True
	)

	return VideoListResponse(
		videos=[VideoResponse.model_validate(v) for v in videos],
		total=total,
		page=page,
		page_size=page_size,
	)


@video_routes.get("/my-videos", response_model=VideoListResponse)
async def list_my_videos(
	user: Annotated[User, Depends(get_authenticated_user)],
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
	page: int = Query(default=1, ge=1, description="Page number"),
	page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
) -> VideoListResponse:
	"""List current user's videos with pagination."""
	skip = (page - 1) * page_size
	videos, total = await video_service.get_videos_by_user(
		user.id, db_session, skip=skip, limit=page_size
	)

	return VideoListResponse(
		videos=[VideoResponse.model_validate(v) for v in videos],
		total=total,
		page=page,
		page_size=page_size,
	)


@video_routes.get("/{video_id}", response_model=VideoResponse)
async def get_video(
	video_id: int,
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> VideoResponse:
	"""Get a video by ID and increment view count."""
	video = await video_service.get_video(video_id, db_session)

	if not video:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
		)

	if not video.is_published:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Video is not published",
		)

	# Increment view count
	await video_service.increment_views(video_id, db_session)

	return VideoResponse.model_validate(video)


@video_routes.patch("/{video_id}", response_model=VideoResponse)
async def update_video(
	video_id: int,
	video_data: VideoUpdateReq,
	user: Annotated[User, Depends(get_authenticated_user)],
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> VideoResponse:
	"""Update a video (only by owner)."""
	video = await video_service.update_video(video_id, user.id, video_data, db_session)

	if not video:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Video not found or you don't have permission to update it",
		)

	return VideoResponse.model_validate(video)


@video_routes.patch("/{video_id}/upload-complete")
async def mark_video_uploaded(
	video_id: int,
	video_key: str = Query(..., description="S3 object key"),
	user: Annotated[User, Depends(get_authenticated_user)] = None,
	db_session: Annotated[AsyncSession, Depends(get_async_session)] = None,
) -> VideoResponse:
	"""
	Mark raw video as uploaded and trigger HLS conversion.

	This endpoint:
	1. Generates presigned URL for the raw video
	2. Saves raw video URL to database
	3. Triggers go-api to convert video to HLS format
	"""
	from src.models.videos import VideoProcessingStatus
	from src.services import video_processing_service

	# Generate the raw video URL
	raw_video_url = await s3_service.generate_presigned_download_url(video_key)

	if not raw_video_url:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="Failed to generate video URL",
		)

	# Update video with raw video URL and set status to PENDING
	video = await video_service.update_raw_video(
		video_id, user.id, raw_video_url, video_key, db_session
	)

	if not video:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Video not found or you don't have permission to update it",
		)

	# Trigger video processing in go-api
	from fastapi import Request

	# Build callback URL for webhook
	# In production, use settings.API_BASE_URL or similar
	callback_url = f"http://localhost:8000/studio/videos/{video_id}/processing-webhook"

	processing_triggered = await video_processing_service.trigger_video_processing(
		video_id=video_id,
		raw_video_url=raw_video_url,
		callback_url=callback_url,
	)

	if processing_triggered:
		# Update status to PROCESSING
		video.processing_status = VideoProcessingStatus.PROCESSING.value
		db_session.add(video)
		await db_session.commit()
		await db_session.refresh(video)
		logger.info(f"Video {video_id} processing triggered successfully")
	else:
		logger.warning(
			f"Failed to trigger video processing for video {video_id}. "
			f"Video saved but will remain in PENDING status."
		)

	return VideoResponse.model_validate(video)


@video_routes.post("/{video_id}/processing-webhook", response_model=VideoResponse)
async def video_processing_webhook(
	video_id: int,
	webhook_data: VideoProcessingWebhookReq,
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> VideoResponse:
	"""
	Webhook endpoint for go-api to notify video processing completion.

	This endpoint is called by go-api when video conversion is complete.
	No authentication required as this is an internal webhook.
	"""
	logger.info(f"Received processing webhook for video {video_id}: status={webhook_data.status}")

	# Validate video_id matches
	if webhook_data.video_id != video_id:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Video ID mismatch between URL and payload",
		)

	# Update video processing status
	video = await video_service.update_processing_status(
		video_id=video_id,
		status=webhook_data.status,
		db_session=db_session,
		processed_video_url=webhook_data.processed_video_url,
		available_qualities=webhook_data.available_qualities,
		error=webhook_data.error,
		duration=webhook_data.duration,
	)

	if not video:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Video {video_id} not found",
		)

	logger.info(
		f"Video {video_id} processing status updated to {webhook_data.status}. "
		f"Processed URL: {webhook_data.processed_video_url}"
	)

	return VideoResponse.model_validate(video)


@video_routes.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
	video_id: int,
	user: Annotated[User, Depends(get_authenticated_user)],
	db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
	"""Delete a video (only by owner)."""
	# Get video first to check for S3 key
	video = await video_service.get_video_by_user(video_id, user.id, db_session)

	if not video:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Video not found or you don't have permission to delete it",
		)

	# Delete from S3 if video_key exists
	if video.video_key:
		await s3_service.delete_video(video.video_key)

	# Delete from database
	success = await video_service.delete_video(video_id, user.id, db_session)

	if not success:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to delete video",
		)
