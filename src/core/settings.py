from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	# general
	ROOT_DIR: Path = Field(default=Path.cwd(), description="Project root directory")

	# logging
	LOG_DIR: Path = Field(
		default_factory=lambda: Path.cwd() / "logs", description="Directory for log files"
	)
	LOG_BACKUP_COUNT: int = Field(default=30, description="Number of log backups to keep")

	# authentication
	SECRET_KEY: str = Field(default="123abc123")
	ALGORITHM: str = Field(default="HS256")
	ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
	ACCESS_TOKEN_MAX_LIFETIME_DAYS: int = Field(default=45)
	REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
	ACCESS_TOKEN_MAX_LIFE_TIME_DAYS: int = Field(default=7)

	# database
	DB_URL: str = Field(default="sqlite:///db.sqlite")
	DB_URL_ASYNC: str = Field(default="sqlite+aiosqlite:///db.sqlite")

	# AWS S3
	AWS_ACCESS_KEY_ID: str = Field(default="")
	AWS_SECRET_ACCESS_KEY: str = Field(default="")
	AWS_REGION: str = Field(default="us-east-1")
	S3_BUCKET_NAME: str = Field(default="")
	S3_PRESIGNED_URL_EXPIRATION: int = Field(
		default=3600, description="Presigned URL expiration time in seconds"
	)

	# Video processing (go-api)
	GO_API_BASE_URL: str = Field(
		default="http://localhost:8080", description="Base URL for go-api video processing service"
	)
	GO_API_TIMEOUT: int = Field(default=30, description="Timeout for go-api requests in seconds")
	VIDEO_PROCESSING_WEBHOOK_SECRET: str = Field(
		default="",
		description="Shared secret for video processing webhooks (optional)",
	)
	VIDEO_PROCESSING_QUALITIES: list[str] = Field(
		default=["360p", "480p", "720p", "1080p"], description="Default video quality levels"
	)

	class Config:
		# load defaults from a .env file in project root, if present
		env_file = ".env"
		case_sensitive = True


# create a single, ready-to-use settings instance
settings = Settings()
