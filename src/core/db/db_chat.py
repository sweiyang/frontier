import re
from datetime import datetime
from typing import Dict, List, Optional, Type

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import text
from sqlalchemy.orm import backref, relationship

from core.db.db import Base, Database, _get_column_type_sql
from core.logging import get_logger

logger = get_logger(__name__)


# Association table for many-to-many relationship between users and projects
# Defined here (before User class) to ensure it's registered in metadata before mapper configuration
project_members = Table(
    "project_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("role", String(50), default="member"),  # owner, admin, member
    Column("joined_at", DateTime, default=datetime.utcnow),
)


class User(Base):
    """
    User account model.

    Stores user credentials and maintains relationships to owned projects
    and project memberships.

    Attributes:
        id: Primary key.
        username: Unique username (normalized to lowercase).
        created_at: Account creation timestamp.
        owned_projects: Projects where user is the owner.
        projects: Projects where user is a member (via project_members).
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owned_projects = relationship("Project", back_populates="owner")
    projects = relationship("Project", secondary=project_members, back_populates="members")


# Registry to cache dynamically created table classes
_project_tables: Dict[str, Dict[str, Type]] = {}


def sanitize_table_name(project_name: str) -> str:
    """Convert project name to valid SQL table name."""
    if not project_name:
        raise ValueError("Project name cannot be empty")

    # Remove invalid characters, replace with underscore
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", project_name)
    # Ensure it starts with a letter or underscore
    if not re.match(r"^[a-zA-Z_]", sanitized):
        sanitized = "_" + sanitized
    # Ensure it doesn't exceed SQL identifier length limits
    if len(sanitized) > 63:  # PostgreSQL identifier length limit
        sanitized = sanitized[:63]
    return sanitized.lower()


def get_conversation_table_class(project_name: str):
    """Get or create Conversation table class for a project."""
    table_name = f"{sanitize_table_name(project_name)}_conversation"

    if table_name in _project_tables:
        return _project_tables[table_name]["conversation"]

    # Create unique class name to avoid SQLAlchemy registry collisions
    class_name = f"Conversation_{sanitize_table_name(project_name)}"

    # Define user_id column separately so we can reference it in the relationship
    user_id_col = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Create new table class dynamically with unique name
    ProjectConversation = type(
        class_name,
        (Base,),
        {
            "__tablename__": table_name,
            "id": Column(Integer, primary_key=True),
            "user_id": user_id_col,
            "title": Column(String(255)),
            "agent_id": Column(Integer, nullable=True),
            "thread_id": Column(String(512), nullable=True),
            "created_at": Column(DateTime, default=datetime.utcnow),
            "updated_at": Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
            "user": relationship("User", foreign_keys=[user_id_col]),
            # Note: 'messages' relationship is added dynamically by get_message_table_class via backref
        },
    )

    _project_tables[table_name] = {"conversation": ProjectConversation}
    return ProjectConversation


def get_message_table_class(project_name: str):
    """Get or create Message table class for a project."""
    table_name = f"{sanitize_table_name(project_name)}_messages"

    if table_name in _project_tables:
        return _project_tables[table_name]["message"]

    conv_table_name = f"{sanitize_table_name(project_name)}_conversation"
    ConversationClass = get_conversation_table_class(project_name)

    # Create unique class name to avoid SQLAlchemy registry collisions
    class_name = f"Message_{sanitize_table_name(project_name)}"

    # Create new table class dynamically with unique name
    ProjectMessage = type(
        class_name,
        (Base,),
        {
            "__tablename__": table_name,
            "id": Column(Integer, primary_key=True),
            "conversation_id": Column(Integer, ForeignKey(f"{conv_table_name}.id"), nullable=False),
            "role": Column(String(50), nullable=False),
            "content": Column(Text, nullable=False),
            "model": Column(String(100)),
            "token_count": Column(Integer),
            "created_at": Column(DateTime, default=datetime.utcnow),
            # Use backref to create 'messages' on ConversationClass automatically
            "conversation": relationship(
                ConversationClass,
                backref=backref("messages", cascade="all, delete-orphan"),
            ),
        },
    )

    _project_tables[table_name] = {"message": ProjectMessage}
    return ProjectMessage


_ensured_projects: set = set()


def ensure_project_tables_exist(project_name: str):
    """Ensure tables for a project exist in the database. Runs DDL once per project per process."""
    if not project_name:
        raise ValueError("Project name is required")

    sanitized = sanitize_table_name(project_name)
    if sanitized in _ensured_projects:
        return

    logger.debug("Creating tables for project: {}", project_name)
    db = get_db()
    ConversationClass = get_conversation_table_class(project_name)
    MessageClass = get_message_table_class(project_name)

    # Use a single connection/transaction so the conversation table FK is
    # committed and visible when the messages table (which references it) is created.
    with db.engine.begin() as conn:
        ConversationClass.__table__.create(conn, checkfirst=True)
        MessageClass.__table__.create(conn, checkfirst=True)

    # Sync missing columns on conversation table (e.g. agent_id added after initial creation)
    insp = sa_inspect(db.engine)
    conv_table = ConversationClass.__table__
    table_names = insp.get_table_names(schema=db.schema)
    if conv_table.name in table_names:
        existing_cols = {c["name"] for c in insp.get_columns(conv_table.name, schema=db.schema)}
        for col_name, col_obj in conv_table.columns.items():
            if col_name not in existing_cols:
                col_type = _get_column_type_sql(col_obj)
                # NOTE: col_name and conv_table.name come from SQLAlchemy model metadata
                # (internal/operator-controlled), not user input. Double-quoted for safety.
                # col_type is a safe SQL literal from _get_column_type_sql (e.g. "INTEGER").
                safe_schema = db.schema.replace('"', "") if db.schema else None
                safe_table = conv_table.name.replace('"', "")
                safe_col = col_name.replace('"', "")
                qualified = f'"{safe_schema}"."{safe_table}"' if safe_schema else f'"{safe_table}"'
                with db.engine.connect() as conn:
                    conn.execute(text(f'ALTER TABLE {qualified} ADD COLUMN "{safe_col}" {col_type}'))
                    conn.commit()

    _ensured_projects.add(sanitized)
    logger.debug("Tables created for project: {}", project_name)


# Database operations

_db: Optional[Database] = None


def get_db() -> Database:
    """Get or create the database instance."""
    global _db
    if _db is None:
        logger.debug("Initializing database instance")
        _db = Database()
        _db.sync_schema()  # Sync schema first to add any missing columns
        _db.create_tables()  # Then create any missing tables
    return _db


def get_or_create_user(username: str) -> User:
    """Get existing user or create new one. Username is normalized to lowercase for case-insensitive handling."""
    # Normalize username to lowercase
    normalized_username = username.lower()
    db = get_db()
    session = db.get_session()
    try:
        # Case-insensitive lookup: find user by lowercase username
        user = session.query(User).filter(func.lower(User.username) == normalized_username).first()
        if not user:
            user = User(username=normalized_username)
            session.add(user)
            session.commit()
            session.refresh(user)
        return user
    finally:
        session.close()


def list_conversations(username: str, project: Optional[str] = None, agent_id: Optional[int] = None) -> List[dict]:
    """List all conversations for a user, filtered by project and optionally by agent. Username comparison is case-insensitive."""
    if not project:
        raise ValueError("Project name is required")

    # Return empty history when message storage is disabled for this project
    from core.db.db_project import get_project_by_name

    project_data = get_project_by_name(project)
    if project_data and project_data.get("disable_message_storage", False):
        return []

    # Normalize username to lowercase for case-insensitive lookup
    normalized_username = username.lower()
    ensure_project_tables_exist(project)
    db = get_db()
    session = db.get_session()
    try:
        # Case-insensitive lookup: find user by lowercase username
        user = session.query(User).filter(func.lower(User.username) == normalized_username).first()
        if not user:
            return []

        ConversationClass = get_conversation_table_class(project)
        query = session.query(ConversationClass).filter(ConversationClass.user_id == user.id)
        if agent_id is not None:
            query = query.filter(ConversationClass.agent_id == agent_id)
        conversations = query.order_by(ConversationClass.updated_at.desc()).all()

        return [
            {
                "id": c.id,
                "title": c.title or "New Chat",
                "project": project,
                "thread_id": c.thread_id,
                "agent_id": c.agent_id,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in conversations
        ]
    finally:
        session.close()


def create_conversation(
    username: str,
    title: Optional[str] = None,
    project: Optional[str] = None,
    agent_id: Optional[int] = None,
) -> dict:
    """Create a new conversation for a user within a project. Username is normalized to lowercase."""
    if not project:
        raise ValueError("Project name is required")

    # Normalize username to lowercase (get_or_create_user will handle it, but normalize here for consistency)
    normalized_username = username.lower()
    ensure_project_tables_exist(project)
    db = get_db()
    session = db.get_session()
    try:
        user = get_or_create_user(normalized_username)

        ConversationClass = get_conversation_table_class(project)
        conversation = ConversationClass(user_id=user.id, title=title, agent_id=agent_id)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        return {
            "id": conversation.id,
            "title": conversation.title or "New Chat",
            "project": project,
            "thread_id": conversation.thread_id,
            "agent_id": conversation.agent_id,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }
    finally:
        session.close()


def get_conversation(conversation_id: int, project: str, user_id: Optional[int] = None) -> Optional[dict]:
    """Get a conversation by ID for a project.

    Returns None if not found.  If ``user_id`` is provided the conversation is
    only returned when it belongs to that user; otherwise ``None`` is returned
    so the caller can surface a 404 or 403 as appropriate.
    """
    if not project:
        raise ValueError("Project name is required")

    ensure_project_tables_exist(project)
    db = get_db()
    session = db.get_session()
    try:
        ConversationClass = get_conversation_table_class(project)
        c = session.query(ConversationClass).filter(ConversationClass.id == conversation_id).first()
        if not c:
            return None
        if user_id is not None and c.user_id != user_id:
            return None
        return {
            "id": c.id,
            "title": c.title or "New Chat",
            "thread_id": c.thread_id,
            "agent_id": c.agent_id,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
    finally:
        session.close()


def set_conversation_thread_id(conversation_id: int, thread_id: str, project: str) -> None:
    """Set the LangGraph thread_id for a conversation."""
    if not project:
        raise ValueError("Project name is required")

    ensure_project_tables_exist(project)
    db = get_db()
    session = db.get_session()
    try:
        ConversationClass = get_conversation_table_class(project)
        session.query(ConversationClass).filter(ConversationClass.id == conversation_id).update(
            {ConversationClass.thread_id: thread_id}
        )
        session.commit()
    finally:
        session.close()


def get_messages(
    conversation_id: int,
    project: str,
    user_id: Optional[int] = None,
    exclude_roles: Optional[List[str]] = None,
) -> List[dict]:
    """Get all messages for a conversation in a project.

    If ``user_id`` is provided, the conversation ownership is verified first.
    Returns an empty list when the conversation does not exist or belongs to a
    different user so that callers can distinguish access-denied from not-found
    using ``get_conversation`` with the same ``user_id``.
    """
    if not project:
        raise ValueError("Project name is required")

    ensure_project_tables_exist(project)
    db = get_db()
    session = db.get_session()
    try:
        # Ownership check: verify the conversation belongs to the requesting user
        if user_id is not None:
            ConversationClass = get_conversation_table_class(project)
            conv = session.query(ConversationClass).filter(ConversationClass.id == conversation_id).first()
            if not conv or conv.user_id != user_id:
                return []

        MessageClass = get_message_table_class(project)
        query = session.query(MessageClass).filter(MessageClass.conversation_id == conversation_id)
        if exclude_roles:
            query = query.filter(~MessageClass.role.in_(exclude_roles))
        messages = query.order_by(MessageClass.created_at.asc()).all()

        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "model": m.model,
                "token_count": m.token_count,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]
    finally:
        session.close()


def save_message(
    conversation_id: int,
    role: str,
    content: str,
    project: str,
    model: str = None,
    token_count: int = None,
) -> int:
    """Save a message to the database."""
    if not project:
        raise ValueError("Project name is required")

    # Check if message storage is disabled
    from core.db.db_project import get_project_by_name

    project_data = get_project_by_name(project)
    disable_storage = project_data.get("disable_message_storage", False) if project_data else False

    ensure_project_tables_exist(project)
    db = get_db()
    session = db.get_session()
    try:
        ConversationClass = get_conversation_table_class(project)

        # Update conversation's updated_at
        conversation = session.query(ConversationClass).filter(ConversationClass.id == conversation_id).first()

        if disable_storage:
            return 0

        if conversation:
            conversation.updated_at = datetime.utcnow()

            # Set title from first user message if not set
            if not conversation.title and role == "user":
                conversation.title = content[:50] + ("..." if len(content) > 50 else "")

        MessageClass = get_message_table_class(project)
        message = MessageClass(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            token_count=token_count,
        )
        session.add(message)

        session.commit()
        session.refresh(message)
        return message.id
    finally:
        session.close()


def delete_project_tables(project_name: str):
    """Delete all tables for a project (use with caution)."""
    if not project_name:
        raise ValueError("Project name is required")

    logger.warning("Deleting tables for project: {}", project_name)
    db = get_db()
    ConversationClass = get_conversation_table_class(project_name)
    MessageClass = get_message_table_class(project_name)

    MessageClass.__table__.drop(db.engine, checkfirst=True)
    ConversationClass.__table__.drop(db.engine, checkfirst=True)

    sanitized = sanitize_table_name(project_name)
    conv_table_name = f"{sanitized}_conversation"
    msg_table_name = f"{sanitized}_messages"
    _project_tables.pop(conv_table_name, None)
    _project_tables.pop(msg_table_name, None)
    _ensured_projects.discard(sanitized)
    logger.info("Tables deleted for project: {}", project_name)
