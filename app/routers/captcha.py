"""captcha module"""
import datetime
import string
import tempfile
import random

from fastapi import Path, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import FileResponse
from captcha.image import ImageCaptcha

from app import models
from app.database import get_db

_captcha_prefix = 'sadjer54!654'
_captcha_valid = 5 * 60
# All characters of verification code
_captcha_char_all = string.ascii_letters + string.digits

router = APIRouter()


# https://github.com/ibbd-dev/fastapi-start/tree/e84277e8d5af45d2f5dae19268ff3ed6721c71d6/app/project/captcha_module

def check_captcha_code(token: str, code: str, db: Session) -> bool:
	"""
		Verify verification captcha code

		:param token: token of the captcha
		:param code: code of user
		:param db: database
		:return: true if captcha code can be found in database
	"""
	token = f"{_captcha_prefix}_{token}"
	code = code.lower().strip()
	captcha = db.query(models.Captcha).filter(models.Captcha.token == token).first()
	if captcha is None:
		return False

	# Verification code can only be used once
	db.delete(captcha)

	# if captcha.created + _captcha_valid < datetime.now:
	#	# expired
	#	return False

	saved_code = captcha.code

	# saved_code = str(saved_code, encoding='utf8')
	print(f'{saved_code} == {code}')
	return saved_code == code


def _set_captcha(token: str, code: str, db: Session) -> bool:
	"""
		Set verification code

		:param token: token
		:param code: code
		:param db: database
		:return:
	"""
	token = f"{_captcha_prefix}_{token}"
	code = code.lower()
	payload = {
		'code': code,
		'token': token,
	}
	new_user = models.Captcha(**payload)
	db.add(new_user)
	db.commit()
	return True


@router.get("/{token}",
			summary='Generate captcha image',
			response_class=FileResponse,
			responses={
				200: {"content": {"image/png": {}}},
				500: {"description": "Generate verification code exception"},
			})
async def captcha_image_api(
	token: str = Path(..., regex='^[0-9a-z\\-]+$', title='Form unique value, used to identify the form',
					description='Form unique value, used to identify the form'),
	db: Session = Depends(get_db)
):
	"""
		Generate captcha image

		Before the form is generated, a unique string token is usually generated. The token value can be used to avoid
		repeated submissions and also to request a verification code.
		The verification code is not case-sensitive.
		This interface returns an image file.

		:param token: token to get a captcha image for (will be store together with generated code)
		:param db: database
		:return:
	"""
	code = ''.join(random.sample(_captcha_char_all, 6))
	# print('captcha: ', code)

	# @todo delete all entries that are expired

	if not _set_captcha(token, code, db):
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		                    detail='Failed to generate verification code')
	image = ImageCaptcha().generate_image(code)
	with tempfile.NamedTemporaryFile(mode='w+b', suffix='.png', delete=False) as outfile:
		image.save(outfile)
		return FileResponse(outfile.name, media_type='image/png')
