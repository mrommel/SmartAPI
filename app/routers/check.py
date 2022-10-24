from fastapi import APIRouter
from starlette.background import BackgroundTasks
from starlette.status import HTTP_201_CREATED

from app.utils import check_state

router = APIRouter()


@router.post('/start', status_code=HTTP_201_CREATED)
async def start_check(background_tasks: BackgroundTasks):
	"""
		endpoint to start check
	"""
	background_tasks.add_task(check_state.check_background_work)
	return {"message": "Job Created, check status after some time!"}


@router.get("/status")
def status():
	return check_state.get_state()
