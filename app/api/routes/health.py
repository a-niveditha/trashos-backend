from fastapi import APIRouter

router = APIRouter(prefix="/health")

@router.get("/")
def get_health():
    return {"status": "healthy"}