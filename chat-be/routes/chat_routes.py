"""
Chat message routes.
"""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import asyncio

from models import Thread, Message
from models.base import get_db
from .schemas import ChatMessageRequest, ChatMessageResponse, AsyncReportRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def send_chat_message(
    request: ChatMessageRequest, 
    db: Session = Depends(get_db),
    fastapi_request: Request = None
):
    """Send a chat message using the supervisor workflow."""
    print(f"DEBUG: Request received - response_mode: '{request.response_mode}', content: '{request.content}'")
    
    # Verify thread exists
    thread = db.query(Thread).filter(Thread.thread_id == request.thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Check if this should be handled as async
    if request.response_mode == "async":
        # Redirect to async endpoint for report generation
        from .async_routes import create_async_report
        from fastapi import BackgroundTasks
        
        async_request = AsyncReportRequest(
            thread_id=request.thread_id,
            content=request.content,
            message_type=request.message_type,
            document_urls=request.document_urls,
            metadata=request.metadata,
            context=request.context,
            priority="normal"
        )
        
        # Create a mock background tasks object
        background_tasks = BackgroundTasks()
        
        return await create_async_report(async_request, background_tasks, db)
    
    # Check if this should be handled as streaming
    if request.response_mode == "stream":
        print(f"DEBUG: Streaming mode detected for request: {request.content}")
        # Return streaming response directly
        supervisor_workflow = fastapi_request.app.state.supervisor_workflow
        return StreamingResponse(
            stream_chat_response(request, supervisor_workflow, db),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
    
    # Get supervisor workflow from app state
    supervisor_workflow = fastapi_request.app.state.supervisor_workflow
    
    # Create user message
    user_message_id = str(uuid4())
    now = datetime.utcnow()
    
    user_message = Message(
        message_id=user_message_id,
        thread_id=request.thread_id,
        content=request.content,
        is_user=True,
        message_type=request.message_type,
        created_at=now,
        meta_data=request.metadata,
    )
    
    db.add(user_message)
    
    # Update thread title if it's the first user message
    if not thread.title or thread.title == "New Conversation":
        thread.title = (
            request.content[:50] + "..." 
            if len(request.content) > 50 
            else request.content
        )
    
    # Update thread's last message timestamp
    thread.created_at = now  # Using created_at as fallback for last_message_at
    
    db.commit()
    db.refresh(user_message)
    
    try:
        # Get conversation history for context
        conversation_history = []
        recent_messages = db.query(Message).filter(
            Message.thread_id == request.thread_id
        ).order_by(Message.created_at.desc()).limit(10).all()
        
        for msg in reversed(recent_messages):
            conversation_history.append({
                "role": "user" if msg.is_user else "assistant",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "message_type": msg.message_type
            })
        
        # Prepare input for supervisor workflow
        workflow_input = {
            "message": request.content,
            "user_id": request.metadata.get("user_id") if request.metadata else None,
            "thread_id": request.thread_id,
            "conversation_history": conversation_history
        }
        
        # Prepare config with threadID for LangGraph checkpointing
        config = {
            "configurable": {
                "thread_id": request.thread_id
            }
        }
        
        # Invoke supervisor workflow with config
        result = await supervisor_workflow.ainvoke(workflow_input, config=config)
        
        # Extract AI response
        ai_response = result.get("response", "I'm sorry, I couldn't process your request.")
        workflow_used = result.get("workflow_used", "unknown")
        confidence_score = result.get("confidence_score", 0.5)
        analysis_type = result.get("analysis_type")
        
        # Create AI message
        ai_message_id = str(uuid4())
        ai_message = Message(
            message_id=ai_message_id,
            thread_id=request.thread_id,
            content=ai_response,
            is_user=False,
            message_type="text",
            created_at=now,
            meta_data={
                "response_to": user_message_id,
                "workflow_used": workflow_used,
                "confidence_score": confidence_score,
                "analysis_type": analysis_type,
                "error": result.get("error", False),
                "error_message": result.get("error_message")
            },
        )
        
        db.add(ai_message)
        db.commit()
        db.refresh(ai_message)
        
        return ChatMessageResponse(
            message_id=user_message_id,
            thread_id=request.thread_id,
            content=request.content,
            is_user=True,
            message_type=request.message_type,
            created_at=now,
            ai_response=ai_response,
            meta_data={
                **(request.metadata or {}),
                "workflow_used": workflow_used,
                "confidence_score": confidence_score,
                "analysis_type": analysis_type
            },
        )
        
    except Exception as e:
        # Fallback response in case of workflow error
        ai_response = f"I encountered an error while processing your message: {str(e)}"
        
        # Create AI message with error
        ai_message_id = str(uuid4())
        ai_message = Message(
            message_id=ai_message_id,
            thread_id=request.thread_id,
            content=ai_response,
            is_user=False,
            message_type="text",
            created_at=now,
            meta_data={
                "response_to": user_message_id,
                "workflow_used": "error",
                "error": True,
                "error_message": str(e)
            },
        )
        
        db.add(ai_message)
        db.commit()
        db.refresh(ai_message)
        
        return ChatMessageResponse(
            message_id=user_message_id,
            thread_id=request.thread_id,
            content=request.content,
            is_user=True,
            message_type=request.message_type,
            created_at=now,
            ai_response=ai_response,
            meta_data={
                **(request.metadata or {}),
                "workflow_used": "error",
                "error": True,
                "error_message": str(e)
            },
        )


async def stream_chat_response(
    request: ChatMessageRequest,
    supervisor_workflow,
    db: Session
):
    """Stream chat responses in real-time"""
    try:
        # Save user message to database first
        user_message_id = str(uuid4())
        now = datetime.utcnow()
        
        user_message = Message(
            message_id=user_message_id,
            thread_id=request.thread_id,
            content=request.content,
            is_user=True,
            message_type=request.message_type,
            created_at=now,
            meta_data=request.metadata,
        )
        
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # Get conversation history for context
        conversation_history = []
        recent_messages = db.query(Message).filter(
            Message.thread_id == request.thread_id
        ).order_by(Message.created_at.desc()).limit(10).all()
        
        for msg in reversed(recent_messages):
            conversation_history.append({
                "role": "user" if msg.is_user else "assistant",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "message_type": msg.message_type
            })
        
        # Prepare input for supervisor workflow
        workflow_input = {
            "message": request.content,
            "user_id": request.metadata.get("user_id") if request.metadata else None,
            "thread_id": request.thread_id,
            "conversation_history": conversation_history
        }
        
        # Prepare config with threadID for LangGraph checkpointing
        config = {
            "configurable": {
                "thread_id": request.thread_id
            }
        }
        
        # Send initial metadata
        initial_chunk = {
            "type": "metadata",
            "data": {
                "thread_id": request.thread_id,
                "status": "processing",
                "message_type": request.message_type
            },
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(initial_chunk)}\n\n"
        
        # Stream the workflow execution with config
        print(f"DEBUG: Starting workflow stream with input: {workflow_input}")
        print(f"DEBUG: Config: {config}")
        async for chunk in supervisor_workflow.astream(workflow_input, config=config):
            print(f"DEBUG: Received chunk: {chunk}")
            # Process each chunk from the workflow
            for node_name, node_data in chunk.items():
                if node_name == "analyze_intent":
                    # Send intent analysis information
                    intent_chunk = {
                        "type": "metadata",
                        "data": {
                            "node": "intent_analysis",
                            "status": "analyzing_intent",
                            "routing_decision": node_data.get("routing_decision"),
                            "confidence_score": node_data.get("confidence_score")
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(intent_chunk)}\n\n"
                
                elif node_name == "simple_chat":
                    # Send simple chat progress
                    progress_chunk = {
                        "type": "metadata",
                        "data": {
                            "node": "simple_chat",
                            "status": "processing_simple_chat",
                            "workflow_used": "simple_chat"
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(progress_chunk)}\n\n"
                
                elif node_name == "report_researcher":
                    # Send report researcher progress
                    print(f"DEBUG: Report researcher node data: {node_data}")
                    print(f"DEBUG: Response in node_data: {node_data.get('response', 'NO RESPONSE')}")
                    print(f"DEBUG: Node data keys: {list(node_data.keys()) if isinstance(node_data, dict) else 'Not a dict'}")
                    
                    # Send initial progress metadata
                    progress_chunk = {
                        "type": "metadata",
                        "data": {
                            "node": "report_researcher",
                            "status": "processing_research",
                            "workflow_used": "report_researcher",
                            "analysis_type": node_data.get("analysis_type", "general")
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(progress_chunk)}\n\n"
                    
                    # Stream the report content if available
                    if "response" in node_data and node_data["response"]:
                        response_text = node_data["response"]
                        print(f"DEBUG: Streaming response text length: {len(response_text)}")
                        print(f"DEBUG: Response text preview: {response_text[:200]}...")
                        
                        # Ensure response is not empty
                        if response_text and len(response_text.strip()) > 0:
                            chunk_size = 100  # Characters per chunk for report content
                            
                            for i in range(0, len(response_text), chunk_size):
                                content_chunk = {
                                    "type": "content",
                                    "data": {
                                        "content": response_text[i:i+chunk_size],
                                        "is_partial": i + chunk_size < len(response_text),
                                        "node": "report_researcher"
                                    },
                                    "timestamp": datetime.now().isoformat()
                                }
                                yield f"data: {json.dumps(content_chunk)}\n\n"
                                
                                # Small delay for streaming effect
                                await asyncio.sleep(0.03)
                        else:
                            print(f"DEBUG: Response text is empty or whitespace only")
                            # Send error message
                            error_chunk = {
                                "type": "error",
                                "data": {
                                    "error": True,
                                    "error_message": "Report content is empty",
                                    "node": "report_researcher"
                                },
                                "timestamp": datetime.now().isoformat()
                            }
                            yield f"data: {json.dumps(error_chunk)}\n\n"
                    else:
                        print(f"DEBUG: No response found in node_data. Keys: {list(node_data.keys()) if isinstance(node_data, dict) else 'Not a dict'}")
                        print(f"DEBUG: Response value: {node_data.get('response', 'KEY NOT FOUND')}")
                        
                        # Send error message for missing response
                        error_chunk = {
                            "type": "error",
                            "data": {
                                "error": True,
                                "error_message": "No response generated from report researcher",
                                "node": "report_researcher"
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        yield f"data: {json.dumps(error_chunk)}\n\n"
                
                elif node_name == "format_response":
                    # Send the final response
                    if "response" in node_data:
                        # Stream the response content in chunks for better UX
                        response_text = node_data["response"]
                        chunk_size = 50  # Characters per chunk
                        
                        for i in range(0, len(response_text), chunk_size):
                            content_chunk = {
                                "type": "content",
                                "data": {
                                    "content": response_text[i:i+chunk_size],
                                    "is_partial": i + chunk_size < len(response_text)
                                },
                                "timestamp": datetime.now().isoformat()
                            }
                            yield f"data: {json.dumps(content_chunk)}\n\n"
                            
                            # Small delay for streaming effect
                            await asyncio.sleep(0.05)
                        
                        # Send final metadata
                        final_chunk = {
                            "type": "metadata",
                            "data": {
                                "status": "completed",
                                "full_response": response_text,
                                "workflow_used": node_data.get("workflow_used", "unknown"),
                                "confidence_score": node_data.get("confidence_score", 0.5),
                                "analysis_type": node_data.get("analysis_type"),
                                "error": node_data.get("error", False),
                                "error_message": node_data.get("error_message")
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        yield f"data: {json.dumps(final_chunk)}\n\n"
                        
                        # Save AI response to database
                        ai_message_id = str(uuid4())
                        ai_message = Message(
                            message_id=ai_message_id,
                            thread_id=request.thread_id,
                            content=response_text,
                            is_user=False,
                            message_type="text",
                            created_at=datetime.utcnow(),
                            meta_data={
                                "response_to": user_message_id,
                                "workflow_used": node_data.get("workflow_used", "unknown"),
                                "confidence_score": node_data.get("confidence_score", 0.5),
                                "analysis_type": node_data.get("analysis_type"),
                                "error": node_data.get("error", False),
                                "error_message": node_data.get("error_message"),
                                "response_mode": "stream"
                            },
                        )
                        
                        db.add(ai_message)
                        db.commit()
                        db.refresh(ai_message)
                
                elif node_name == "error_handler":
                    # Send error information
                    error_chunk = {
                        "type": "error",
                        "data": {
                            "error": True,
                            "error_message": node_data.get("error_message", "Unknown error occurred"),
                            "node": "error_handler"
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
        
        # Send end signal
        end_chunk = {
            "type": "end",
            "data": {"status": "stream_completed"},
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(end_chunk)}\n\n"
        
    except Exception as e:
        # Send error chunk
        error_chunk = {
            "type": "error",
            "data": {
                "error": True,
                "error_message": f"Streaming error: {str(e)}"
            },
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"


@router.post("/stream")
async def stream_chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None
):
    """Stream chat responses in real-time using Server-Sent Events."""
    print(f"DEBUG: Stream endpoint called with content: '{request.content}'")
    print(f"DEBUG: Request response_mode: '{request.response_mode}'")
    
    # Verify thread exists
    thread = db.query(Thread).filter(Thread.thread_id == request.thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Get supervisor workflow from app state
    supervisor_workflow = fastapi_request.app.state.supervisor_workflow
    print(f"DEBUG: Supervisor workflow obtained: {supervisor_workflow is not None}")
    
    try:
        return StreamingResponse(
            stream_chat_response(request, supervisor_workflow, db),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")


@router.post("/streaming")
async def streaming_chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None
):
    """Alternative streaming endpoint that handles response_mode parameter."""
    # Verify thread exists
    thread = db.query(Thread).filter(Thread.thread_id == request.thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Get supervisor workflow from app state
    supervisor_workflow = fastapi_request.app.state.supervisor_workflow
    
    try:
        return StreamingResponse(
            stream_chat_response(request, supervisor_workflow, db),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")


@router.post("/stream/test")
async def stream_test_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None
):
    """Test streaming endpoint with simple response."""
    async def test_stream():
        # Send initial metadata
        initial_chunk = {
            "type": "metadata",
            "data": {
                "thread_id": request.thread_id,
                "status": "processing",
                "message_type": request.message_type
            },
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(initial_chunk)}\n\n"
        
        # Send test content
        test_content = f"""
# Test Report - {request.content}

## Executive Summary
This is a test report generated for: {request.content}

## Key Findings
- Test finding 1: The system is working correctly
- Test finding 2: Streaming is functional
- Test finding 3: Report generation is operational

## Detailed Analysis
This test report demonstrates that the streaming functionality is working properly. The report contains structured content with multiple sections.

## Conclusion
The streaming report generation system is functioning as expected.

---
*Test report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # Stream the content in chunks
        chunk_size = 50
        for i in range(0, len(test_content), chunk_size):
            content_chunk = {
                "type": "content",
                "data": {
                    "content": test_content[i:i+chunk_size],
                    "is_partial": i + chunk_size < len(test_content)
                },
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(content_chunk)}\n\n"
            await asyncio.sleep(0.05)
        
        # Send final metadata
        final_chunk = {
            "type": "metadata",
            "data": {
                "status": "completed",
                "full_response": test_content,
                "workflow_used": "test",
                "confidence_score": 1.0,
                "analysis_type": "test",
                "error": False,
                "error_message": None
            },
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        
        # Send end signal
        end_chunk = {
            "type": "end",
            "data": {"status": "stream_completed"},
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(end_chunk)}\n\n"
    
    try:
        return StreamingResponse(
            test_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test streaming error: {str(e)}")


@router.post("/stream/debug")
async def stream_debug_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None
):
    """Debug streaming endpoint to test report researcher directly."""
    async def debug_stream():
        # Send initial metadata
        initial_chunk = {
            "type": "metadata",
            "data": {
                "thread_id": request.thread_id,
                "status": "debug_mode",
                "message_type": request.message_type
            },
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(initial_chunk)}\n\n"
        
        try:
            # Get supervisor workflow from app state
            supervisor_workflow = fastapi_request.app.state.supervisor_workflow
            
            # Prepare workflow input
            workflow_input = {
                "message": request.content,
                "user_id": request.metadata.get("user_id") if request.metadata else None,
                "thread_id": request.thread_id,
                "conversation_history": []
            }
            
            # Prepare config with threadID
            config = {
                "configurable": {
                    "thread_id": request.thread_id
                }
            }
            
            # Stream the workflow execution
            async for chunk in supervisor_workflow.astream(workflow_input, config=config):
                debug_chunk = {
                    "type": "debug",
                    "data": {
                        "chunk": chunk,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                yield f"data: {json.dumps(debug_chunk)}\n\n"
                
        except Exception as e:
            error_chunk = {
                "type": "error",
                "data": {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        debug_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.post("/stream/report-test")
async def stream_report_test(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None
):
    """Test endpoint specifically for report generation debugging."""
    async def report_test_stream():
        # Send initial metadata
        initial_chunk = {
            "type": "metadata",
            "data": {
                "thread_id": request.thread_id,
                "status": "report_test_mode",
                "message_type": request.message_type,
                "test_message": "Testing report generation with enhanced debugging"
            },
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(initial_chunk)}\n\n"
        
        try:
            # Get supervisor workflow from app state
            supervisor_workflow = fastapi_request.app.state.supervisor_workflow
            
            # Force report researcher workflow by using report keywords
            test_message = f"Generate a comprehensive report about {request.content}"
            
            # Prepare workflow input
            workflow_input = {
                "message": test_message,
                "user_id": request.metadata.get("user_id") if request.metadata else None,
                "thread_id": request.thread_id,
                "conversation_history": []
            }
            
            # Prepare config with threadID
            config = {
                "configurable": {
                    "thread_id": request.thread_id
                }
            }
            
            # Send test message info
            test_chunk = {
                "type": "test_info",
                "data": {
                    "original_message": request.content,
                    "test_message": test_message,
                    "timestamp": datetime.now().isoformat()
                }
            }
            yield f"data: {json.dumps(test_chunk)}\n\n"
            
            # Stream the workflow execution
            chunk_count = 0
            async for chunk in supervisor_workflow.astream(workflow_input, config=config):
                chunk_count += 1
                debug_chunk = {
                    "type": "debug",
                    "data": {
                        "chunk_number": chunk_count,
                        "chunk": chunk,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                yield f"data: {json.dumps(debug_chunk)}\n\n"
                
                # Check for report researcher response
                for node_name, node_data in chunk.items():
                    if node_name == "report_researcher" and "response" in node_data:
                        response_length = len(node_data["response"]) if node_data["response"] else 0
                        response_chunk = {
                            "type": "report_response",
                            "data": {
                                "node": node_name,
                                "response_length": response_length,
                                "response_preview": node_data["response"][:200] if node_data["response"] else "EMPTY",
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                        yield f"data: {json.dumps(response_chunk)}\n\n"
                
        except Exception as e:
            error_chunk = {
                "type": "error",
                "data": {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        report_test_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )