import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, db_path: str = None):
        # Default to data/conduit.db relative to project root
        if db_path is None:
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

