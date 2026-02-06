from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core import security
from app.db.session import get_db
from app.models.user import User

security_scheme = HTTPBearer()

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate user from JWT token."""
    
    # define http exception for unauthorized creds 
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = request.cookies.get("auth_token")
    if not token:
        raise credentials_exception

    try:
        is_valid, payload = security.verify_token(token)
        if not is_valid or not payload:
            raise credentials_exception # auth not found
            
        username: str = payload.get("sub") #username is the subject
        if username is None:
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Check if current user is admin - like Express.js role middleware."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
