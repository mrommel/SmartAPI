"""exceptions module"""
from traceback import format_exc
from typing import Any

from fastapi import HTTPException, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_jwt_auth.exceptions import AuthJWTException
from pydantic import ValidationError
from starlette.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, \
	HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_504_GATEWAY_TIMEOUT

HTTP_600_ID_NOT_EXISTED = 600

_messages = {
	# 4XX
	HTTP_400_BAD_REQUEST: 'Request parameter verification failed',
	HTTP_401_UNAUTHORIZED: 'Permission check failed',
	HTTP_403_FORBIDDEN: 'Response parameter verification failed',
	HTTP_404_NOT_FOUND: 'The requested resource does not exist',
	# 5XX
	HTTP_500_INTERNAL_SERVER_ERROR: 'Internal server error',
	HTTP_504_GATEWAY_TIMEOUT: 'Timeout when requesting upstream service',
	# 600-999
	HTTP_600_ID_NOT_EXISTED: 'requestID does not exist',
}


class BaseException(HTTPException):
	"""
		Custom exception base class

		Exceptions thrown inside the program should be given to this base class
		Exceptions are thrown using this type or its subclasses, and will be handled and responded to in a unified
		manner.
		For nested exception handling, if this type of exception is caught, it can be raised directly, and other
		exceptions can be further processed.
	"""

	def __init__(self, code: int, message: str = None, detail: Any = None) -> None:
		"""
			:param code: Must be a value defined in status
			:param message: Exception information, which can usually be displayed to front-end users
			:param detail Detailed exception information, usually used for development troubleshooting
		"""
		self.code = code
		self.message = message if message else _messages[code]
		status_code = code if code < 600 else HTTP_500_INTERNAL_SERVER_ERROR
		super().__init__(status_code, detail)

	def __repr__(self) -> str:
		return f"code={self.code} message={self.message}\n detail={self.detail}"


class InternalException(BaseException):
	"""
		Internal error exception

		This type is usually used to raise when an exception occur
	"""


class ErrorResponse(JSONResponse):
	"""
		basic error response
	"""

	def __init__(self, status: int, message: str, detail: str):
		"""
			constructs a basic error response from a single error item content

			:param status:
			:param message:
			:param detail:
		"""
		if status >= 1000:  # The specified code value is abnormal
			super().__init__(
				status_code=HTTP_500_INTERNAL_SERVER_ERROR,
				content={
					'code': status,
					'message': message,
					'detail': detail
				}
			)
			return

		status_code = status if status < 600 else HTTP_500_INTERNAL_SERVER_ERROR
		message = _messages[status] if message is None else message
		super().__init__(
			status_code=status_code,
			content={
				'code': status,
				'message': message,
				'detail': detail
			}
		)


def init_exception(app: FastAPI):
	"""Initialize exception handling"""

	def get_detail(msg: str) -> str:
		return '\n'.join(msg.strip().split('\n')[-3:])

	@app.exception_handler(RequestValidationError)
	async def validation_exception_handler(request, exc: Exception) -> ErrorResponse:
		"""
			Request parameter exception

			:param request: the request
			:param exc: request validation exception
			:return: ErrorResponse
		"""
		_ = request  # prevent warning
		return ErrorResponse(HTTP_400_BAD_REQUEST, message='Request parameter verification failed', detail=str(exc))

	@app.exception_handler(ValidationError)
	async def resp_validation_exception_handler(request, exc: Exception) -> ErrorResponse:
		"""
			Response value parameter validation exception

			:param request: the request
			:param exc: validation error exception
			:return: ErrorResponse
		"""
		_ = request  # prevent warning
		return ErrorResponse(HTTP_403_FORBIDDEN, message='Response parameter verification failed', detail=str(exc))

	@app.exception_handler(BaseException)
	async def base_exception_handler(request, exc: BaseException) -> ErrorResponse:
		"""
			Catch custom exception

			:param request: the request
			:param exc: generic exception
			:return: ErrorResponse
		"""
		_ = request  # prevent warning
		# Print the detailed information of the exception to the console, and you can also write the log to the
		# corresponding file system here, etc.
		# print(format_exc(), flush=True)
		return ErrorResponse(exc.code, message=exc.message, detail=exc.detail)

	@app.exception_handler(HTTPException)
	async def http_exception_handler(request, exc: HTTPException) -> ErrorResponse:
		"""
			Catch FastAPI exceptions
		"""
		_ = request  # prevent warning
		# print(format_exc(), flush=True)
		return ErrorResponse(exc.status_code, message=str(exc.detail), detail=exc.detail)

	@app.exception_handler(AuthJWTException)
	def authjwt_exception_handler(exc: AuthJWTException):
		"""
			jwt error page

			:param exc: exception
			:return: JSONResponse with the error
		"""
		return ErrorResponse(exc.status_code, message=str(exc.message), detail=exc.detail)

	@app.exception_handler(Exception)
	async def all_exception_handler(request, exc: Exception) -> ErrorResponse:
		"""
			catch all other exceptions
		"""
		_ = request  # prevent warning
		_ = exc  # prevent warning
		_ = format_exc()
		# print(msg, flush=True)
		return ErrorResponse(HTTP_500_INTERNAL_SERVER_ERROR, message='inner exception', detail=get_detail(msg))

	@app.exception_handler(KeyError)
	async def key_error_handler(request, exc: KeyError) -> ErrorResponse:
		"""
			catch all other exceptions
		"""
		_ = request  # prevent warning
		_ = exc  # prevent warning
		_ = format_exc()
		# print(msg, flush=True)
		return ErrorResponse(HTTP_500_INTERNAL_SERVER_ERROR, message='inner exception', detail=get_detail(msg))

	@app.exception_handler(ValueError)
	async def value_error_handler(request, exc: ValueError) -> ErrorResponse:
		"""
			catch all other exceptions
		"""
		_ = request  # prevent warning
		_ = exc  # prevent warning
		_ = format_exc()
		# print(msg, flush=True)
		return ErrorResponse(HTTP_500_INTERNAL_SERVER_ERROR, message='inner exception', detail=get_detail(msg))
