from fastapi import APIRouter

from .videos_api import video_routes

studio_routes = APIRouter(prefix="/studio")


@studio_routes.get("/info")
async def get_studio_info():
	pass


# Include video routes as a sub-router
studio_routes.include_router(video_routes)
