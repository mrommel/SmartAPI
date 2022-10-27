"""auth end-points module"""
from datetime import timedelta

from fastapi import APIRouter, Request, Response, status, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app import oauth2
from app.oauth2 import AuthJWT
from .. import schemas, models, utils
from ..config import settings
from ..database import get_db
from ..models import RoleChoices, GenderChoices

router = APIRouter()
ACCESS_TOKEN_EXPIRES_IN = settings.ACCESS_TOKEN_EXPIRES_IN
REFRESH_TOKEN_EXPIRES_IN = settings.REFRESH_TOKEN_EXPIRES_IN


# Register a new user
@router.post('/signup', status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
async def create_user(payload: schemas.CreateUserSchema, db: Session = Depends(get_db)):
	"""
		end-point to create a new user

		:return: new user if successful
	"""
	# Check if user already exist
	user = db.query(models.User).filter(
		models.User.email == EmailStr(payload.email.lower())).first()
	if user:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Account already exist')
	# Compare password and passwordConfirm
	if payload.password != payload.passwordConfirm:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Passwords do not match')
	#  Hash the password
	payload.password = utils.hash_password(payload.password)
	del payload.passwordConfirm
	payload.role = RoleChoices.USER.value
	payload.gender = GenderChoices.MALE.value
	payload.verified = True
	payload.email = EmailStr(payload.email.lower())
	new_user = models.User(**payload.dict())
	db.add(new_user)
	db.commit()
	db.refresh(new_user)
	return new_user


# Login user
@router.post('/login')
def login(payload: schemas.LoginUserSchema, response: Response, db: Session = Depends(get_db),
          authorize: AuthJWT = Depends()):
	"""
		end-point to log in a user

		:param payload: user data
		:param response: response object
		:param db: database session (is automatically generated)
		:param authorize: security context
		:return: status and the access token
	"""
	# Check if the user exist
	user = db.query(models.User).filter(
		models.User.email == EmailStr(payload.username.lower())).first()
	if not user:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
		                    detail='Incorrect Email or Password')

	# Check if user verified his email
	if not user.verified:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
		                    detail='Please verify your email address')

	# Check if the password is valid
	if not utils.verify_password(payload.password, user.password):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
		                    detail='Incorrect Email or Password')

	# Create access token
	access_token_value = authorize.create_access_token(
		subject=str(user.id), expires_time=timedelta(minutes=ACCESS_TOKEN_EXPIRES_IN))

	# Create refresh token
	refresh_token_value = authorize.create_refresh_token(
		subject=str(user.id), expires_time=timedelta(minutes=REFRESH_TOKEN_EXPIRES_IN))

	# Store refresh and access tokens in cookie
	response.set_cookie('access_token', access_token_value, ACCESS_TOKEN_EXPIRES_IN * 60,
	                    ACCESS_TOKEN_EXPIRES_IN * 60, '/', None, False, True, 'lax')
	response.set_cookie('refresh_token', refresh_token_value,
	                    REFRESH_TOKEN_EXPIRES_IN * 60, REFRESH_TOKEN_EXPIRES_IN * 60, '/', None, False, True, 'lax')
	response.set_cookie('logged_in', 'True', ACCESS_TOKEN_EXPIRES_IN * 60,
	                    ACCESS_TOKEN_EXPIRES_IN * 60, '/', None, False, False, 'lax')

	# Send both access
	return {'status': 'success', 'access_token': access_token_value}


# Refresh access token
@router.get('/refresh')
def refresh_token(response: Response, request: Request, authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
	"""

		:param authorize:
		:param response:
		:param request:
		:param db:
		:return:
	"""
	try:
		authorize.jwt_refresh_token_required()

		request.scope = 'abc'

		user_id = authorize.get_jwt_subject()
		if not user_id:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
			                    detail='Could not refresh access token')
		user = db.query(models.User).filter(models.User.id == user_id).first()
		if not user:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
			                    detail='The user belonging to this token no logger exist')
		access_token = authorize.create_access_token(
			subject=str(user.id), expires_time=timedelta(minutes=ACCESS_TOKEN_EXPIRES_IN))
	except Exception as e:
		error = e.__class__.__name__
		if error == 'MissingTokenError':
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please provide refresh token') from e

		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error) from e

	response.set_cookie('access_token', access_token, ACCESS_TOKEN_EXPIRES_IN * 60,
	                    ACCESS_TOKEN_EXPIRES_IN * 60, '/', None, False, True, 'lax')
	response.set_cookie('logged_in', 'True', ACCESS_TOKEN_EXPIRES_IN * 60,
	                    ACCESS_TOKEN_EXPIRES_IN * 60, '/', None, False, False, 'lax')
	return {'access_token': access_token}


# Logout user
@router.get('/logout', status_code=status.HTTP_200_OK)
def logout(response: Response, authorize: AuthJWT = Depends(), user_id: str = Depends(oauth2.require_user)):
	"""
		end-point to log the current user out

		:param response: context
		:param authorize: security context
		:param user_id: username to be logged out (retrieved from context)
	"""
	authorize.unset_jwt_cookies()
	response.set_cookie('logged_in', '', -1)
	_ = '' + user_id  # to prevent warning

	return {'status': 'success'}
