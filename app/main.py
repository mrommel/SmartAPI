"""main module"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_jwt_auth.exceptions import AuthJWTException
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.routers import user, auth, check

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

origins = [
	settings.CLIENT_ORIGIN,
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(auth.router, tags=['Auth'], prefix='/api/auth')
app.include_router(user.router, tags=['Users'], prefix='/api/users')
app.include_router(check.router, tags=['Checks'], prefix='/api/checks')


@app.get("/", tags=['Website'], response_class=HTMLResponse)
async def home(request: Request):
	"""
		home page

		:param request: request
		:return:
	"""
	logged_in = False
	if 'logged_in' in request.cookies:
		logged_in = bool(request.cookies['logged_in'])
		print(f'logged_in={logged_in}')

	data = {
		"page": "Home page",
		"logged": f'{logged_in}'
	}
	return templates.TemplateResponse("index.html", {"request": request, "data": data})


@app.get('/profile', tags=['Website'], response_class=HTMLResponse)
def profile(request: Request):
	"""
		profile page

		:param request: request
		:return:
	"""
	logged_in = False
	if 'logged_in' in request.cookies:
		logged_in = bool(request.cookies['logged_in'])
		print(f'logged_in={logged_in}')

	data = {
		"page": "Profile",
		"logged": f'{logged_in}'
	}
	return templates.TemplateResponse("profile.html", {"request": request, "data": data})


@app.get('/checks', tags=['Website'], response_class=HTMLResponse)
def checks(request: Request):
	"""
		checks page

		:param request: request
		:return:
	"""
	logged_in = False
	if 'logged_in' in request.cookies:
		logged_in = bool(request.cookies['logged_in'])
		print(f'logged_in={logged_in}')

	data = {
		"page": "Checks",
		"logged": f'{logged_in}',
	}
	return templates.TemplateResponse("checks.html", {"request": request, "data": data})


@app.get('/api/healthchecker', tags=['Health'])
def root():
	"""
		sample end-point

		:return: 'hello world'
	"""
	return {'message': 'Hello World'}


@app.exception_handler(404)
async def custom_404_handler(request, __):
	"""
		404 error page

		:param request: request
		:param __: empty
		:return: HTMLResponse
	"""
	content = {
		"request": request,
		"error_title": "404 Not Found",
		"error_description": "The server can not find the requested resource. In the browser, this means the URL is "
		                     "not recognized. In an API, this can also mean that the endpoint is valid but the "
		                     "resource itself does not exist. Servers may also send this response instead of 403 "
		                     "Forbidden to hide the existence of a resource from an unauthorized client. This response "
		                     "code is probably the most well known due to its frequent occurrence on the web.",
		"data": {}
	}
	return templates.TemplateResponse("error.html", content)


@app.exception_handler(500)
async def custom_500_handler(request, __):
	"""
		handle 500 error

		:param request: requesr
		:param __: empty
		:return: HTMLResponse
	"""
	content = {
		"request": request,
		"error_title": "500 Internal Server Error",
		"error_description": "The server has encountered a situation it does not know how to handle.",
		"data": {}
	}
	return templates.TemplateResponse("error.html", content)


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(exc: AuthJWTException):
	"""
		jwt error page

		:param exc: exception
		:return: HTMLResponse
	"""
	return JSONResponse(
		status_code=exc.status_code,
		content={"detail": exc.message}
	)
