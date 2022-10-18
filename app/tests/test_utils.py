"""test utils module"""
from starlette.testclient import TestClient


class CookieConfigurableTestClient(TestClient):
	"""
		class that provides a configurable text client
		gist: https://gist.github.com/melvinkcx/d208972b452641b8c1bd504f237b7d3a
	"""
	_access_token = None

	def set_access_token(self, token):
		"""
			method to overwrite the access token

			:param token:
			:return: Nothing
		"""
		self._access_token = token

	def reset(self):
		"""
			method to reset the access token

			:return: Nothing
		"""
		self._access_token = None

	def request(self, *args, **kwargs):
		"""
			method to exchange the access token (if needed)

			:param args: args
			:param kwargs: kwargs
			:return: result of request
		"""
		cookies = kwargs.get("cookies")
		if cookies is None and self._access_token is not None:
			kwargs["cookies"] = {"access_token": self._access_token}

		return super().request(*args, **kwargs)
