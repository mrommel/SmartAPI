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

	def load_dialect_impl(self, dialect):
		if dialect.name == 'postgresql':
			return dialect.type_descriptor(UUID())
		else:
			return dialect.type_descriptor(CHAR(32))

	def process_bind_param(self, value, dialect):
		if value is None:
			return value
		elif dialect.name == 'postgresql':
			return str(value)
		else:
			if not isinstance(value, uuid.UUID):
				return "%.32x" % uuid.UUID(value).int
			else:
				# hexstring
				return "%.32x" % value.int

	def process_result_value(self, value, dialect):
		if value is None:
			return value
		else:
			if not isinstance(value, uuid.UUID):
				value = uuid.UUID(value)
			return value


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
# created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
# updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
