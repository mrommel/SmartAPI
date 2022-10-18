import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.fixture
def create_test_user():
	signup_response = client.post(
		"/api/users/login",
		json={"email": "sample@abc.de", "password": "secret", "fullname": "Sample Author"},
	)
	assert signup_response.status_code == 200
	assert signup_response.json()["access_token"] is not None


@pytest.fixture
def valid_access_token(create_test_user):
	login_response = client.post(
		"/api/users/login",
		json={"email": "sample@abc.de", "password": "secret"},
	)
	assert login_response.status_code == 200
	assert login_response.json()["access_token"] is not None

	return login_response.json()["access_token"]


def test_health():
	response = client.get(
		"/api/healthchecker",
	)
	assert response.status_code == 200


def test_login_successfully(valid_access_token):
	assert valid_access_token is not None


def test_login_wrong_password():
	response = client.post(
		"/user/login",
		json={"email": "abdulazeez@x.com", "password": "weakpassword"},
	)
	assert response.status_code == 200
	assert response.json() == {
		'error': 'Wrong login details!',
	}