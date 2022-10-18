"""test module"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Redefining name - for fixtures
# pylint: disable=W0621

# Unused argument - for fixtures
# pylint: disable=W0613


client = TestClient(app)

# debug
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
	SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
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
	signup_response = client.post(
		"/api/auth/register",
		json={
			"name": "string",
			"email": "sample@abc.de",
			"photo": "abc.jpg",
			"password": "secret123",
			"passwordConfirm": "secret123",
			"role": "user",
			"verified": "true"
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
	login_response = client.post(
		"/api/auth/login",
		json={"email": "sample@abc.de", "password": "secret123"},
	)
	assert login_response.status_code == 200
	assert login_response.json()["access_token"] is not None

	def delete_user():
		try:
			db = TestingSessionLocal()
		finally:
			db.execute("delete from users")
			db.commit()

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


def test_login_successfully(valid_access_token):
	"""
		test if access token is valid

		:param valid_access_token:
		:return: Nothing
	"""
	assert valid_access_token is not None


def test_login_wrong_password():
	"""
		verify that wrong credentials cannot be used

		:return: Nothing
	"""
	response = client.post(
		"/api/auth/login",
		json={"email": "abdulazeez@x.com", "password": "weakpassword"},
	)

	assert response.status_code == 400
	assert response.json() == {
		'detail': 'Incorrect Email or Password',
	}



