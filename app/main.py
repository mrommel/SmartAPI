"""main module"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.config import settings
from app.routers import user, auth

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


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
	logged_in = False
	if 'logged_in' in request.cookies:
		logged_in = bool(request.cookies['logged_in'])
		print(f'logged_in={logged_in}')

	data = {
		"page": "Home page",
		"logged": f'{logged_in}'
	}
	return templates.TemplateResponse("index.html", {"request": request, "data": data})


@app.get('/api/healthchecker')
def root():
	"""
		sample end-point

		:return: 'hello world'
	"""
	return {'message': 'Hello World'}


@app.exception_handler(404)
async def custom_404_handler(request, __):
	return templates.TemplateResponse("error.html", {"request": request, "error": "404"})


@app.exception_handler(500)
async def custom_500_handler(request, __):
	return templates.TemplateResponse("error.html", {"request": request, "error": "500"})
