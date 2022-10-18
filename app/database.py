"""database module"""
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

__config_path__ = "../alembic.ini"
__migration_path__ = "../alembic/env.py"

cfg = Config(__config_path__)
cfg.set_main_option("script_location", __migration_path__)


async def migrate_db(conn_url: str):
	async_engine = create_async_engine(conn_url, echo=True)
	async with async_engine.begin() as conn:
		await conn.run_sync(__execute_upgrade)


def __execute_upgrade(connection):
	cfg.attributes["connection"] = connection
	command.upgrade(cfg, "head")


SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@" \
                          f"{settings.POSTGRES_HOSTNAME}:{settings.DATABASE_PORT}/{settings.POSTGRES_DB} "

if 'unittest' in sys.modules.keys():
	SQLALCHEMY_DATABASE_URL = "sqlite:///../db.sqlite"
	await migrate_db(SQLALCHEMY_DATABASE_URL)

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
