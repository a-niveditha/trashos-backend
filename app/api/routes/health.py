from fastapi import APIRouter
from app.services.health_service import get_health

router = APIRouter(prefix="/health")

@router.get("/")
def health():
    return get_health()