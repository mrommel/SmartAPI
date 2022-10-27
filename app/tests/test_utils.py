"""test of utility functions module"""
from app.utils import hash_password, verify_password


def test_hash_password():
	"""
		check password hash
	"""
	hashed_password = hash_password('password123')
	assert hashed_password.startswith('$2b$12$') is True


def test_verify_password():
	"""
		verify password hash
	"""
	hashed_password = hash_password('password123')
	assert verify_password('password123', hashed_password) is True
