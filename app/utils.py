"""utils module"""
import os
# -*- coding: utf-8 -*-
import time
from urllib.parse import urlencode, quote_plus

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from urllib3.exceptions import MaxRetryError

from app import models
from app.config import settings
from app.models import PlatformChoices, ActionChoices

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


class CheckContent:
	"""
		class that encapsulates data to be checked on different platforms
	"""

	def __init__(self, query: str, min_duration: int):
		self.query = query
		self.min_duration = min_duration

	def dailymotion_url(self) -> str:
		"""
			get the dailymotion video url

			:return: dailymotion video url
		"""
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


class DailymotionVideoItem:
	"""
		class that represents a dailymotion video idem
	"""

	def __init__(self, id: str, title: str, duration: int):
		"""
			constructs a dailymotion video item

			:param id: id of video
			:param title: title of video
			:param duration: duration of video
		"""
		self.video_id = id
		self.title = title
		self.duration = duration

	def __repr__(self):
		"""
			get the string representation of dailymotion video item

			:return: string representation of dailymotion video item
		"""
		return f'<video id={self.video_id}, title="{self.title}", duration={self.duration}>'


class DailymotionVideoList:
	"""
		class that encapsulates a dailymotion video list
	"""

	def __init__(self, page: int, limit: int, explicit, total, has_more, list: [DailymotionVideoItem]):
		"""

			:param page: current page
			:param limit: limit
			:param explicit: yes / no
			:param total: total number of results
			:param has_more: are there more results
			:param list: list of videos
		"""
		self.page = page
		self.limit = limit
		self.explicit = explicit
		self.total = total
		self.has_more = has_more
		self.videos = list

	def __repr__(self):
		"""
			get a string representation of this dailymotion video list

			:return: string representation of this dailymotion video list
		"""
		return f'<dm videolist({self.total}) = [{self.videos}]>'


class YoutubePageInfo:
	"""
		class that encapsulates a youtube page info
	"""

	def __init__(self, totalResults: int, resultsPerPage: int):
		"""
			constructor for a youtube page info

			:param totalResults: total results
			:param resultsPerPage: results per page
		"""
		self.totalResults = totalResults
		self.resultsPerPage = resultsPerPage


class YoutubeVideoId:
	"""
		class representation of youtube video id
	"""

	def __init__(self, kind: str, videoId: str):
		"""
			constructs a youtube video id

			:param kind: kind is a youtube video id
			:param videoId: youtube video id
		"""
		self.kind = kind
		self.videoId = videoId


class YoutubeSnippet:
	"""
		class that represents youtube video data
	"""

	def __init__(self, title: str, description: str):
		"""
			constructor of youtube video data

			:param title: title of the video
			:param description: description of the video
		"""
		self.title = title
		self.description = description

	def __repr__(self):
		"""
			get string representation of a youtube video data

			:return: string representation of a youtube video data
		"""
		return f'<yt video snippet({self.title})>'


class YoutubeContentDetails:
	"""
		class represents youtube video content details
	"""

	def __init__(self, duration: str):
		"""
			constructor of youtube content details

			:param duration: duration in youtube duration representation
		"""
		self.duration = duration

	def __repr__(self):
		"""
			get string representation of youtube duration representation

			:return: string representation of youtube duration representation
		"""
		return f'<yt video content duration={self.duration}>'


class YoutubeVideoItem:
	"""
		class that represents a youtube video
	"""

	def __init__(
		self,
		kind: str,
		etag: str,
		id: YoutubeVideoId,
		snippet: YoutubeSnippet,
		contentDetails: YoutubeContentDetails = None
	):
		"""
			constructor of a youtube video

			:param kind: kind (it is a video)
			:param etag: etag of video
			:param id: struct with video id
			:param snippet: additional data
			:param contentDetails: additional video data
		"""
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


class YoutubeVideoList:
	"""
		class that represents a youtube video list
	"""

	def __init__(
		self,
		kind: str,
		etag: str,
		nextPageToken: str = '',
		regionCode: str = '',
		pageInfo: YoutubePageInfo = None,
		items: [YoutubeVideoItem] = None
	):
		"""
			build YouTube video list

			:type pageInfo: page info
			:type nextPageToken: token of next page
		"""
		self.kind = kind
		self.etag = etag
		self.nextPageToken = nextPageToken
		self.regionCode = regionCode
		self.pageInfo = pageInfo

		if items is None:
			self.videos = []
		else:
			self.videos = items

	def __repr__(self):
		return f'<yt videolist({len(self.videos)}) = [{self.videos}]>'


def convert_youtube_duration_to_seconds(duration) -> int:
	"""
		convert the string representation of a youtube string to seconds

		:param duration: duration in youtube string representation
		:return: youtube string in seconds
	"""
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
	"""
		class that represents the complete data of a check request
	"""

	def __init__(self):
		self.checks = [
			CheckContent(query='scrubs anfänger', min_duration=25),
			CheckContent(query='"big bang theory"', min_duration=20),
			CheckContent(query='"how i met your mother"', min_duration=15),
			CheckContent(query='tng', min_duration=40),
			CheckContent(query='"next generation"', min_duration=40),
			CheckContent(query='"nächste generation"', min_duration=40),
			CheckContent(query='"star trek"', min_duration=40),
			CheckContent(query='picard', min_duration=30),
			CheckContent(query='hawkeye', min_duration=30),
			CheckContent(query='wandavision', min_duration=30),
			CheckContent(query='loki', min_duration=30),
			CheckContent(query='"agent carter"', min_duration=15),
			CheckContent(query='mandalorian', min_duration=30),
			CheckContent(query='"S.H.I.E.L.D."', min_duration=30),
			CheckContent(query='mandalorianer', min_duration=30),
			CheckContent(query='obi-wan', min_duration=30),
			CheckContent(query='kenobi', min_duration=30),
			CheckContent(query='"babylon berlin"', min_duration=30),
			CheckContent(query='Voyager', min_duration=30),
			CheckContent(query='"Deep space nine"', min_duration=30),
			CheckContent(query='"Agatha Christie" Poirot', min_duration=30),
			# CheckContent(query='"Mord ist ihr Hobby"', min_duration=30),
			CheckContent(query='wakanda', min_duration=30),
			CheckContent(query='"police academy"', min_duration=30),
			CheckContent(query='"Die Tudors"', min_duration=30),
			CheckContent(query='"Neues aus Entenhausen"', min_duration=20),
			CheckContent(query='"The Crown"', min_duration=45),
			CheckContent(query='"Andor"', min_duration=35),
			CheckContent(query='"New girl"', min_duration=20),
			CheckContent(query='"broke girls"', min_duration=20),
			CheckContent(query='Bridgerton', min_duration=45),
			CheckContent(query='"Dark desire"', min_duration=25),
			CheckContent(query='Foundation', min_duration=35),
			CheckContent(query='"all mankind"', min_duration=25),
			CheckContent(query='"sex life"', min_duration=45),
			CheckContent(query='Sanditon', min_duration=45),
			CheckContent(query='"carnival row"', min_duration=25),
		]
		self.current_index = len(self.checks)

	def _check_dailymotion_url(self, url: CheckContent, db: Session):
		"""
			check a single url and add a video entry to db if needed

			:param url: video url to check
			:param db: database
		"""
		dailymotion_url = url.dailymotion_url()
		try:
			response = requests.get(dailymotion_url, timeout=10)
		except (requests.exceptions.ConnectionError, MaxRetryError, requests.exceptions.ReadTimeout):
			print(f'cannot fetch url from dailymotion: {dailymotion_url}')
			return

		video_list = DailymotionVideoList(**response.json())

		for video in video_list.videos:
			existing_video = db.query(models.Video).filter(models.Video.video_id == video['id']).first()

			if existing_video:
				continue

			payload = {
				'video_id': video['id'],
				'title': video['title'],
				'duration': video['duration'],
				'action': 'Pending',  # cannot import ActionChoices (circular import)
				'platform': 'Dailymotion'
			}

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
			with open('token.json', 'w', encoding="utf-8") as token:
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

			video_list_details = []

			for video in video_list.videos:
				existing_video = db.query(models.Video).filter(models.Video.video_id == video['id']['videoId']).first()

				if existing_video:
					continue

				video_list_details.append(video['id']['videoId'])

			if len(video_list_details) == 0:
				print('no videos to fetch details for')
				return

			video_ids = ','.join(video_list_details)
			# print(f'try to fetch more info for: {video_ids}')

			# fetch duration for these videos
			request = youtube_service.videos().list(
				part="snippet,contentDetails",
				id=video_ids
			)

			response = request.execute()
			video_list = YoutubeVideoList(**response)
			# print(details_video_list)

			for video in video_list.videos:
				# print(video['contentDetails']['duration'])
				# print(video)
				duration = convert_youtube_duration_to_seconds(video['contentDetails']['duration'])
				# print(f"duration of {video['id']} / {video['snippet']['title']}: {duration}")

				payload = {
					'video_id': video['id'],
					'title': video['snippet']['title'],
					'duration': duration,
					'action': 'Pending',  # cannot import ActionChoices (circular import)
					'platform': 'Youtube'  # cannot import PlatformChoices (circular import)
				}

				new_video = models.Video(**payload)
				db.add(new_video)

			db.commit()

			time.sleep(1)
		except HttpError as error:
			# TODO(developer) - Handle errors from drive API.
			print(f'An error occurred: {error}')

	def check_background_work(self, db: Session):
		"""
			starts the check of dailymotion and youtube

			:param db: database
			:return: Nothing
		"""
		self.current_index = 0
		for check in self.checks:
			self._check_dailymotion_url(check, db)
			# self._check_youtube_url(check, db)
			self.current_index += 1
		print(f'checked all {len(self.checks)} items')

	def get_state(self):
		"""
			get the state of the current background thread

			:return: state of the current background thread
		"""
		status = 'ready'

		if self.current_index < len(self.checks):
			status = f'running ({self.current_index} / {len(self.checks)})'

		return {'status': status}


check_state = CheckTaskState()


class DownloadTaskState:
	"""
		class that represents the complete data of a download request
	"""

	def __init__(self):
		pass

	def download_background_work(self, video_id: str, platform: str, db: Session):
		"""
			starts the download of dailymotion or youtube video

			:param video_id: id of video
			:param platform: platform
			:param db: database
			:return: Nothing
		"""
		user_path = os.path.expanduser('~')
		if platform == PlatformChoices.YOUTUBE.value:
			print(f'started downloading of youtube video {video_id}')
			os.system(f"cd '{user_path}/Downloads'; youtube-dl https://www.youtube.com/watch?v={video_id}")
			print(f'finished downloading of youtube video {video_id}')
		elif platform == PlatformChoices.DAILYMOTION.value:
			print(f'started downloading of dailymotion video {video_id}')

			os.system(f"cd '{user_path}/Downloads'; youtube-dl https://www.dailymotion.com/video/{video_id}")
			print(f'finished downloading of dailymotion video {video_id}')
		else:
			print(f'could not download video from platform: {platform}')
			return

		existing_video = db.query(models.Video).filter(models.Video.video_id == video_id).first()
		if existing_video is None:
			raise Exception('can get downloaded video')

		existing_video.action = ActionChoices.DOWNLOADED.value
		db.add(existing_video)
		db.commit()


download_state = DownloadTaskState()
