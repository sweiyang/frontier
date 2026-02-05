import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from conduit.core.config import get_config


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, db_url: str = None, db_path: str = None):
        """
        Initialize database connection.

        Args:
            db_url: Full database URL (e.g., 'postgresql://user:pass@host:port/dbname'
                    or 'postgresql+psycopg2://...' for PostgreSQL/Yugabyte).
                    If provided, this takes precedence over config and db_path.
            db_path: SQLite database file path (for backward compatibility).
                    Only used if db_url is not provided.

        Configuration: Set database.url in config.yaml, or pass db_url here.
        Supports both SQLite (sqlite:///path/to/db) and PostgreSQL (postgresql://...).
        """
        db_url = db_url or get_config().database_url

        if db_url:
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
        from conduit.core.db import db_chat  # noqa: F401
        from conduit.core.db import db_project  # noqa: F401
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.SessionLocal()

