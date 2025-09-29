"""
Message model for the chat application.
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class Message(Base):
    __tablename__ = "messages"
    
    message_id = Column(String, primary_key=True, index=True)
    thread_id = Column(String, ForeignKey("threads.thread_id"), index=True)
    content = Column(Text, nullable=False)
    is_user = Column(Boolean, default=False)
    message_type = Column(String, default="text")  # "text" | "document"
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, nullable=True)
    document_id = Column(String, ForeignKey("documents.document_id"), nullable=True)
    
    # Relationships
    thread = relationship("Thread", back_populates="messages")
    document = relationship("Document", back_populates="messages")
