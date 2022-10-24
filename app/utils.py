"""utils module"""
import time
import uuid

from passlib.context import CryptContext
from sqlalchemy import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
	"""
		hash a password

		:param password: password to hash
		:return: hashed password
	"""
	return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
	"""
		check / verify if a password is valid against a hash

		:param password: password
		:param hashed_password: hashed password
		:return: True if password is valid
	"""
	return pwd_context.verify(password, hashed_password)


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


class CheckTaskState:

	def __init__(self):
		self.urls = [
			'http://www.google.de',
			'http://www.amazon.de',
			'http://www.realtek.de',
			'http://www.avm.de'
		]
		self.current_index = len(self.urls)

	def _check_url(self, url: str):
		print(f'check url: {url}')
		time.sleep(5)

	def check_background_work(self):
		self.current_index = 0
		for url in self.urls:
			self._check_url(url)
			self.current_index += 1

	def get_state(self):
		status = 'ready'

		if self.current_index < len(self.urls):
			status = 'running'

		return {'status': status}


check_state = CheckTaskState()
