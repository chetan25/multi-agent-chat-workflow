"""
Legacy routes for backward compatibility.
"""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import Thread
from models.base import get_db
from .schemas import (
    StartThreadResponse,
    ThreadResponse,
    ChatRequest,
    UpdateStateRequest,
)

router = APIRouter(tags=["legacy"])


@router.post("/start_thread", response_model=StartThreadResponse)
async def start_thread(db: Session = Depends(get_db)):
    """Legacy endpoint to start a thread."""
    thread_id = str(uuid4())
    new_thread = Thread(
        thread_id=thread_id,
        title="New Conversation",
    )
    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)
    return StartThreadResponse(thread_id=new_thread.thread_id)


@router.post("/ask_question/{thread_id}", response_model=ThreadResponse)
async def ask_question(
    thread_id: str, request: ChatRequest, db: Session = Depends(get_db)
):
    """Legacy endpoint to ask a question."""
    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread ID does not exist.")
    
    if not request.question:
        raise HTTPException(status_code=400, detail="Missing question.")
    
    # Placeholder response for now
    response_state = [None, {"answer": f"AI Response to: {request.question}", "error": False}]
    
    # Update thread with legacy fields (these would need to be added to the model)
    # For now, we'll store in metadata
    if not thread.meta_data:
        thread.meta_data = {}
    
    thread.meta_data.update({
        "question_asked": True,
        "question": request.question,
        "answer": response_state[1].get("answer"),
        "confirmed": False,
        "error": response_state[1].get("error", False),
    })
    
    db.commit()
    
    return ThreadResponse(
        thread_id=thread.thread_id,
        question_asked=thread.meta_data.get("question_asked", False),
        question=thread.meta_data.get("question"),
        answer=thread.meta_data.get("answer"),
        confirmed=thread.meta_data.get("confirmed", False),
        error=thread.meta_data.get("error", False),
    )


@router.patch("/edit_state/{thread_id}", response_model=ThreadResponse)
async def edit_state(
    thread_id: str, request: UpdateStateRequest, db: Session = Depends(get_db)
):
    """Legacy endpoint to edit thread state."""
    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread ID does not exist.")
    
    if not thread.meta_data or not thread.meta_data.get("question_asked"):
        raise HTTPException(
            status_code=400, detail="Cannot edit a thread without a question."
        )
    
    if thread.meta_data.get("confirmed"):
        raise HTTPException(
            status_code=400, detail="Cannot edit a thread after it has been confirmed."
        )
    
    # Update answer in metadata
    thread.meta_data["answer"] = request.answer
    db.commit()
    
    return ThreadResponse(
        thread_id=thread.thread_id,
        question_asked=thread.meta_data.get("question_asked", False),
        question=thread.meta_data.get("question"),
        answer=thread.meta_data.get("answer"),
        confirmed=thread.meta_data.get("confirmed", False),
        error=thread.meta_data.get("error", False),
    )


@router.post("/confirm/{thread_id}", response_model=ThreadResponse)
async def confirm(thread_id: str, db: Session = Depends(get_db)):
    """Legacy endpoint to confirm a thread."""
    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread ID does not exist.")
    
    if not thread.meta_data or not thread.meta_data.get("question_asked"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm thread {thread_id} as no question has been asked.",
        )
    
    # Placeholder response for now
    response_state = {"confirmed": True, "answer": thread.meta_data.get("answer")}
    
    thread.meta_data.update({
        "confirmed": bool(response_state.get("confirmed")),
        "answer": response_state.get("answer"),
    })
    
    db.commit()
    
    return ThreadResponse(
        thread_id=thread.thread_id,
        question_asked=thread.meta_data.get("question_asked", False),
        question=thread.meta_data.get("question"),
        answer=thread.meta_data.get("answer"),
        confirmed=thread.meta_data.get("confirmed", False),
        error=thread.meta_data.get("error", False),
    )


@router.get("/sessions", response_model=list[ThreadResponse])
async def list_sessions(db: Session = Depends(get_db)):
    """Legacy endpoint to list sessions."""
    threads = db.query(Thread).all()
    return [
        ThreadResponse(
            thread_id=thread.thread_id,
            question_asked=thread.meta_data.get("question_asked", False) if thread.meta_data else False,
            question=thread.meta_data.get("question") if thread.meta_data else None,
            answer=thread.meta_data.get("answer") if thread.meta_data else None,
            confirmed=thread.meta_data.get("confirmed", False) if thread.meta_data else False,
            error=thread.meta_data.get("error", False) if thread.meta_data else False,
        )
        for thread in threads
    ]
