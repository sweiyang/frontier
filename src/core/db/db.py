import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from core.config import get_config


def _ensure_sqlite_dir(db_url: str) -> None:
    """If db_url is a SQLite file URL, ensure the database file's parent directory exists."""
    if not db_url or not db_url.strip().lower().startswith("sqlite:///"):
        return
    path_part = db_url.strip()[10:]  # after "sqlite:///"
    if not path_part or path_part == ":memory:":
        return
    # Resolve relative paths (e.g. ./data/conduit.db) against cwd
    db_path = os.path.abspath(path_part)
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, db_url: str = None):
        """
        Initialize database connection.

        Args:
            db_url: Full database URL (e.g., 'postgresql://user:pass@host:port/dbname'
                    or 'postgresql+psycopg2://...' for PostgreSQL/Yugabyte).
                    If provided, this takes precedence over config.

        Configuration: Set database.url in config.yaml, or pass db_url here.
        Supports both SQLite (sqlite:///path/to/db) and PostgreSQL (postgresql://...).
        """
        db_url = db_url or get_config().database_url

        if db_url:
            _ensure_sqlite_dir(db_url)
            self.engine = create_engine(db_url)
        else:
            # Default to SQLite in data directory
            data_dir = os.path.join(os.path.dirname(__file__), "../../data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "conduit.db")
            self.engine = create_engine(f"sqlite:///{db_path}")
        
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        # Import models to register them with Base
        from core.db import db_chat  # noqa: F401
        from core.db import db_project  # noqa: F401
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.SessionLocal()

