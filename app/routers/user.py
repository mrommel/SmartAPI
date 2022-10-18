"""user end-points module"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter()


@router.get('/me', response_model=schemas.UserResponse)
def get_me(db: Session = Depends(get_db), user_id: str = Depends(oauth2.require_user)):
	"""
		endpoint to return the current users data
	"""
	user = db.query(models.User).filter(models.User.id == user_id).first()
	return user
