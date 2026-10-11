# src/config.py
"""
Application & database configuration.

Environment variables (loaded from a `.env` file if present, otherwise from
the system environment):

    DB_NAME      default: db_learn
    DB_OWNER     default: premananda
    DB_PASSWORD  default: ""            (empty string)
    DB_HOST      default: localhost
    DB_PORT      default: 5432
    DB_USER      default: postgres
    ENV          default: development   ("development" | "production")

Special characters in DB_USER, DB_PASSWORD and DB_NAME are URL-encoded
automatically, so passwords like `p@ss:w/rd` are safe.

--------------------------------------------------------------------------------
USAGE
--------------------------------------------------------------------------------

1. Import the pre-built singletons (recommended):

    from src.config import config, db_config

    # Async SQLAlchemy engine
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(db_config.ASYNC_DATABASE_URL)

    # Sync SQLAlchemy engine
    from sqlalchemy import create_engine
    engine = create_engine(db_config.DATABASE_URL)

    # Raw connection params (e.g. for psycopg2 / asyncpg directly)
    import asyncpg
    conn = await asyncpg.connect(**db_config.get_connection_params())

    # DSN string
    dsn = db_config.get_dsn()

2. Check the environment:

    if config.is_development:
        ...
    elif config.is_production:
        ...

3. Dump non-sensitive settings (safe to log):

    logger.info(config.get_all())
    # {'database': {'name': ..., 'owner': ..., 'host': ..., 'port': ...,
    #               'user': ...},
    #  'environment': 'development'}

4. Build a fresh instance (e.g. in tests, with env vars already patched):

    from src.config import DatabaseConfig
    cfg = DatabaseConfig(load_env=False)   # skip .env loading

5. Verify that required env vars were explicitly provided:

    if not db_config.is_configured():
        logger.warning("Falling back to default DB settings")

--------------------------------------------------------------------------------
"""

import logging
import os
from typing import Any
from urllib.parse import quote_plus

from dotenv import find_dotenv, load_dotenv

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration class."""

    def __init__(self, load_env: bool = True):
        if load_env:
            self._load_env()
        self._init_db_config()

    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        env_file = find_dotenv()
        if env_file:
            load_dotenv(env_file)
            logger.info(f"✅ Loaded environment from: {env_file}")
        else:
            logger.warning("⚠️ No .env file found, using system environment variables")

    def _init_db_config(self) -> None:
        """Initialize database configuration from environment variables."""
        self.DB_NAME = os.getenv("DB_NAME", "db_learn")
        self.DB_OWNER = os.getenv("DB_OWNER", "premananda")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "")
        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = os.getenv("DB_PORT", "5432")
        self.DB_USER = os.getenv("DB_USER", "postgres")

        # URL-encode user, password, and database name to handle special characters
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        host = self.DB_HOST
        port = self.DB_PORT
        name = quote_plus(self.DB_NAME)

        # Synchronous PostgreSQL URL
        self.DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{name}"

        # Async SQLAlchemy URL (asyncpg driver)
        self.ASYNC_DATABASE_URL = (
            f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
        )

    def get_connection_params(self) -> dict[str, Any]:
        """Get database connection parameters as dictionary."""
        return {
            "database": self.DB_NAME,
            "user": self.DB_USER,
            "password": self.DB_PASSWORD,
            "host": self.DB_HOST,
            "port": self.DB_PORT,
        }

    def get_dsn(self) -> str:
        """Get Database Source Name (DSN) string."""
        return self.DATABASE_URL

    def is_configured(self) -> bool:
        """Check if required environment variables are explicitly set."""
        required = ["DB_NAME", "DB_USER", "DB_HOST"]
        return all(os.getenv(attr) is not None for attr in required)

    def __repr__(self) -> str:
        return f"DatabaseConfig(DB_NAME={self.DB_NAME}, DB_HOST={self.DB_HOST}, DB_USER={self.DB_USER})"


class AppConfig:
    """Main application configuration class."""

    def __init__(self):
        self._load_env()
        self.db = DatabaseConfig(load_env=False)

    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        env_file = find_dotenv()
        if env_file:
            load_dotenv(env_file)

    @property
    def is_development(self) -> bool:
        return os.getenv("ENV", "development").lower() == "development"

    @property
    def is_production(self) -> bool:
        return os.getenv("ENV", "development").lower() == "production"

    def get_all(self) -> dict[str, Any]:
        """Get all non-sensitive configuration as dictionary."""
        return {
            "database": {
                "name": self.db.DB_NAME,
                "owner": self.db.DB_OWNER,
                "host": self.db.DB_HOST,
                "port": self.db.DB_PORT,
                "user": self.db.DB_USER,
            },
            "environment": os.getenv("ENV", "development"),
        }


# Create singleton instances
config = AppConfig()
db_config = config.db


if __name__ == "__main__":
    # Quick manual check:  python -m src.config
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print(
        f"Environment      : {'development' if config.is_development else 'production'}"
    )
    print(f"DB explicitly set: {db_config.is_configured()}")
    print(f"Config object    : {db_config!r}")
    print(f"Sync DSN         : {db_config.get_dsn()}")
    print(f"Async DSN        : {db_config.ASYNC_DATABASE_URL}")
    print(f"Connection params: {db_config.get_connection_params()}")
    print(f"Public settings  : {config.get_all()}")

    # Example: create an async engine (requires SQLAlchemy installed)
    #
    # import asyncio
    # from sqlalchemy.ext.asyncio import create_async_engine
    #
    # async def _check():
    #     engine = create_async_engine(db_config.ASYNC_DATABASE_URL)
    #     async with engine.connect() as conn:
    #         print("✅ Connected:", await conn.scalar(text("SELECT 1")))
    #     await engine.dispose()
    #
    # asyncio.run(_check())
