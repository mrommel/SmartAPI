"""models module"""
import enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, func, Enum

from .database import Base
from .utils import GUID


class GenderChoices(enum.Enum):
	"""
		enum that contains gender choices
	"""
	MALE = 'Male'
	FEMALE = 'Female'
	OTHER = 'Other'

	@staticmethod
	def fetch_names():
		"""
			get array with enum names

			:return: array with enum names
		"""
		return [c.value for c in GenderChoices]


class User(Base):
	"""
		model of a user (maps to db class)
	"""
	__tablename__ = 'users'
	id = Column(GUID(), primary_key=True, nullable=False, default=uuid.uuid4)
	name = Column(String, nullable=False)
	email = Column(String, unique=True, nullable=False)
	password = Column(String, nullable=False)
	photo = Column(String, nullable=True)
	gender = Column(Enum(GenderChoices, values_callable=lambda x: [str(member.value) for member in GenderChoices]))
	verified = Column(Boolean, nullable=False, server_default='False')
	role = Column(String, server_default='user', nullable=False)

	created_at = Column(DateTime, default=func.current_timestamp())
	updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
