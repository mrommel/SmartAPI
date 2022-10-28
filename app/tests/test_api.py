"""test module"""
from http.cookiejar import CookieJar

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import ObjectDeletedError
from starlette.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.routers.captcha import _set_captcha

# Redefining name - for fixtures
# pylint: disable=W0621

# Unused argument - for fixtures
# pylint: disable=W0613


client = TestClient(app)

# debug
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.sqlite"

engine = create_engine(
	SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
	"""
		creates a mock database

		:return: mock sqlite database
	"""
	try:
		db = TestingSessionLocal()
		yield db
	finally:
		db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def create_test_user():
	"""
		fixture to create a test user
		:return: Nothing
	"""
	db = TestingSessionLocal()
	# fake captcha
	_set_captcha('token', 'code', db)

	# make request
	signup_response = client.post(
		"/api/auth/signup",
		json={
			"name": "string",
			"email": "sample@abc.de",
			"photo": "abc.jpg",
			"password": "secret123",
			"passwordConfirm": "secret123",
			"role": "User",
			"gender": "Male",
			"verified": "true",
			"captchaCode": "code",
			"captchaToken": "token"
		},
	)

	assert signup_response.status_code == 201
	assert signup_response.json()["name"] == 'string'
	assert signup_response.json()["email"] == 'sample@abc.de'
	assert signup_response.json()["photo"] == 'abc.jpg'
	assert signup_response.json()["id"] is not None
	assert signup_response.json()["created_at"] is not None
	assert signup_response.json()["updated_at"] is not None

	return {}


@pytest.fixture
def valid_access_token(create_test_user, request) -> str:
	"""
		get a valid access_token

		:param request:
		:param create_test_user: fixture to create a test user
		:return: access_token
	"""
	# client.headers = {"Content-type": "application/json"}
	login_response = client.post(
		"/api/auth/login",
		json={"username": "sample@abc.de", "password": "secret123"},
	)
	assert login_response.status_code == 200
	assert login_response.json()["access_token"] is not None

	def delete_user():
		try:
			db = TestingSessionLocal()
			db.execute("delete from users")
			db.commit()
		except ObjectDeletedError as e:
			print(f"exception: {e}")

	request.addfinalizer(delete_user)

	return login_response.json()["access_token"]


def test_health():
	"""
		test the health endpoint

		:return: Nothing
	"""
	response = client.get(
		"/api/healthchecker",
	)
	assert response.status_code == 200


def test_cant_create_user_twice(valid_access_token):
	"""
		check if a user with the same username cant be created twice

		:param valid_access_token:
		:return:
	"""
	signup_response = client.post(
		"/api/auth/signup",
		json={
			"name": "string",
			"email": "sample@abc.de",
			"photo": "abc.jpg",
			"password": "secret234",
			"passwordConfirm": "secret234",
			"role": "User",
			"gender": "Male",
			"verified": "true",
			"captchaCode": "code",
			"captchaToken": "token"
		},
	)

	# print(signup_response.json())
	assert signup_response.status_code == 409
	assert signup_response.json() == {
		'code': 409,
		'message': 'Account already exist',
		'detail': 'Account already exist'
	}


def test_cant_create_user_password_mismatch():
	"""
		check if a user with different password cant be created
	"""
	db = TestingSessionLocal()
	# fake captcha
	_set_captcha('token', 'code', db)

	signup_response = client.post(
		"/api/auth/signup",
		json={
			"name": "string",
			"email": "sample2@abc.de", # different user
			"photo": "abc.jpg",
			"password": "secret234",
			"passwordConfirm": "secret1234", # mismatch
			"role": "User",
			"gender": "Male",
			"verified": "true",
			"captchaCode": "code",
			"captchaToken": "token"
		},
	)

	# print(signup_response.json())
	assert signup_response.status_code == 400
	assert signup_response.json() == {
		'code': 400,
		'message': 'Passwords do not match',
		'detail': 'Passwords do not match'
	}


def test_cant_create_user_captcha_empty():
	"""
		check if a user with different password cant be created
	"""
	signup_response = client.post(
		"/api/auth/signup",
		json={
			"name": "string",
			"email": "sample@abc.de",
			"photo": "abc.jpg",
			"password": "secret234",
			"passwordConfirm": "secret234",
			"role": "User",
			"gender": "Male",
			"verified": "true",
			"captchaCode": "",
			"captchaToken": "token"
		},
	)

	# print(signup_response.json())
	assert signup_response.status_code == 400
	assert signup_response.json() == {
		'code': 400,
		'message': 'Captcha not valid',
		'detail': 'Captcha not valid'
	}


def test_login_successfully(valid_access_token):
	"""
		test if access token is valid

		:param valid_access_token:
		:return: Nothing
	"""
	assert valid_access_token is not None


def test_login_wrong_username_and_password():
	"""
		verify that wrong credentials cannot be used

		:return: Nothing
	"""
	response = client.post(
		"/api/auth/login",
		json={"username": "abdulazeez@x.com", "password": "weakpassword"},
	)

	assert response.status_code == 400
	assert response.json() == {
		'code': 400,
		'detail': 'Incorrect Email or Password',
		'message': 'Incorrect Email or Password'
	}


def test_login_valid_username_and_wrong_password():
	"""
		verify that wrong credentials cannot be used

		:return: Nothing
	"""
	response = client.post(
		"/api/auth/login",
		json={"username": "sample@abc.de", "password": "weakpassword"},
	)

	# print(response.json())
	assert response.status_code == 400
	assert response.json() == {
		'code': 400,
		'detail': 'Incorrect Email or Password',
		'message': 'Incorrect Email or Password'
	}


def test_user_profile_success(valid_access_token):
	"""
		get current users profile data

		:param valid_access_token: fixture that adds a jwt cookie
		:return: Nothing
	"""

	response = client.get(
		"/api/users/me",
		headers={
			'accept': 'application/json',
			'Content-Type': 'application/json',
			'Authorization': f'Bearer {valid_access_token}',
		},
	)

	assert response.status_code == 200
	assert response.json()["name"] == 'string'
	assert response.json()["email"] == 'sample@abc.de'
	assert response.json()["photo"] == 'abc.jpg'
	assert response.json()["id"] is not None
	assert response.json()["created_at"] is not None
	assert response.json()["updated_at"] is not None


def test_user_profile_invalid_token():
	"""
		get error for current users profile data because of invalid token

		:return: Nothing
	"""

	response = client.get(
		"/api/users/me",
		headers={
			'accept': 'application/json',
			'Content-Type': 'application/json',
			'Authorization': 'Bearer abc',
		}
	)

	assert response.status_code == 401
	assert response.json() == {
		'code': 401,
		'detail': 'Token is invalid or has expired',
		'message': 'Token is invalid or has expired'
	}


def test_user_profile_empty_token():
	"""
		get error for current users profile data because of empty token

		:return: Nothing
	"""
	client.cookies = CookieJar()
	response = client.get(
		"/api/users/me",
		headers={
			'accept': 'application/json',
			'Content-Type': 'application/json',
			'Authorization': '',
		}
	)

	assert response.status_code == 401
	assert response.json() == {
		'code': 401,
		'detail': 'You are not logged in',
		'message': 'You are not logged in'
	}


def test_user_profile_no_token():
	"""
		get error for current users profile data because of no token

		:return: Nothing
	"""
	client.cookies = CookieJar()
	response = client.get(
		"/api/users/me",
		headers={
			'accept': 'application/json',
			'Content-Type': 'application/json',
			# no Authorization header at all
		},
		cookies={}
	)

	assert response.status_code == 401
	assert response.json() == {
		'code': 401,
		'detail': 'You are not logged in',
		'message': 'You are not logged in'
	}
