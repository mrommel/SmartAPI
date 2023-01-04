"""main module"""

from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.config import settings
# from app.debug import VKAPI, TwoFactorException
from app.exceptions import init_exception
from app.routers import user, auth, check, captcha
from app.schemas import VersionResponse

_version = '1.0.0'

app = FastAPI(version=_version)

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
app.include_router(captcha.router, tags=['Users'], prefix='/api/captcha')
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


@app.get('/api/healthchecker', tags=['Core'])
def root():
	"""
		sample end-point

		:return: 'hello world'
	"""
	return {'message': 'Hello World'}


@app.get("/api/version", tags=['Core'], summary='Get system version number', response_model=VersionResponse)
async def version_api():
	"""Get system version number"""
	return {"version": _version}


second_factor_needed = False


@app.post('/videos', tags=['Website'])
def videos_post(request: Request, token: str = Form()):
	"""
		videos 2fa page
	"""
	global second_factor_needed
	second_factor_needed = False

	def second_factor():
		print(f'use 2fa code: {token}')
		return token, True

	api = VKAPI(
		username='+4917660980345',
		password=',,K4+$HXm9ZY49)',
		auth_handler=second_factor,
		app_id='51464256',
		client_secret='ixZVx5bYH1O2AEyqfiHq'
	)

	try:
		videos = api.search_videos('Star Trek')
		print(f'videos={videos}')
	except TwoFactorException:
		print('second factor needed - show form1')
		raise TwoFactorException('2fa not handled')

	if second_factor_needed:
		print('second factor needed - show form2')
		raise TwoFactorException('2fa not handled')

	data = {
		"page": "Checks",
		"logged": 'False',
		"videos": videos
	}
	return templates.TemplateResponse("videos.html", {"request": request, "data": data})


@app.get('/videos', tags=['Website'], response_class=HTMLResponse)
def videos_get(request: Request):
	"""
		videos page
	"""

	api = VKAPI(
		username=None,
		password=None,
		token='vk1.a'
		      '.ylVbfGBPSrKFWZ9dupfU62w2M4yvCPbZyeqpvSjsX7FjUcXaZmfBvYTSKBfdCatSTbr8Xnr3qeVQF_fk8FgIyvWYvF8pkyzDo04yzVD'
		      'hmW-bhsr6fuWZG13HKM1elu6W3OsjWXj2IUOXS8PKhB31guFvG9fRgvwrb8AVX47bET94Veu0PIPdzCmGdf5J57jv',
		app_id='51464256',
		client_secret=None
	)
	# api.auth()

	videos = []
	template = 'videos.html'
	try:
		videos = api.search_videos('Star Trek')
		print(f'videos={videos}')
	except:
		print('error')

	data = {
		"page": "Videos",
		"logged": 'False',
		"videos": videos
	}
	return templates.TemplateResponse(template, {"request": request, "data": data})


# *****************************************************

init_exception(app)
