"""database module"""

from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

__config_path__ = "../alembic.ini"
__migration_path__ = "../alembic/env.py"

cfg = Config(__config_path__)
cfg.set_main_option("script_location", __migration_path__)


SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@" \
                          f"{settings.POSTGRES_HOSTNAME}:{settings.DATABASE_PORT}/{settings.POSTGRES_DB} "

engine = create_engine(
	SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
	"""
		get db context from env values

		:return: db context
	"""
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
