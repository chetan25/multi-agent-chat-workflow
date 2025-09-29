"""
Document upload routes.
"""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from models import Document
from models.base import get_db
from .schemas import UploadResponse, DocumentInfo

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    thread_id: str = Form(None),
    db: Session = Depends(get_db),
):
    """Upload a document."""
    # Validate file type
    allowed_types = [
        "image/jpeg",
        "image/png", 
        "image/gif",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    # Validate file size (10MB limit)
    max_size = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Generate unique filename
    document_id = str(uuid4())
    file_extension = Path(file.filename).suffix
    filename = f"{document_id}{file_extension}"
    
    # Save file
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    file_path = uploads_dir / filename
    
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)
    
    # Generate public URL
    file_url = f"/uploads/{filename}"
    
    # Save document info to database
    document = Document(
        document_id=document_id,
        filename=file.filename,
        file_path=str(file_path),
        file_url=file_url,
        file_type=file.content_type,
        file_size=len(file_content),
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return UploadResponse(
        document_id=document.document_id,
        filename=document.filename,
        file_url=document.file_url,
        file_type=document.file_type,
        file_size=document.file_size,
        uploaded_at=document.uploaded_at,
    )


@router.get("/documents/{document_id}", response_model=DocumentInfo)
async def get_document_info(document_id: str, db: Session = Depends(get_db)):
    """Get document information."""
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentInfo(
        document_id=document.document_id,
        filename=document.filename,
        file_url=document.file_url,
        file_type=document.file_type,
        file_size=document.file_size,
        uploaded_at=document.uploaded_at,
    )


@router.get("/documents/{document_id}/download")
async def download_document(document_id: str, db: Session = Depends(get_db)):
    """Download a document."""
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=str(file_path),
        filename=document.filename,
        media_type=document.file_type,
    )
