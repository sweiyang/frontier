from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from conduit.core.db.db import Base, Database


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user")
    owned_projects = relationship("Project", back_populates="owner")  # Projects user created
    projects = relationship("Project", secondary="project_members", back_populates="members")  # All projects user is in


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project = Column(String(255), nullable=True)  # Project name from URL
    title = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(50), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    model = Column(String(100))  # e.g., "gpt-4", "claude-3"
    token_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


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
    """Get existing user or create new one."""
    db = get_db()
    session = db.get_session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            user = User(username=username)
            session.add(user)
            session.commit()
            session.refresh(user)
        return user
    finally:
        session.close()


def list_conversations(username: str, project: Optional[str] = None) -> List[dict]:
    """List all conversations for a user, optionally filtered by project."""
    db = get_db()
    session = db.get_session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return []
        
        query = session.query(Conversation).filter(
            Conversation.user_id == user.id
        )
        
        # Filter by project if provided
        if project is not None:
            query = query.filter(Conversation.project == project)
        
        conversations = query.order_by(Conversation.updated_at.desc()).all()
        
        return [
            {
                "id": c.id,
                "title": c.title or "New Chat",
                "project": c.project,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat()
            }
            for c in conversations
        ]
    finally:
        session.close()


def create_conversation(username: str, title: Optional[str] = None, project: Optional[str] = None) -> dict:
    """Create a new conversation for a user within a project."""
    db = get_db()
    session = db.get_session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            user = User(username=username)
            session.add(user)
            session.commit()
            session.refresh(user)
        
        conversation = Conversation(
            user_id=user.id,
            title=title,
            project=project
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        
        return {
            "id": conversation.id,
            "title": conversation.title or "New Chat",
            "project": conversation.project,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat()
        }
    finally:
        session.close()


def get_messages(conversation_id: int) -> List[dict]:
    """Get all messages for a conversation."""
    db = get_db()
    session = db.get_session()
    try:
        messages = session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()
        
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
    model: str = None,
    token_count: int = None
) -> int:
    """Save a message to the database."""
    db = get_db()
    session = db.get_session()
    try:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            token_count=token_count
        )
        session.add(message)
        
        # Update conversation's updated_at
        conversation = session.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
            
            # Set title from first user message if not set
            if not conversation.title and role == "user":
                conversation.title = content[:50] + ("..." if len(content) > 50 else "")
        
        session.commit()
        session.refresh(message)
        return message.id
    finally:
        session.close()

