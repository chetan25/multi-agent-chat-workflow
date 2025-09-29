"""
User management routes.
"""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models import User
from models.base import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


class CreateUserRequest(BaseModel):
    username: str
    email: str = None
    user_id: str = None


class CreateUserResponse(BaseModel):
    user_id: str
    username: str
    email: str = None
    is_active: bool
    created_at: datetime


@router.post("", response_model=CreateUserResponse)
async def create_user(request: CreateUserRequest, db: Session = Depends(get_db)):
    """Create a new user."""
    user_id = request.user_id or str(uuid4())
    now = datetime.utcnow()
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already exists (if provided)
    if request.email:
        existing_email = db.query(User).filter(User.email == request.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    new_user = User(
        user_id=user_id,
        username=request.username,
        email=request.email,
        is_active=True,
        created_at=now
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return CreateUserResponse(
        user_id=new_user.user_id,
        username=new_user.username,
        email=new_user.email,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )


@router.get("/{user_id}")
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return CreateUserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at
    )
