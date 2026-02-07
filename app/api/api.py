from fastapi import APIRouter
from app.api.routes import health 
from app.api.routes import auth
from app.api.routes import submissions
from app.api.routes import stats


router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(submissions.router)
router.include_router(stats.router)