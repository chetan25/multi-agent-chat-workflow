"""
Thread management routes.
"""

from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import Thread, Message
from models.base import get_db
from .schemas import (
    CreateThreadRequest,
    CreateThreadResponse,
    ThreadSummary,
    ThreadDetails,
    MessageResponse,
)

router = APIRouter(prefix="/api/threads", tags=["threads"])


@router.post("", response_model=CreateThreadResponse)
async def create_thread(request: CreateThreadRequest, db: Session = Depends(get_db)):
    """Create a new thread."""
    thread_id = str(uuid4())
    now = datetime.utcnow()
    
    new_thread = Thread(
        thread_id=thread_id,
        title=request.title or "New Conversation",
        created_at=now,
        user_id=request.metadata.get("user_id") if request.metadata else None,
        meta_data=request.metadata,
    )
    
    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)
    
    return CreateThreadResponse(
        thread_id=new_thread.thread_id,
        title=new_thread.title,
        created_at=new_thread.created_at,
        last_message_at=new_thread.created_at,
    )


@router.get("", response_model=List[ThreadSummary])
async def list_threads(db: Session = Depends(get_db)):
    """List all threads with summaries."""
    threads = db.query(Thread).order_by(Thread.created_at.desc()).all()
    
    result = []
    for thread in threads:
        # Get message count and last message preview
        message_count = len(thread.messages)
        last_message_preview = None
        if thread.messages:
            last_message = max(thread.messages, key=lambda m: m.created_at)
            last_message_preview = (
                last_message.content[:100] + "..." 
                if len(last_message.content) > 100 
                else last_message.content
            )
        
        result.append(ThreadSummary(
            thread_id=thread.thread_id,
            title=thread.title,
            created_at=thread.created_at,
            last_message_at=thread.created_at,  # Using created_at as fallback
            message_count=message_count,
            last_message_preview=last_message_preview,
        ))
    
    return result


@router.get("/{thread_id}", response_model=ThreadDetails)
async def get_thread(thread_id: str, db: Session = Depends(get_db)):
    """Get thread details with messages."""
    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    messages = [
        MessageResponse(
            message_id=msg.message_id,
            content=msg.content,
            is_user=msg.is_user,
            message_type=msg.message_type,
            created_at=msg.created_at,
            metadata=msg.meta_data,
        )
        for msg in sorted(thread.messages, key=lambda m: m.created_at)
    ]
    
    return ThreadDetails(
        thread_id=thread.thread_id,
        title=thread.title,
        created_at=thread.created_at,
        last_message_at=thread.created_at,  # Using created_at as fallback
        messages=messages,
    )


@router.delete("/{thread_id}")
async def delete_thread(thread_id: str, db: Session = Depends(get_db)):
    """Delete a thread."""
    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    db.delete(thread)
    db.commit()
    
    return {"success": True, "message": "Thread deleted successfully"}


@router.get("/{thread_id}/messages", response_model=List[MessageResponse])
async def get_thread_messages(thread_id: str, db: Session = Depends(get_db)):
    """Get all messages for a thread."""
    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    messages = [
        MessageResponse(
            message_id=msg.message_id,
            content=msg.content,
            is_user=msg.is_user,
            message_type=msg.message_type,
            created_at=msg.created_at,
            metadata=msg.meta_data,
        )
        for msg in sorted(thread.messages, key=lambda m: m.created_at)
    ]
    
    return messages
