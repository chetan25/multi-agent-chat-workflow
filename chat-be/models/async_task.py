"""
Async task model for tracking long-running operations.
"""

from sqlalchemy import Column, String, DateTime, Float, Text, Boolean
from datetime import datetime

from .base import Base


class AsyncTask(Base):
    __tablename__ = "async_tasks"
    
    task_id = Column(String, primary_key=True, index=True)
    thread_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, default="queued")  # queued, awaiting_choice, processing, completed, failed
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    message = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    workflow_type = Column(String, nullable=True)  # report_researcher, etc.
    priority = Column(String, default="normal")  # low, normal, high
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
