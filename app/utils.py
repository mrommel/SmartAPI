"""utils module"""
from passlib.context import CryptContext

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
