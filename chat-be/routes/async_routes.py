"""
Async task management routes for long-running operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from models import AsyncTask, Thread, Message
from models.base import get_db
from .schemas import (
    AsyncReportRequest,
    AsyncReportResponse,
    AsyncTaskStatus,
     ResponseModeChoice,
    InterruptionResponse,
)

router = APIRouter(prefix="/api/async", tags=["async"])


@router.post("/report", response_model=InterruptionResponse)
async def create_async_report(
    request: AsyncReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create an async report generation task with interruption for user choice."""
    # Verify thread exists
    thread = db.query(Thread).filter(Thread.thread_id == request.thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Create task ID
    task_id = str(uuid4())
    now = datetime.utcnow()
    
    # Create async task record in awaiting_choice status
    async_task = AsyncTask(
        task_id=task_id,
        thread_id=request.thread_id,
        user_id=request.metadata.get("user_id") if request.metadata else None,
        status="awaiting_choice",
        progress=0.0,
        message="Awaiting your choice for response mode",
        workflow_type="report_researcher",
        priority=request.priority,
        created_at=now,
        updated_at=now
    )
    
    db.add(async_task)
    
    # Create user message
    user_message_id = str(uuid4())
    user_message = Message(
        message_id=user_message_id,
        thread_id=request.thread_id,
        content=request.content,
        is_user=True,
        message_type=request.message_type,
        created_at=now,
        meta_data={
            **(request.metadata or {}),
            "async_task_id": task_id,
            "response_mode": "pending_choice"
        }
    )
    
    db.add(user_message)
    
    # Create AI interruption message
    ai_message_id = str(uuid4())
    ai_message = Message(
        message_id=ai_message_id,
        thread_id=request.thread_id,
        content="I understand you want a report generated. How would you like to receive the response?\n\n1. **Streaming Response**: Get real-time updates as I generate the report\n2. **Async Response**: Get the complete report when finished (you can continue chatting meanwhile)\n\nPlease choose your preferred response mode.",
        is_user=False,
        message_type="text",
        created_at=now,
        meta_data={
            "async_task_id": task_id,
            "interruption": True,
            "awaiting_choice": True,
            "choices": ["stream", "async"]
        }
    )
    
    db.add(ai_message)
    db.commit()
    db.refresh(async_task)
    
    return InterruptionResponse(
        task_id=task_id,
        thread_id=request.thread_id,
        status="awaiting_choice",
        message="Please choose your response mode: streaming or async",
        choices=["stream", "async"],
        created_at=now
    )


@router.post("/choice", response_model=AsyncReportResponse)
async def handle_response_mode_choice(
    choice: ResponseModeChoice,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle user's choice for response mode (stream or async)."""
    # Get the task
    task = db.query(AsyncTask).filter(AsyncTask.task_id == choice.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != "awaiting_choice":
        raise HTTPException(
            status_code=400, 
            detail=f"Task is not awaiting choice. Current status: {task.status}"
        )
    
    now = datetime.utcnow()
    
    # Create user choice message
    choice_message_id = str(uuid4())
    choice_message = Message(
        message_id=choice_message_id,
        thread_id=task.thread_id,
        content=f"I choose {choice.response_mode} response mode",
        is_user=True,
        message_type="text",
        created_at=now,
        meta_data={
            "async_task_id": choice.task_id,
            "response_mode": choice.response_mode,
            "user_choice": True
        }
    )
    
    db.add(choice_message)
    
    if choice.response_mode == "stream":
        # For streaming, we should redirect to streaming endpoint
        # The frontend should handle this by calling the streaming endpoint directly
        # We don't need to create a background task for streaming
        
        # Update task status to indicate streaming mode
        task.status = "streaming"
        task.progress = 0.0
        task.message = "Streaming report generation requested"
        task.updated_at = now
        db.commit()
        
        return AsyncReportResponse(
            task_id=choice.task_id,
            thread_id=task.thread_id,
            status="streaming",
            message="Please use the streaming endpoint to receive real-time updates.",
            estimated_completion_time=None,
            created_at=now
        )
        
    else:  # async
        # For async, start background processing
        task.status = "queued"
        task.progress = 0.0
        task.message = "Report generation queued for async processing"
        task.updated_at = now
        
        # Create AI confirmation message
        ai_message_id = str(uuid4())
        ai_message = Message(
            message_id=ai_message_id,
            thread_id=task.thread_id,
            content="Perfect! I'll generate your report in the background. You can continue chatting while I work on it. I'll notify you when it's ready.",
            is_user=False,
            message_type="text",
            created_at=now,
            meta_data={
                "async_task_id": choice.task_id,
                "response_mode": "async",
                "confirmation": True
            }
        )
        
        db.add(ai_message)
        db.commit()
        
        # Start background task for async processing
        background_tasks.add_task(
            process_async_report,
            choice.task_id,
            task.thread_id,
            task.user_id
        )
        
        # Calculate estimated completion time
        estimated_time = now + timedelta(minutes=7)
        
        return AsyncReportResponse(
            task_id=choice.task_id,
            thread_id=task.thread_id,
            status="queued",
            message="Report generation queued. You can continue chatting while it processes.",
            estimated_completion_time=estimated_time.isoformat(),
            created_at=now
        )


@router.get("/task/{task_id}", response_model=AsyncTaskStatus)
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """Get the status of an async task."""
    task = db.query(AsyncTask).filter(AsyncTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return AsyncTaskStatus(
        task_id=task.task_id,
        thread_id=task.thread_id,
        status=task.status,
        progress=task.progress,
        message=task.message,
        result=task.result,
        error=task.error,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.get("/thread/{thread_id}/tasks", response_model=List[AsyncTaskStatus])
async def get_thread_tasks(thread_id: str, db: Session = Depends(get_db)):
    """Get all async tasks for a thread."""
    tasks = db.query(AsyncTask).filter(
        AsyncTask.thread_id == thread_id
    ).order_by(AsyncTask.created_at.desc()).all()
    
    return [
        AsyncTaskStatus(
            task_id=task.task_id,
            thread_id=task.thread_id,
            status=task.status,
            progress=task.progress,
            message=task.message,
            result=task.result,
            error=task.error,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
        for task in tasks
    ]


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str, db: Session = Depends(get_db)):
    """Cancel an async task (if it's still queued or processing)."""
    task = db.query(AsyncTask).filter(AsyncTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status in ["completed", "failed"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel task with status: {task.status}"
        )
    
    task.status = "cancelled"
    task.message = "Task cancelled by user"
    task.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"success": True, "message": "Task cancelled successfully"}


async def process_streaming_report(
    task_id: str,
    thread_id: str,
    user_id: str
):
    """Background task to process streaming report generation."""
    from models.base import SessionLocal
    from workflows.supervisor_workflow import create_supervisor_workflow
    
    db = SessionLocal()
    try:
        # Get the task
        task = db.query(AsyncTask).filter(AsyncTask.task_id == task_id).first()
        if not task:
            return
        
        # Get the original user message
        user_message = db.query(Message).filter(
            Message.thread_id == thread_id,
            Message.is_user == True
        ).filter(
            Message.meta_data.op('->>')('async_task_id') == task_id
        ).first()
        
        if not user_message:
            return
        
        content = user_message.content
        
        # Update status to processing
        task.status = "processing"
        task.progress = 0.1
        task.message = "Starting streaming report generation..."
        task.updated_at = datetime.utcnow()
        db.commit()
        
        # Get supervisor workflow
        supervisor_workflow = create_supervisor_workflow()
        
        # Load conversation history for context
        conversation_history = []
        recent_messages = db.query(Message).filter(
            Message.thread_id == thread_id
        ).order_by(Message.created_at.desc()).limit(10).all()
        
        for msg in reversed(recent_messages):
            conversation_history.append({
                "role": "user" if msg.is_user else "assistant",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "message_type": msg.message_type
            })
        
        # Prepare workflow input
        workflow_input = {
            "message": content,
            "user_id": user_id,
            "thread_id": thread_id,
            "conversation_history": conversation_history
        }
        
        # Prepare config with threadID
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Update progress
        task.progress = 0.3
        task.message = "Analyzing requirements and gathering data..."
        task.updated_at = datetime.utcnow()
        db.commit()
        
        # Simulate some processing time for demo
        await asyncio.sleep(2)
        
        # Update progress
        task.progress = 0.6
        task.message = "Generating comprehensive report..."
        task.updated_at = datetime.utcnow()
        db.commit()
        
        # Stream supervisor workflow for real-time updates
        result = None
        async for chunk in supervisor_workflow.astream(workflow_input, config=config):
            # Process each chunk and update progress
            for node_name, node_data in chunk.items():
                if node_name == "analyze_intent":
                    task.progress = 0.4
                    task.message = "Analyzing requirements and routing request..."
                    task.updated_at = datetime.utcnow()
                    db.commit()
                    
                elif node_name == "report_researcher":
                    task.progress = 0.7
                    task.message = "Generating comprehensive report..."
                    task.updated_at = datetime.utcnow()
                    db.commit()
                    
                elif node_name == "format_response":
                    # This is the final chunk with the complete response
                    result = node_data
                    task.progress = 0.9
                    task.message = "Finalizing report..."
                    task.updated_at = datetime.utcnow()
                    db.commit()
        
        # Simulate final processing
        await asyncio.sleep(1)
        
        # Extract response
        ai_response = result.get("response", "Report generation completed.")
        workflow_used = result.get("workflow_used", "report_researcher")
        analysis_type = result.get("analysis_type", "general")
        
        # Create AI message
        ai_message_id = str(uuid4())
        now = datetime.utcnow()
        
        ai_message = Message(
            message_id=ai_message_id,
            thread_id=thread_id,
            content=ai_response,
            is_user=False,
            message_type="text",
            created_at=now,
            meta_data={
                "async_task_id": task_id,
                "workflow_used": workflow_used,
                "analysis_type": analysis_type,
                "response_mode": "stream"
            }
        )
        
        db.add(ai_message)
        
        # Update task as completed
        task.status = "completed"
        task.progress = 1.0
        task.message = "Streaming report generation completed successfully"
        task.result = ai_response
        task.completed_at = now
        task.updated_at = now
        
        db.commit()
        
    except Exception as e:
        # Update task as failed
        task.status = "failed"
        task.message = f"Streaming report generation failed: {str(e)}"
        task.error = str(e)
        task.updated_at = datetime.utcnow()
        db.commit()
        
    finally:
        db.close()


async def process_async_report(
    task_id: str,
    thread_id: str,
    user_id: str
):
    """Background task to process async report generation."""
    from models.base import SessionLocal
    from workflows.supervisor_workflow import create_supervisor_workflow
    
    db = SessionLocal()
    try:
        # Get the task
        task = db.query(AsyncTask).filter(AsyncTask.task_id == task_id).first()
        if not task:
            return
        
        # Get the original user message
        user_message = db.query(Message).filter(
            Message.thread_id == thread_id,
            Message.is_user == True
        ).filter(
            Message.meta_data.op('->>')('async_task_id') == task_id
        ).first()
        
        if not user_message:
            return
        
        content = user_message.content
        
        # Update status to processing
        task.status = "processing"
        task.progress = 0.1
        task.message = "Starting async report generation..."
        task.updated_at = datetime.utcnow()
        db.commit()
        
        # Get supervisor workflow
        supervisor_workflow = create_supervisor_workflow()
        
        # Load conversation history for context
        conversation_history = []
        recent_messages = db.query(Message).filter(
            Message.thread_id == thread_id
        ).order_by(Message.created_at.desc()).limit(10).all()
        
        for msg in reversed(recent_messages):
            conversation_history.append({
                "role": "user" if msg.is_user else "assistant",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "message_type": msg.message_type
            })
        
        # Prepare workflow input
        workflow_input = {
            "message": content,
            "user_id": user_id,
            "thread_id": thread_id,
            "conversation_history": conversation_history
        }
        
        # Prepare config with threadID
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Update progress
        task.progress = 0.3
        task.message = "Analyzing requirements and gathering data..."
        task.updated_at = datetime.utcnow()
        db.commit()
        
        # Simulate some processing time for demo
        await asyncio.sleep(2)
        
        # Update progress
        task.progress = 0.6
        task.message = "Generating comprehensive report..."
        task.updated_at = datetime.utcnow()
        db.commit()
        
        # Invoke supervisor workflow
        result = await supervisor_workflow.ainvoke(workflow_input, config=config)
        
        # Update progress
        task.progress = 0.9
        task.message = "Finalizing report..."
        task.updated_at = datetime.utcnow()
        db.commit()
        
        # Simulate final processing
        await asyncio.sleep(1)
        
        # Extract response
        ai_response = result.get("response", "Report generation completed.")
        workflow_used = result.get("workflow_used", "report_researcher")
        analysis_type = result.get("analysis_type", "general")
        
        # Extract report title from content or user message
        def extract_report_title(content: str, user_message: str) -> str:
            """Extract report title from content or generate from user message"""
            import re
            
            # First, try to extract title from markdown headers in the content
            header_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if header_match:
                return header_match.group(1).strip()
            
            # Try to extract from other markdown patterns
            alt_header_match = re.search(r'^##\s+(.+)$', content, re.MULTILINE)
            if alt_header_match:
                return alt_header_match.group(1).strip()
            
            # Try to extract from the first line if it looks like a title
            first_line = content.split('\n')[0].strip()
            if first_line and len(first_line) < 100 and '.' not in first_line:
                return first_line
            
            # Fallback: generate title from user message
            user_words = user_message.lower()
            if 'report about' in user_words:
                topic = user_message.split('report about', 1)[1].strip()
                return f"Report: {topic}" if topic else "Research Report"
            elif 'report on' in user_words:
                topic = user_message.split('report on', 1)[1].strip()
                return f"Report: {topic}" if topic else "Research Report"
            elif 'analysis of' in user_words:
                topic = user_message.split('analysis of', 1)[1].strip()
                return f"Analysis: {topic}" if topic else "Analysis Report"
            elif 'generate' in user_words and 'report' in user_words:
                words = user_message.split()
                topic_words = []
                for i, word in enumerate(words):
                    if word.lower() in ['about', 'on', 'regarding', 'concerning', 'for']:
                        topic_words = words[i+1:i+6]
                        break
                topic = ' '.join(topic_words).replace('?', '').replace('!', '').strip()
                return f"Report: {topic}" if topic else "Research Report"
            
            # Final fallback
            return "Research Report"
        
        report_title = extract_report_title(ai_response, content)
        
        print(f"DEBUG: Async report result keys: {result.keys()}")
        print(f"DEBUG: Async report response length: {len(ai_response) if ai_response else 0}")
        print(f"DEBUG: Async report response preview: {ai_response[:200] if ai_response else 'EMPTY'}...")
        print(f"DEBUG: Extracted report title: {report_title}")
        logger.info(f"DEBUG: Async report result keys: {result.keys()}")
        logger.info(f"DEBUG: Async report response length: {len(ai_response) if ai_response else 0}")
        logger.info(f"DEBUG: Async report response preview: {ai_response[:200] if ai_response else 'EMPTY'}...")
        logger.info(f"DEBUG: Extracted report title: {report_title}")
        
        # Create AI message with proper metadata for accordion display
        ai_message_id = str(uuid4())
        now = datetime.utcnow()
        
        ai_message = Message(
            message_id=ai_message_id,
            thread_id=thread_id,
            content=ai_response,
            is_user=False,
            message_type="text",
            created_at=now,
            meta_data={
                "async_task_id": task_id,
                "workflow_used": workflow_used,
                "analysis_type": analysis_type,
                "response_mode": "async",
                "completed_task": True,
                "report_title": report_title,
                "original_task": {
                    "task_id": task_id,
                    "workflow_used": workflow_used,
                    "response_mode": "async"
                }
            }
        )
        
        db.add(ai_message)
        
        # Update task as completed with proper result
        task.status = "completed"
        task.progress = 1.0
        task.message = "Async report generation completed successfully"
        task.result = ai_response
        task.completed_at = now
        task.updated_at = now
        
        db.commit()
        
        print(f"DEBUG: Async report completed for task {task_id}")
        print(f"DEBUG: Report content length: {len(ai_response)}")
        print(f"DEBUG: Message saved with ID: {ai_message_id}")
        
    except Exception as e:
        # Update task as failed
        task.status = "failed"
        task.message = f"Async report generation failed: {str(e)}"
        task.error = str(e)
        task.updated_at = datetime.utcnow()
        db.commit()
        
    finally:
        db.close()
