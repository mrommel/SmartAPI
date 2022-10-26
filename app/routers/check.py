from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND

from app.utils import check_state
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
	return check_state.get_state()


@router.get("/checks", response_model=schemas.CheckResponse)
def checks(db: Session = Depends(get_db), user_id: str = Depends(oauth2.require_user)):
	videos = db.query(models.Video).filter(models.Video.action == 'Pending').all()

	response_videos = []

	for video in videos:
		response_video = VideoResponse(video_id=video.video_id, title=video.title, duration=video.duration)
		response_videos.append(response_video)

	response_schema = schemas.CheckResponse()
	response_schema.videos = response_videos
	return response_schema


@router.post('/ignore')
def ignore_video(payload: schemas.ExistingVideoSchema = Depends(schemas.ExistingVideoSchema), db: Session = Depends(get_db)):
	"""
		end-point to ignore an existing video

		:return: Nothing
	"""
	# Check if user already exist
	existing_video = db.query(models.Video).filter(models.Video.video_id == payload.video_id).first()
	if existing_video is None:
		raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f'Video with id {payload.video_id} does not exist')

	existing_video.action = ActionChoices.IGNORE.value
	db.add(existing_video)
	db.commit()

	return {'result': 'success'}
