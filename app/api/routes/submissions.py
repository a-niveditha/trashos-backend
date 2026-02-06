from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.submission import Submission, SubmissionStatus
from app.schema.submission import SubmissionCreate, SubmissionUpdate, SubmissionResponse, SubmissionList

router = APIRouter(prefix="/submissions", tags=["Submissions"])


@router.post("/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):  
    #might've to add route level auth check
    # Create new submission linked to current user

    # call to ml function goes here

    #------------------------------------
    submission = Submission(
        user_id=current_user.id,
        image_path_url=submission_data.image_path_url,
        status=SubmissionStatus.PENDING
    )
    
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    return submission


@router.get("/", response_model=SubmissionList)
def get_submissions(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status_filter: Optional[SubmissionStatus] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's submissions with pagination"""
    
    # Base query for user's submissions
    query = db.query(Submission).filter(Submission.user_id == current_user.id)
    
    # Apply status filter if provided
    if status_filter:
        query = query.filter(Submission.status == status_filter)
    
    # Order by newest first
    query = query.order_by(desc(Submission.created_at))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    submissions = query.offset(offset).limit(per_page).all()
    
    return SubmissionList(
        items=submissions,
        total=total,
        page=page,
        per_page=per_page,
        has_next=offset + per_page < total,
        has_prev=page > 1
    )


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific submission (like Express.js GET /submissions/:id)"""
    
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.user_id == current_user.id  
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    return submission

@router.delete("/{submission_id}")
def delete_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a submission"""
    
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.user_id == current_user.id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    db.delete(submission)
    db.commit()
    
    return {"message": "Submission deleted successfully"}


