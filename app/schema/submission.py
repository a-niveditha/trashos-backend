import uuid
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.models.submission import SubmissionStatus


class SubmissionCreate(BaseModel):
    """Schema for creating a new submission"""
    image_path_url: str = Field(..., min_length=1, max_length=1000)
    
    @field_validator('image_path_url')
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        # Basic validation - can be extended for specific formats
        if not v.strip():
            raise ValueError('Image path cannot be empty')
        return v.strip()


class SubmissionUpdate(BaseModel):
    """Schema for updating submission (usually by ML service)"""
    classification: Optional[str] = Field(None, max_length=255)
    resell_value: Optional[Decimal] = Field(None, gt=0)
    co2_saved: Optional[float] = Field(None, ge=0.0)
    resell_places: Optional[List[str]] = None
    model_version: Optional[str] = Field(None, max_length=50)
    status: Optional[SubmissionStatus] = None

class SubmissionResponse(BaseModel):
    """Schema for submission response"""
    id: uuid.UUID
    user_id: uuid.UUID
    image_path_url: str
    classification: Optional[str] = None
    resell_value: Optional[Decimal] = None
    co2_saved: Optional[float] = None
    resell_places: Optional[List[str]] = None
    model_version: Optional[str] = None
    status: SubmissionStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

    @property
    def confidence_percentage(self) -> Optional[float]:
        """Get ML confidence as percentage"""
        return self.ml_confidence * 100 if self.ml_confidence is not None else None


class SubmissionList(BaseModel):
    """Schema for listing submissions with pagination"""
    items: List[SubmissionResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool