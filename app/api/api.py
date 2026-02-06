from fastapi import APIRouter
from app.api.routes import health 
from app.api.routes import auth
from app.api.routes import submissions


router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(submissions.router)