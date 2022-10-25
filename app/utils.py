"""utils module"""
import os
# -*- coding: utf-8 -*-
import time
import urllib
import uuid
from urllib.parse import urlencode, quote_plus

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from passlib.context import CryptContext
from sqlalchemy import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session

from app import models
from app.config import settings

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

	def dailymotion_url(self) -> str:
		host = 'https://api.dailymotion.com'
		field = 'id,title,duration'
		language = 'de'
		payload = {
			'fields': field,
			'search': self.query,
			'limit': 100,
			'languages': language,
			'longer_than': self.min_duration,
			'sort': 'recent'
		}
		query_str = urlencode(payload, quote_via=quote_plus)
		return f'{host}/videos?{query_str}'


class DailymotionVideoItem(object):
	def __init__(self, id: str, title: str, duration: int):
		self.video_id = id
		self.title = title
		self.duration = duration

	def __repr__(self):
		return f'<video id={self.video_id}, title="{self.title}", duration={self.duration}>'


class DailymotionVideoList(object):
	def __init__(self, page: int, limit: int, explicit, total, has_more, list: [DailymotionVideoItem]):
		self.page = page
		self.limit = limit
		self.explicit = explicit
		self.total = total
		self.has_more = has_more
		self.videos = list

	def __repr__(self):
		return f'<dm videolist({self.total}) = [{self.videos}]>'


class YoutubePageInfo(object):
	def __init__(self, totalResults: int, resultsPerPage: int):
		self.totalResults = totalResults
		self.resultsPerPage = resultsPerPage


class YoutubeVideoId(object):
	def __init__(self, kind: str, videoId: str):
		self.kind = kind
		self.videoId = videoId


class YoutubeSnippet(object):
	def __init__(self, title: str, description: str):
		self.title = title
		self.description = description

	def __repr__(self):
		return f'<yt video snippet({self.title})>'


class YoutubeContentDetails(object):
	def __init__(self, duration: str):
		self.duration = duration

	def __repr__(self):
		return f'<yt video content duration={self.duration}>'


class YoutubeVideoItem(object):
	def __init__(self, kind: str, etag: str, id: YoutubeVideoId, snippet: YoutubeSnippet,
	             contentDetails: YoutubeContentDetails = None):
		self.kind = kind
		self.etag = etag
		self.id = id
		self.snippet = snippet
		self.contentDetails = contentDetails

	def __repr__(self):
		duration = ""
		if self.contentDetails is not None:
			duration = self.contentDetails.duration

		return f'<yt video: title={self.snippet.title}, duration={duration}>'


class YoutubeVideoList(object):
	def __init__(self, kind: str, etag: str, nextPageToken: str = '', regionCode: str = '',
	             pageInfo: YoutubePageInfo = None, items: [YoutubeVideoItem] = []):
		"""
			build youtube video list

			:type nextPageToken: token of next page
		"""
		self.kind = kind
		self.etag = etag
		self.nextPageToken = nextPageToken
		self.regionCode = regionCode
		self.pageInfo = pageInfo
		self.videos = items

	def __repr__(self):
		return f'<yt videolist({len(self.videos)}) = [{self.videos}]>'


def convert_youtube_duration_to_seconds(duration):
	day_time = duration.split('T')
	day_duration = day_time[0].replace('P', '')
	day_list = day_duration.split('D')
	if len(day_list) == 2:
		day = int(day_list[0]) * 60 * 60 * 24
		day_list = day_list[1]
	else:
		day = 0
		day_list = day_list[0]
	hour_list = day_time[1].split('H')
	if len(hour_list) == 2:
		hour = int(hour_list[0]) * 60 * 60
		hour_list = hour_list[1]
	else:
		hour = 0
		hour_list = hour_list[0]
	minute_list = hour_list.split('M')
	if len(minute_list) == 2:
		minute = int(minute_list[0]) * 60
		minute_list = minute_list[1]
	else:
		minute = 0
		minute_list = minute_list[0]
	second_list = minute_list.split('S')
	if len(second_list) == 2:
		second = int(second_list[0])
	else:
		second = 0
	return day + hour + minute + second


class CheckTaskState:

	def __init__(self):
		self.checks = [
			CheckContent(query='scrubs anfänger', min_duration=25),
			CheckContent(query='"big bang theory"', min_duration=20),
			CheckContent(query='"how i met your mother"', min_duration=15),
			CheckContent(query='tng', min_duration=40),
			CheckContent(query='"next generation"', min_duration=40),
			CheckContent(query='picard', min_duration=30),
			CheckContent(query='hawkeye', min_duration=30),
			CheckContent(query='wandavision', min_duration=30),
			CheckContent(query='loki', min_duration=30),
			CheckContent(query='"agent carter"', min_duration=30),
			CheckContent(query='mandalorian', min_duration=30),
			CheckContent(query='obi-wan', min_duration=30),
			CheckContent(query='"babylon berlin"', min_duration=30),
		]
		self.current_index = len(self.checks)

	def _check_dailymotion_url(self, url: CheckContent, db: Session):
		"""
			check a single url and add a video entry to db if needed

			:param url: video url to check
			:param db: database
		"""
		response = requests.get(url.dailymotion_url())
		video_list = DailymotionVideoList(**response.json())

		for video in video_list.videos:
			existing_video = db.query(models.Video).filter(models.Video.video_id == video['id']).first()

			if existing_video:
				continue

			payload = dict()
			payload['video_id'] = video['id']
			payload['title'] = video['title']
			payload['duration'] = video['duration']
			payload['action'] = 'Pending'  # cannot import ActionChoices (circular import)
			payload['platform'] = 'Dailymotion'
			new_video = models.Video(**payload)
			db.add(new_video)

		db.commit()

		time.sleep(1)

	def _authenticated_youtube_service(self):

		# Disable OAuthlib's HTTPS verification when running locally.
		# *DO NOT* leave this option enabled in production.
		os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

		# params
		api_service_name = "youtube"
		api_version = "v3"
		client_secrets_file = "client_secret_264441737748-pccau743h1d0ve02d0lgccn5a8qoo91j.apps.googleusercontent.com.json"

		# If modifying these scopes, delete the file token.json.
		scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

		creds = None
		# The file token.json stores the user's access and refresh tokens, and is
		# created automatically when the authorization flow completes for the first
		# time.
		if os.path.exists('token.json'):
			creds = Credentials.from_authorized_user_file('token.json', scopes)

		# If there are no (valid) credentials available, let the user log in.
		if not creds or not creds.valid:
			if creds and creds.expired and creds.refresh_token:
				creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
				creds = flow.run_local_server(port=0)

			# Save the credentials for the next run
			with open('token.json', 'w') as token:
				token.write(creds.to_json())

		return build(api_service_name, api_version, credentials=creds, developerKey=settings.GOOGLE_API_KEY)

	def _check_youtube_url(self, check_content: CheckContent, db: Session):

		try:
			youtube_service = self._authenticated_youtube_service()

			request = youtube_service.search().list(
				part="snippet",
				maxResults=50,
				regionCode="DE",
				type="video",
				videoDuration="long",
				videoType="episode",
				q=check_content.query
			)
			response = request.execute()

			video_list = YoutubeVideoList(**response)
			# print(video_list)

			for video in video_list.videos:
				existing_video = db.query(models.Video).filter(models.Video.video_id == video['id']['videoId']).first()

				if existing_video:
					continue

				# fetch duration
				detail_request = youtube_service.videos().list(
					part="snippet,contentDetails",
					id=video['id']['videoId']
				)
				detail_response = detail_request.execute()
				detail_video_list = YoutubeVideoList(**detail_response)
				print(detail_video_list)
				print(detail_video_list['items'][0]['contentDetails']['duration'])
				duration = convert_youtube_duration_to_seconds(
					detail_video_list['items'][0]['contentDetails']['duration'])
				time.sleep(1)

				payload = dict()
				payload['video_id'] = video['id']['videoId']
				payload['title'] = video['snippet']['title']
				payload['duration'] = duration
				payload['action'] = 'Pending'  # cannot import ActionChoices (circular import)
				payload['platform'] = 'Youtube'  # cannot import ActionChoices (circular import)
				new_video = models.Video(**payload)
				db.add(new_video)

			db.commit()

			time.sleep(1)
		except HttpError as error:
			# TODO(developer) - Handle errors from drive API.
			print(f'An error occurred: {error}')

	def check_background_work(self, db: Session):
		self.current_index = 0
		for check in self.checks:
			self._check_dailymotion_url(check, db)
			self._check_youtube_url(check, db)
			self.current_index += 1
		print(f'checked all {len(self.checks)} items')

	def get_state(self):
		status = 'ready'

		if self.current_index < len(self.checks):
			status = f'running ({self.current_index} / {len(self.checks)})'

		return {'status': status}


check_state = CheckTaskState()
