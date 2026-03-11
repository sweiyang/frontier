from datetime import datetime
from typing import List, Optional, Dict, Type
import re
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from core.db.db import Base, Database


# Association table for many-to-many relationship between users and projects
# Defined here (before User class) to ensure it's registered in metadata before mapper configuration
project_members = Table(
    "project_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("role", String(50), default="member"),  # owner, admin, member
    Column("joined_at", DateTime, default=datetime.utcnow)
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Note: relationships to project-specific tables are handled dynamically
    owned_projects = relationship("Project", back_populates="owner")
    projects = relationship("Project", secondary=project_members, back_populates="members")


# Registry to cache dynamically created table classes
_project_tables: Dict[str, Dict[str, Type]] = {}


def sanitize_table_name(project_name: str) -> str:
    """Convert project name to valid SQL table name."""
    if not project_name:
        raise ValueError("Project name cannot be empty")
    
    # Remove invalid characters, replace with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', project_name)
    # Ensure it starts with a letter or underscore
    if not re.match(r'^[a-zA-Z_]', sanitized):
        sanitized = '_' + sanitized
    # Ensure it doesn't exceed SQL identifier length limits
    if len(sanitized) > 63:  # PostgreSQL identifier length limit
        sanitized = sanitized[:63]
    return sanitized.lower()


def get_conversation_table_class(project_name: str):
    """Get or create Conversation table class for a project."""
    table_name = f"{sanitize_table_name(project_name)}_conversation"
    
    if table_name in _project_tables:
        return _project_tables[table_name]['conversation']
    
    # Create new table class dynamically
    class ProjectConversation(Base):
        __tablename__ = table_name
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        title = Column(String(255))
        thread_id = Column(String(512), nullable=True)  # LangGraph thread ID for agent continuity
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        user = relationship("User", foreign_keys=[user_id])
        messages = relationship("ProjectMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    _project_tables[table_name] = {'conversation': ProjectConversation}
    return ProjectConversation


def get_message_table_class(project_name: str):
    """Get or create Message table class for a project."""
    table_name = f"{sanitize_table_name(project_name)}_messages"
    
    if table_name in _project_tables:
        return _project_tables[table_name]['message']
    
    conv_table_name = f"{sanitize_table_name(project_name)}_conversation"
    ConversationClass = get_conversation_table_class(project_name)
    
    # Create new table class dynamically
    class ProjectMessage(Base):
        __tablename__ = table_name
        
        id = Column(Integer, primary_key=True)
        conversation_id = Column(Integer, ForeignKey(f"{conv_table_name}.id"), nullable=False)
        role = Column(String(50), nullable=False)
        content = Column(Text, nullable=False)
        model = Column(String(100))
        token_count = Column(Integer)
        created_at = Column(DateTime, default=datetime.utcnow)
        
        conversation = relationship(ConversationClass, back_populates="messages")
    
    _project_tables[table_name] = {'message': ProjectMessage}
    return ProjectMessage


_ensured_projects: set = set()


def ensure_project_tables_exist(project_name: str):
    """Ensure tables for a project exist in the database. Runs DDL once per project per process."""
    if not project_name:
        raise ValueError("Project name is required")
    
    sanitized = sanitize_table_name(project_name)
    if sanitized in _ensured_projects:
        return
    
    db = get_db()
    ConversationClass = get_conversation_table_class(project_name)
    MessageClass = get_message_table_class(project_name)
    
    ConversationClass.__table__.create(db.engine, checkfirst=True)
    MessageClass.__table__.create(db.engine, checkfirst=True)
    _ensured_projects.add(sanitized)


# Database operations

_db: Optional[Database] = None


def get_db() -> Database:
    """Get or create the database instance."""
    global _db
    if _db is None:
        _db = Database()
        _db.create_tables()
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


def list_conversations(username: str, project: Optional[str] = None) -> List[dict]:
    """List all conversations for a user, filtered by project. Username comparison is case-insensitive."""
    if not project:
        raise ValueError("Project name is required")
    
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
        conversations = session.query(ConversationClass).filter(
            ConversationClass.user_id == user.id
        ).order_by(ConversationClass.updated_at.desc()).all()
        
        return [
            {
                "id": c.id,
                "title": c.title or "New Chat",
                "project": project,
                "thread_id": c.thread_id,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat()
            }
            for c in conversations
        ]
    finally:
        session.close()


def create_conversation(username: str, title: Optional[str] = None, project: Optional[str] = None) -> dict:
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
        conversation = ConversationClass(
            user_id=user.id,
            title=title
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        
        return {
            "id": conversation.id,
            "title": conversation.title or "New Chat",
            "project": project,
            "thread_id": conversation.thread_id,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat()
        }
    finally:
        session.close()


def get_conversation(conversation_id: int, project: str) -> Optional[dict]:
    """Get a conversation by ID for a project. Returns None if not found."""
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
        return {
            "id": c.id,
            "title": c.title or "New Chat",
            "thread_id": c.thread_id,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat()
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


def get_messages(conversation_id: int, project: str) -> List[dict]:
    """Get all messages for a conversation in a project."""
    if not project:
        raise ValueError("Project name is required")
    
    ensure_project_tables_exist(project)
    db = get_db()
    session = db.get_session()
    try:
        MessageClass = get_message_table_class(project)
        messages = session.query(MessageClass).filter(
            MessageClass.conversation_id == conversation_id
        ).order_by(MessageClass.created_at.asc()).all()
        
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "model": m.model,
                "token_count": m.token_count,
                "created_at": m.created_at.isoformat()
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
    token_count: int = None
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
        conversation = session.query(ConversationClass).filter(
            ConversationClass.id == conversation_id
        ).first()
        
        if conversation:
            conversation.updated_at = datetime.utcnow()
            
            # Set title from first user message if not set
            if not conversation.title and role == "user":
                conversation.title = content[:50] + ("..." if len(content) > 50 else "")
        
        if disable_storage:
            session.commit()
            return 0
            
        MessageClass = get_message_table_class(project)
        message = MessageClass(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            token_count=token_count
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
    
    db = get_db()
    ConversationClass = get_conversation_table_class(project_name)
    MessageClass = get_message_table_class(project_name)
    
    # Drop tables
    MessageClass.__table__.drop(db.engine, checkfirst=True)
    ConversationClass.__table__.drop(db.engine, checkfirst=True)
    
    # Remove from caches
    sanitized = sanitize_table_name(project_name)
    conv_table_name = f"{sanitized}_conversation"
    msg_table_name = f"{sanitized}_messages"
    _project_tables.pop(conv_table_name, None)
    _project_tables.pop(msg_table_name, None)
    _ensured_projects.discard(sanitized)
