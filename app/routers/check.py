"""auth module"""
import os

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND

from app.utils import check_state, download_state
from .. import oauth2, models, schemas
from ..database import get_db
from ..models import ActionChoices
from ..schemas import VideoResponse

router = APIRouter()


@router.post('/start', status_code=HTTP_201_CREATED)
async def start_check(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
	"""
		endpoint to start check
	"""
	background_tasks.add_task(check_state.check_background_work, db=db)
	return {"message": "Job Created, check status after some time!"}


@router.get("/status")
def status():
	"""
		get the status of the background service to download videos

		:return: status of the background service to download videos
	"""
	return check_state.get_state()


@router.get("/checks", response_model=schemas.CheckResponse)
def checks(db: Session = Depends(get_db)):
	"""
		returns the list of videos to be checked (aka status pending)

		:param db: database - injected
		:return: list of videos
	"""
	videos = db.query(models.Video).filter(models.Video.action == 'Pending').all()

	response_videos = []

	for video in videos:
		response_video = VideoResponse(
			video_id=video.video_id,
			platform=video.platform.value,
			title=video.title,
			duration=video.duration
		)
		response_videos.append(response_video)

	response_schema = schemas.CheckResponse()
	response_schema.videos = response_videos
	return response_schema


@router.post('/ignore')
def ignore_video(
	video_id: str = Body(embed=True, description="video id of dailymotion or youtube video"),
	db: Session = Depends(get_db)
):
	"""
		end-point to ignore an existing video

		:param video_id: identifier of a dailymotion or youtube video
		:param db: database - injected
		:return: Nothing
	"""
	# Check if user already exist
	existing_video = db.query(models.Video).filter(models.Video.video_id == video_id).first()
	if existing_video is None:
		raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f'Video with id {video_id} does not exist')

	existing_video.action = ActionChoices.IGNORE.value
	db.add(existing_video)
	db.commit()

	return {'result': 'success'}


@router.post('/download')
def download_video(
	background_tasks: BackgroundTasks,
	video_id: str = Body(embed=True, description="video id of dailymotion or youtube video"),
	platform: str = Body(embed=True, description="platform: dailymotion or youtube video"),
	db: Session = Depends(get_db)
):
	"""
		end-point to ignore an existing video

		:param background_tasks:
		:param video_id: identifier of a dailymotion or youtube video
		:param platform: platform of the video
		:param db: database - injected
		:return: Nothing
	"""
	# Check if user already exist
	existing_video = db.query(models.Video).filter(models.Video.video_id == video_id).first()
	if existing_video is None:
		raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f'Video with id {video_id} does not exist')

	existing_video.action = ActionChoices.DOWNLOADING.value
	db.add(existing_video)
	db.commit()

	background_tasks.add_task(download_state.download_background_work, video_id, platform, db=db)

	return {'result': 'success'}
