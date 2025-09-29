"""
Pydantic schemas for API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# New Enhanced API Schemas
class CreateThreadRequest(BaseModel):
    title: Optional[str] = None
    metadata: Optional[dict] = None


class CreateThreadResponse(BaseModel):
    thread_id: str
    title: str
    created_at: datetime
    last_message_at: datetime


class ThreadSummary(BaseModel):
    thread_id: str
    title: str
    created_at: datetime
    last_message_at: datetime
    message_count: int
    last_message_preview: Optional[str] = None


class ThreadDetails(BaseModel):
    thread_id: str
    title: str
    created_at: datetime
    last_message_at: datetime
    messages: List['MessageResponse']


class MessageResponse(BaseModel):
    message_id: str
    content: str
    is_user: bool
    message_type: str
    created_at: datetime
    metadata: Optional[dict] = None


class ChatMessageRequest(BaseModel):
    thread_id: str
    content: str
    message_type: str = "text"  # "text" | "document"
    document_urls: Optional[List[str]] = None
    metadata: Optional[dict] = None
    context: Optional[dict] = None
    response_mode: str = "sync"  # "sync" | "stream" | "async"


class AsyncReportRequest(BaseModel):
    thread_id: str
    content: str
    message_type: str = "text"
    document_urls: Optional[List[str]] = None
    metadata: Optional[dict] = None
    context: Optional[dict] = None
    priority: str = "normal"  # "low" | "normal" | "high"


class ChatMessageResponse(BaseModel):
    message_id: str
    thread_id: str
    content: str
    is_user: bool
    message_type: str
    created_at: datetime
    ai_response: Optional[str] = None
    metadata: Optional[dict] = None


class AsyncReportResponse(BaseModel):
    task_id: str
    thread_id: str
    status: str  # "queued" | "processing" | "completed" | "failed"
    message: str
    estimated_completion_time: Optional[str] = None
    created_at: datetime


class AsyncTaskStatus(BaseModel):
    task_id: str
    thread_id: str
    status: str  # "queued" | "processing" | "completed" | "failed"
    progress: Optional[float] = None  # 0.0 to 1.0
    message: str
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ResponseModeChoice(BaseModel):
    task_id: str
    response_mode: str  # "stream" | "async"
    user_id: Optional[str] = None


class InterruptionResponse(BaseModel):
    task_id: str
    thread_id: str
    status: str  # "awaiting_choice"
    message: str
    choices: List[str]  # ["stream", "async"]
    created_at: datetime


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    file_url: str
    file_type: str
    file_size: int
    uploaded_at: datetime


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    file_url: str
    file_type: str
    file_size: int
    uploaded_at: datetime


# Legacy schemas for backward compatibility
class StartThreadResponse(BaseModel):
    thread_id: str


class ThreadResponse(BaseModel):
    thread_id: str
    question_asked: bool
    question: Optional[str] = None
    answer: Optional[str] = None
    confirmed: bool
    error: bool


class ChatRequest(BaseModel):
    question: Optional[str] = None


class UpdateStateRequest(BaseModel):
    answer: str
