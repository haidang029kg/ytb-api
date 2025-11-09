"""Service for video processing via go-api."""

import httpx

from src.core.logger import logger
from src.core.settings import settings
from src.schemas.videos import VideoProcessingRequest


async def trigger_video_processing(
    video_id: int,
    raw_video_url: str,
    callback_url: str,
    qualities: list[str] | None = None,
) -> bool:
    """
    Trigger video processing in go-api.

    Args:
            video_id: Video ID
            raw_video_url: URL to the raw video file
            callback_url: Webhook callback URL for processing completion
            qualities: Desired output qualities (defaults to settings)

    Returns:
            True if request was successful, False otherwise
    """
    if not settings.GO_API_BASE_URL:
        logger.warning("GO_API_BASE_URL is not configured. Skipping video processing.")
        return False

    if qualities is None:
        qualities = settings.VIDEO_PROCESSING_QUALITIES

    processing_request = VideoProcessingRequest(
        video_id=video_id,
        raw_video_url=raw_video_url,
        callback_url=callback_url,
        qualities=qualities,
    )

    try:
        async with httpx.AsyncClient(timeout=settings.GO_API_TIMEOUT) as client:
            response = await client.post(
                f"{settings.GO_API_BASE_URL}/api/v1/videos/process",
                json=processing_request.model_dump(),
                headers={"Content-Type": "application/json"},
            )

            if response.status_code in (200, 201, 202):
                logger.info(
                    f"Successfully triggered video processing for video {video_id}. "
                    f"Status: {response.status_code}"
                )
                return True
            else:
                logger.error(
                    f"Failed to trigger video processing for video {video_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return False

    except httpx.TimeoutException:
        logger.error(f"Timeout calling go-api for video {video_id}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error calling go-api for video {video_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error calling go-api for video {video_id}: {e}")
        return False
