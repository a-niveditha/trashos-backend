from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.submission import Submission, SubmissionStatus
from app.schema.stats import UserStatsResponse, PeriodStatsResponse, ImpactStatsResponse

router = APIRouter(prefix="/stats", tags=["Statistics"])

@router.get("/user", response_model=UserStatsResponse)
def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics for dashboard header"""
    
    # Get all classified submissions for the user
    classified_submissions = db.query(Submission).filter(
        Submission.user_id == current_user.id,
        Submission.status == SubmissionStatus.CLASSIFIED
    ).all()
    
    # Calculate total CO2 saved (in grams) and convert to approximate kg
    total_co2 = sum(
        float(s.co2_saved) if s.co2_saved else 0.0 
        for s in classified_submissions
    )
    total_kg = total_co2/1000.0
    
    # Calculate total revenue
    total_revenue = sum(
        float(s.resell_value) if s.resell_value else 0.0 
        for s in classified_submissions
    )
    
    # Format joined date
    joined_date = current_user.created_at.strftime("%d/%m/%Y")
    
    return UserStatsResponse(
        totalKg=f"{total_kg:.2f}",
        revenue=f"{total_revenue:,.0f}",
        name=current_user.username,
        joinedDate=joined_date
    )


@router.get("/period", response_model=PeriodStatsResponse)
def get_period_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get period statistics for dashboard cards (items recycled)"""
    
    now = datetime.utcnow()
    
    # Calculate date boundaries
    one_week_ago = now - timedelta(days=7)
    one_month_ago = now - timedelta(days=30)
    one_year_ago = now - timedelta(days=365)
    
    # Count classified submissions in each period
    weekly_count = db.query(func.count(Submission.id)).filter(
        Submission.user_id == current_user.id,
        Submission.status == SubmissionStatus.CLASSIFIED,
        Submission.created_at >= one_week_ago
    ).scalar() or 0
    
    monthly_count = db.query(func.count(Submission.id)).filter(
        Submission.user_id == current_user.id,
        Submission.status == SubmissionStatus.CLASSIFIED,
        Submission.created_at >= one_month_ago
    ).scalar() or 0
    
    yearly_count = db.query(func.count(Submission.id)).filter(
        Submission.user_id == current_user.id,
        Submission.status == SubmissionStatus.CLASSIFIED,
        Submission.created_at >= one_year_ago
    ).scalar() or 0
    
    return PeriodStatsResponse(
        yearly=str(yearly_count),
        monthly=str(monthly_count),
        weekly=str(weekly_count)
    )


@router.get("/impact", response_model=ImpactStatsResponse)
def get_impact_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get impact statistics for statistics page"""
    
    # Get all classified submissions
    classified_submissions = db.query(Submission).filter(
        Submission.user_id == current_user.id,
        Submission.status == SubmissionStatus.CLASSIFIED
    ).all()
    
    # Count recycled items (only recyclable ones)
    recycled_items = sum(
        1 for s in classified_submissions 
        if s.recyclable is True
    )
    
    # Calculate total CO2 saved (in kg)
    co2_averted = sum(
        float(s.co2_saved) / 1000.0 if s.co2_saved else 0.0 
        for s in classified_submissions
    )
    
    # Calculate total earned
    earned = sum(
        float(s.resell_value) if s.resell_value else 0.0 
        for s in classified_submissions
    )
    
    # Estimate trees saved (approximately 1 tree per 20kg of CO2 saved)
    trees_saved = co2_averted / 23.5
    
    
    return ImpactStatsResponse(
        recycledItems=recycled_items,
        co2Averted=round(co2_averted, 2),
        earned=round(earned, 2),
        treesSaved=round(trees_saved, 2),
    )
