from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from core.config import get_config
from core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class for all database models."""
    pass


class Database:
    """
    Database connection manager for PostgreSQL/YugabyteDB.
    
    Handles connection setup, schema management, and session creation.
    Configuration is loaded from config.yaml.
    
    Attributes:
        engine: SQLAlchemy engine instance.
        schema: Optional schema name for table isolation.
        SessionLocal: Session factory for creating database sessions.
    """
    
    def __init__(self):
        """
        Initialize PostgreSQL/YugabyteDB database connection.

        Configuration is read from config.yaml under database.<env>:
          - host, port, dbname, user, credential, schema

        SQLite is not supported.
        """
        config = get_config()

        user = config.database_user
        credential = config.database_credential
        host = config.database_host
        port = config.database_port
        dbname = config.database_name

        db_url = f"postgresql://{user}:{credential}@{host}:{port}/{dbname}"
        logger.info("Connecting to database at %s:%s/%s", host, port, dbname)
        self.engine = create_engine(db_url)
        self.schema = config.database_schema

        if self.schema:
            self._ensure_schema_exists()
            self._set_search_path()

        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.debug("Database connection established")

    def _ensure_schema_exists(self):
        """Create the schema if it doesn't exist."""
        logger.debug("Ensuring schema '%s' exists", self.schema)
        with self.engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.schema}"))
            conn.commit()

    def _set_search_path(self):
        """Set search_path on every new connection so tables use the configured schema."""
        schema = self.schema

        @event.listens_for(self.engine, "connect")
        def set_search_path(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute(f"SET search_path TO {schema}, public")
            cursor.close()

    def create_tables(self):
        """
        Create all database tables defined in SQLAlchemy models.
        
        Imports db_chat and db_project modules to ensure all models
        are registered before creating tables.
        """
        from core.db import db_chat  # noqa: F401
        from core.db import db_project  # noqa: F401
        logger.debug("Creating database tables")
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """
        Create and return a new database session.
        
        Returns:
            A SQLAlchemy Session instance bound to the database engine.
        """
        return self.SessionLocal()
