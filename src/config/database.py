"""PostgreSQL connection helpers for the project.

This module reads database settings from the root .env file, builds a
reusable SQLAlchemy engine, and exposes a session factory and connection
helpers for the rest of the application.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Generator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOTENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(DOTENV_PATH)


class DatabaseConnectionError(RuntimeError):
	"""Raised when the PostgreSQL connection cannot be established."""


@dataclass(frozen=True)
class DatabaseSettings:
	host: str
	port: int
	name: str
	user: str
	password: str


def _read_settings() -> DatabaseSettings:
	import os

	host = os.getenv("DB_HOST")
	port = os.getenv("DB_PORT")
	name = os.getenv("DB_NAME")
	user = os.getenv("DB_USER")
	password = os.getenv("DB_PASSWORD")

	missing = [
		key
		for key, value in {
			"DB_HOST": host,
			"DB_PORT": port,
			"DB_NAME": name,
			"DB_USER": user,
			"DB_PASSWORD": password,
		}.items()
		if not value
	]
	if missing:
		missing_values = ", ".join(missing)
		raise DatabaseConnectionError(
			f"Missing database configuration in {DOTENV_PATH}: {missing_values}"
		)

	try:
		parsed_port = int(port)
	except ValueError as exc:
		raise DatabaseConnectionError("DB_PORT must be a valid integer.") from exc

	return DatabaseSettings(
		host=host,
		port=parsed_port,
		name=name,
		user=user,
		password=password,
	)


def _build_database_url(settings: DatabaseSettings) -> str:
	return (
		"postgresql+psycopg2://"
		f"{quote_plus(settings.user)}:{quote_plus(settings.password)}"
		f"@{settings.host}:{settings.port}/{quote_plus(settings.name)}"
	)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
	"""Return a reusable SQLAlchemy engine bound to the project database."""

	settings = _read_settings()
	database_url = _build_database_url(settings)

	try:
		engine = create_engine(
			database_url,
			pool_pre_ping=True,
			pool_recycle=1800,
			future=True,
		)
		with engine.connect() as connection:
			connection.execute(text("SELECT 1"))
		return engine
	except SQLAlchemyError as exc:
		raise DatabaseConnectionError(
			"Unable to connect to PostgreSQL. "
			f"Check that the database '{settings.name}' is running on "
			f"{settings.host}:{settings.port} and that the credentials in {DOTENV_PATH} are correct."
		) from exc


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


@contextmanager
def get_session() -> Generator[Session, None, None]:
	"""Yield a SQLAlchemy session and ensure it is closed afterwards."""

	session = SessionLocal()
	try:
		yield session
		session.commit()
	except SQLAlchemyError:
		session.rollback()
		raise
	finally:
		session.close()


@contextmanager
def get_connection() -> Generator:
	"""Yield a reusable database connection from the shared engine."""

	connection = get_engine().connect()
	try:
		yield connection
	finally:
		connection.close()


def test_connection() -> bool:
	"""Return True when the PostgreSQL connection is available."""

	try:
		with get_connection() as connection:
			connection.execute(text("SELECT 1"))
		return True
	except DatabaseConnectionError:
		raise
	except SQLAlchemyError as exc:
		raise DatabaseConnectionError("PostgreSQL connection test failed.") from exc

