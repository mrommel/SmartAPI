"""schema module"""
import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr, constr

from app.models import RoleChoices, GenderChoices


class UserBaseSchema(BaseModel):
	"""
		user schema
	"""
	name: str
	email: EmailStr
	photo: str

	class Config:
		"""
			user schema config
		"""
		orm_mode = True


class CreateUserSchema(UserBaseSchema):
	"""
		schema to create a new user
	"""
	password: constr(min_length=8)
	passwordConfirm: str
	role: str = RoleChoices.USER.value
	gender: str = GenderChoices.MALE.value
	verified: bool = False


class LoginUserSchema(BaseModel):
	"""
		schema to log in a user
	"""
	username: EmailStr
	password: constr(min_length=8)


class UserResponse(UserBaseSchema):
	"""
		schema with user information
	"""
	id: uuid.UUID
	created_at: datetime
	updated_at: datetime


class VideoResponse(BaseModel):
	"""
		video check schema
	"""
	video_id: str
	title: str
	duration: int


class CheckResponse(BaseModel):
	"""
		check schema
	"""
	videos: List[VideoResponse] = []

	class Config:
		arbitrary_types_allowed = True


class ExistingVideoSchema(BaseModel):
	"""
		schema for existing video
	"""
	video_id: str
