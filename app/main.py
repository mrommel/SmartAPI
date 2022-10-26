"""main module"""

from fastapi import FastAPI, HTTPException
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


@app.exception_handler(HTTPException)
async def http_exception_handler(_request, exc):
	"""
		generic exception handler

		:param _request: request
		:param exc: exception
		:return: JSONResponse with the error
	"""
	return JSONResponse(
		status_code=exc.status_code,
		content={
			"detail": exc.detail
		}
	)


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(exc: AuthJWTException):
	"""
		jwt error page

		:param exc: exception
		:return: JSONResponse with the error
	"""
	return JSONResponse(
		status_code=exc.status_code,
		content={
			"detail": exc.message
		}
	)
