"""schema module"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, constr
from starlette.requests import Request

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
