from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schema.auth import Token, UserCreate, UserResponse
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, response: Response, db: Session = Depends(get_db)):
    """Register a new user"""
    
    is_strong, message = security.validate_password_strength(user_in.password) # custom defined func in security
    if not is_strong:
        raise HTTPException(status_code=400, detail=message)
    
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=409, detail="User with this email already exists")
    
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=409, detail="Username already taken")
    
    user = User(
        email=user_in.email,
        username=user_in.username,
        password_hash=security.get_password_hash(user_in.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )

    response.set_cookie(
        key="auth_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        httponly=True,
        secure=False,
        samesite="lax"
    ) # store session in cookies
    
    return user;


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), response: Response = None, db: Session = Depends(get_db)):
    
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    
    if not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    db.commit()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )

    response.set_cookie(
        key="auth_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        httponly=True,
        secure=False,
        samesite="lax"
    )
    
    return user

@router.post("/logout")
def logout(response: Response):
    """Clear cookies"""
    response.delete_cookie(key="auth_token")
    return {"message": "Successfully logged out!"}


