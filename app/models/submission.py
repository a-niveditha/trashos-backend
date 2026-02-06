import uuid
from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import String, UUID, Enum as SQLEnum, Numeric, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.user import User


class SubmissionStatus(Enum):
    PENDING = "pending"
    CLASSIFIED = "classified" 
    FAILED = "failed"


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign key to User
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    image_path_url: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    resell_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=True
    )

    classification: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    co2_saved: Mapped[Optional[float]] = mapped_column(
        Float,  # kg of CO2 saved
        nullable=True
    )

    resell_places: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True
    )

    # ML Model tracking
    model_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # Processing status
    status: Mapped[SubmissionStatus] = mapped_column(
        SQLEnum(SubmissionStatus),
        default=SubmissionStatus.PENDING,
        nullable=False,
        index=True
    )

    # Relationship to User (optional, for easier querying)
    user: Mapped["User"] = relationship("User", back_populates="submissions")

    def __repr__(self) -> str:
        return f"<Submission(id={self.id}, user_id={self.user_id}, status={self.status.value})>"

    @property
    def is_processed(self) -> bool:
        """Check if submission has been processed (classified or failed)"""
        return self.status in [SubmissionStatus.CLASSIFIED, SubmissionStatus.FAILED]