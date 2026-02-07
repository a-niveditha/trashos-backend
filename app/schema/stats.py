from pydantic import BaseModel


class UserStatsResponse(BaseModel):
    """Schema for user statistics (dashboard header)"""
    totalKg: str
    revenue: str
    name: str
    joinedDate: str


class PeriodStatsResponse(BaseModel):
    """Schema for period statistics (dashboard cards)"""
    yearly: str
    monthly: str
    weekly: str


class ImpactStatsResponse(BaseModel):
    """Schema for impact statistics (statistics page)"""
    recycledItems: int
    co2Averted: float
    earned: float
    treesSaved: float
    wasteGenerated: float
    fuelSaved: float
