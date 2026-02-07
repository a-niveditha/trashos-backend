import shutil
from typing import List, Optional
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pathlib import Path

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.submission import Submission, SubmissionStatus
from app.schema.submission import SubmissionCreate, SubmissionResponse, SubmissionList
from app.utils.file_upload_validation import TEMP_DIR, validate_image_file
from app.utils.ml_func import process_with_ml_model

router = APIRouter(prefix="/submissions", tags=["Submissions"])


@router.post("/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):  
    """
    Create new submission by uploading image file
    Processes file with ML model and saves results to database
    """

    validate_image_file(file)
    file_extension = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = TEMP_DIR / unique_filename
    file_url = f"/api/submissions/files/{unique_filename}"
    
    try:
        # Write the uploaded file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create initial submission record
        submission = Submission(
            user_id=current_user.id,
            image_path_url=file_url,
            status=SubmissionStatus.PENDING
        )

        db.add(submission)
        db.commit()
        db.refresh(submission)

        # Process with ML models (after file is fully written and closed)
        try:
            ml_results = process_with_ml_model(str(file_path))

            submission.classification = ml_results.get("classification")
            submission.confidence = ml_results.get("confidence")
            submission.material_type = ml_results.get("material_type")
            submission.recyclable = ml_results.get("recyclable")
            submission.resell_value = ml_results.get("resell_value")
            submission.co2_saved = ml_results.get("co2_saved")
            submission.resell_places = ml_results.get("resell_places")
            submission.model_version = ml_results.get("model_version")
            submission.status = SubmissionStatus.CLASSIFIED
        
            db.commit()
            db.refresh(submission)

        except Exception as ml_error:
            submission.status = SubmissionStatus.FAILED
            db.commit()
            db.refresh(submission)

            print(f"ML processing failed: {ml_error}")

        return submission
        
    except Exception as e:
        if file_path.exists():
            file_path.unlink()

        # Rollback any database changes instead of trying to delete
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process submission: {str(e)}"
        )
    finally:
        file.file.close()

@router.get("/files/{filename}")
async def get_submission_file(filename: str):
    """Serve uploaded submission files"""
    file_path = TEMP_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    from fastapi.responses import FileResponse
    return FileResponse(path=file_path)



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
    """Get a specific submission"""
    
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
    """Delete a submission and its associated file"""
    
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.user_id == current_user.id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Try to delete associated file
    if submission.image_path_url and "/files/" in submission.image_path_url:
        filename = submission.image_path_url.split("/")[-1]
        file_path = TEMP_DIR / filename
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                # Log the error but don't fail the deletion
                print(f"Failed to delete file {filename}: {e}")
    
    db.delete(submission)
    db.commit()
    
    return {"message": "Submission deleted successfully"}