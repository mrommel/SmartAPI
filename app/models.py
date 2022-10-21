"""models module"""
import uuid

from sqlalchemy import Column, String, Boolean, TypeDecorator, CHAR, DateTime, func
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
		"""Receive a literal parameter value to be rendered inline within
		a statement."""

	@property
	def python_type(self):
		"""Return the Python type object expected to be returned
		by instances of this type, if known."""


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
	verified = Column(Boolean, nullable=False, server_default='False')
	role = Column(String, server_default='user', nullable=False)
	created_at = Column(DateTime, default=func.current_timestamp())
	updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
