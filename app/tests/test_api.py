"""test module"""
import pytest
from fastapi.testclient import TestClient
import sqlalchemy.ext.asyncio

from app.main import app

# Redefining name - for fixtures
# pylint: disable=W0621

# Unused argument - for fixtures
# pylint: disable=W0613


client = TestClient(app)


@pytest_asyncio.fixture(autouse=True)
async def migrate():
    await migrate_db(conn_url)
    yield

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
	print(signup_response.json())
	assert signup_response.status_code == 200
	assert signup_response.json()["access_token"] is not None


@pytest.fixture
def valid_access_token(create_test_user) -> str:
	"""
		get a valid access_token

		:param create_test_user: fixture to create a test user
		:return: access_token
	"""
	login_response = client.post(
		"/api/auth/login",
		json={"email": "sample@abc.de", "password": "secret"},
	)
	assert login_response.status_code == 200
	assert login_response.json()["access_token"] is not None

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
	assert response.status_code == 200
	assert response.json() == {
		'error': 'Wrong login details!',
	}
