"""models module"""
import enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, func, Enum, Integer, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

from .database import Base


class GUID(TypeDecorator):
	"""Platform-independent GUID type.
	Uses PostgreSQL's UUID type, otherwise uses
	CHAR(32), storing as stringified hex values.
	"""
	impl = CHAR

	cache_ok = True

	def load_dialect_impl(self, dialect):
		if dialect.name == 'postgresql':
			return dialect.type_descriptor(UUID())

		return dialect.type_descriptor(CHAR(32))

	def process_bind_param(self, value, dialect):
		if value is None:
			return value

		if dialect.name == 'postgresql':
			return str(value)

		if not isinstance(value, uuid.UUID):
			return f'{uuid.UUID(value).int:32x}'

		# hex string
		return f'{value.int:32x}'

	def process_result_value(self, value, dialect):
		if value is None:
			return value

		if not isinstance(value, uuid.UUID):
			value = uuid.UUID(value)

		return value

	def process_literal_param(self, value, dialect):
		"""
			Receive a literal parameter value to be rendered inline within
			a statement.
		"""

	@property
	def python_type(self):
		"""
			Return the Python type object expected to be returned
			by instances of this type, if known.
		"""


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


class RoleChoices(enum.Enum):
	"""
		enum that contains role choices
	"""
	USER = 'User'
	IBD = 'IBD'
	OEM = 'OEM'

	@staticmethod
	def fetch_names():
		"""
			get array with enum names

			:return: array with enum names
		"""
		return [c.value for c in RoleChoices]


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
	gender = Column(Enum(GenderChoices, values_callable=lambda x: [str(member.value) for member in GenderChoices]),
	                server_default='Other')
	verified = Column(Boolean, nullable=False, server_default='False')
	role = Column(Enum(RoleChoices, values_callable=lambda x: [str(member.value) for member in RoleChoices]),
	              server_default='User', nullable=False)

	created_at = Column(DateTime, default=func.current_timestamp())
	updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class ActionChoices(enum.Enum):
	"""
		enum that contains action choices
	"""
	IGNORE = 'Ignore'
	DOWNLOADED = 'Download'
	PENDING = 'Pending'

	@staticmethod
	def fetch_names():
		"""
			get array with enum names

			:return: array with enum names
		"""
		return [c.value for c in ActionChoices]


class PlatformChoices(enum.Enum):
	"""
		enum that contains action choices
	"""
	DAILYMOTION = 'Dailymotion'
	VK = 'VK'
	YOUTUBE = 'Youtube'


class Video(Base):
	"""
		model of a video (maps to db class)
	"""
	__tablename__ = 'videos'
	id = Column(GUID(), primary_key=True, nullable=False, default=uuid.uuid4)
	video_id = Column(String, unique=True, nullable=False)
	title = Column(String, nullable=False)
	duration = Column(Integer, nullable=False)
	action = Column(Enum(ActionChoices, values_callable=lambda x: [str(member.value) for member in ActionChoices]),
	                server_default='Pending')
	platform = Column(
		Enum(PlatformChoices, values_callable=lambda x: [str(member.value) for member in PlatformChoices]),
		server_default='Dailymotion')

	created_at = Column(DateTime, default=func.current_timestamp())
	updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class Captcha(Base):
	"""
		model of a captcha entry
	"""
	__tablename__ = 'captcha'
	id = Column(GUID(), primary_key=True, nullable=False, default=uuid.uuid4)
	code = Column(String, nullable=False)
	token = Column(String, nullable=False)

	created_at = Column(DateTime, default=func.current_timestamp())
	updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
