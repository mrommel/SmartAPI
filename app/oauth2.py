"""oauth2 module"""
import base64
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import models
from .config import settings
from .database import get_db


class Settings(BaseModel):
	"""
		oauth2 settings
	"""
	authjwt_algorithm: str = settings.JWT_ALGORITHM
	authjwt_decode_algorithms: List[str] = [settings.JWT_ALGORITHM]
	authjwt_token_location: set = {'cookies', 'headers'}
	authjwt_access_cookie_key: str = 'access_token'
	authjwt_refresh_cookie_key: str = 'refresh_token'
	authjwt_cookie_csrf_protect: bool = False
	authjwt_public_key: str = base64.b64decode(settings.JWT_PUBLIC_KEY).decode('utf-8')
	authjwt_private_key: str = base64.b64decode(settings.JWT_PRIVATE_KEY).decode('utf-8')


@AuthJWT.load_config
def get_config():
	"""
		get current oauth2 settings

		:return: current oauth2 settings
	"""
	return Settings()


class NotVerified(Exception):
	"""
		oath2 not verified exception
	"""


class UserNotFound(Exception):
	"""
		oath2 user not found exception
	"""


def require_user(db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
	"""
		check if user is in security context

		:param db:
		:param Authorize: security context
		:return: user_id or exception
	"""
	try:
		Authorize.jwt_required()
		user_id = Authorize.get_jwt_subject()
		user = db.query(models.User).filter(models.User.id == user_id).first()

		if not user:
			raise UserNotFound('User no longer exist')

		if not user.verified:
			raise NotVerified('You are not verified')

	except Exception as e:
		error = e.__class__.__name__
		print(error)
		if error == 'MissingTokenError':
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='You are not logged in') from e

		if error == 'UserNotFound':
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User no longer exist') from e

		if error == 'NotVerified':
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Please verify your account') from e

		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token is invalid or has expired') from e

	return user_id
