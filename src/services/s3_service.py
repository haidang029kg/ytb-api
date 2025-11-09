import uuid
from typing import Optional

import aioboto3
from botocore.exceptions import ClientError

from src.core.logger import logger
from src.core.settings import settings


def _is_s3_configured() -> bool:
    """Check if S3 is properly configured."""
    return bool(
        settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.S3_BUCKET_NAME
    )


async def generate_presigned_upload_url(
    file_extension: str = "mp4",
    content_type: str = "video/mp4",
    folder: str = "videos",
) -> Optional[dict[str, str]]:
    """
    Generate a presigned URL for uploading a video to S3.

    Args:
            file_extension: File extension (default: mp4)
            content_type: Content type (default: video/mp4)
            folder: S3 folder path (default: videos)

    Returns:
            Dict with upload_url and video_key, or None if S3 is not configured
    """
    if not _is_s3_configured():
        logger.warning("S3 is not configured. Cannot generate presigned URL.")
        return None

    # Generate unique video key
    video_key = f"{folder}/{uuid.uuid4()}.{file_extension}"

    try:
        session = aioboto3.Session()
        async with session.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        ) as s3_client:
            presigned_url = await s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.S3_BUCKET_NAME,
                    "Key": video_key,
                    "ContentType": content_type,
                },
                ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRATION,
            )

            return {"upload_url": presigned_url, "video_key": video_key}

    except ClientError as e:
        logger.error(f"Error generating presigned URL: {e}")
        return None


async def generate_presigned_download_url(
    video_key: str, expires_in: Optional[int] = None
) -> Optional[str]:
    """
    Generate a presigned URL for downloading/viewing a video from S3.

    Args:
            video_key: S3 object key
            expires_in: URL expiration time in seconds (default: from settings)

    Returns:
            Presigned URL string or None if error
    """
    if not _is_s3_configured():
        logger.warning("S3 is not configured. Cannot generate presigned URL.")
        return None

    if expires_in is None:
        expires_in = settings.S3_PRESIGNED_URL_EXPIRATION

    try:
        session = aioboto3.Session()
        async with session.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        ) as s3_client:
            presigned_url = await s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET_NAME, "Key": video_key},
                ExpiresIn=expires_in,
            )
            return presigned_url

    except ClientError as e:
        logger.error(f"Error generating presigned download URL: {e}")
        return None


async def delete_video(video_key: str) -> bool:
    """
    Delete a video from S3.

    Args:
            video_key: S3 object key

    Returns:
            True if successful, False otherwise
    """
    if not _is_s3_configured():
        logger.warning("S3 is not configured. Cannot delete video.")
        return False

    try:
        session = aioboto3.Session()
        async with session.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        ) as s3_client:
            await s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=video_key)
            logger.info(f"Successfully deleted video: {video_key}")
            return True

    except ClientError as e:
        logger.error(f"Error deleting video {video_key}: {e}")
        return False
