"""utils module"""
import time
import uuid
import requests

from passlib.context import CryptContext
from sqlalchemy import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session

from app import models

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


class CheckContent:
	def __init__(self, query: str, min_duration: int):
		self.query = query
		self.min_duration = min_duration

	def url(self) -> str:
		host = 'https://api.dailymotion.com'
		field = 'id,title,duration'
		language = 'de'
		return f'{host}/videos?fields={field}&search={self.query}&limit=50&languages={language}' \
		       f'&longer_than={self.min_duration}&sort=recent'


class VideoItem(object):
	def __init__(self, id: str, title: str, duration: int):
		self.video_id = id
		self.title = title
		self.duration = duration

	def __repr__(self):
		return f'<video id={self.video_id}, title="{self.title}", duration={self.duration}>'


class VideoListItem(object):
	def __init__(self, page: int, limit: int, explicit, total, has_more, list: [VideoItem]):
		self.page = page
		self.limit = limit
		self.explicit = explicit
		self.total = total
		self.has_more = has_more
		self.videos = list

	def __repr__(self):
		return f'<videolist({self.total}) = [{self.videos}]>'


class CheckTaskState:

	def __init__(self):
		self.checks = [
			CheckContent(query='scrubs%20anf%C3%A4nger', min_duration=25),
			CheckContent(query='%22big%20bang%20theory%22', min_duration=20),
			CheckContent(query='%22how%20i%20met%20your%20mother%22', min_duration=15),
			CheckContent(query='tng', min_duration=40),
			CheckContent(query='%22next%20generation%22', min_duration=40),
			CheckContent(query='picard', min_duration=30),
		]
		self.current_index = len(self.checks)

	def _check_url(self, url: str, db: Session):
		response = requests.get(url)
		video_list = VideoListItem(**response.json())

		for video in video_list.videos:
			existing_video = db.query(models.Video).filter(models.Video.video_id == video['id']).first()

			if existing_video:
				continue

			payload = dict()
			payload['video_id'] = video['id']
			payload['title'] = video['title']
			payload['duration'] = video['duration']
			payload['action'] = 'Pending'  # cannot import ActionChoices (circular import)
			new_video = models.Video(**payload)
			db.add(new_video)

		db.commit()

		time.sleep(2)

	def check_background_work(self, db: Session):
		self.current_index = 0
		for check in self.checks:
			self._check_url(check.url(), db)
			self.current_index += 1
		print('checked all {len(self.checks)} items')

	def get_state(self):
		status = 'ready'

		if self.current_index < len(self.urls):
			status = 'running ({self.current_index} / {len(self.urls)})'

		return {'status': status}


check_state = CheckTaskState()
