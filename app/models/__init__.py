# Import all models here so they're registered with SQLAlchemy
# This ensures Alembic can detect all models for migrations

from app.models.user import User, RoleEnum
from app.models.submission import Submission, SubmissionStatus

__all__ = ["User", "RoleEnum", "Submission", "SubmissionStatus"]