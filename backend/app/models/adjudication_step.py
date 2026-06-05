"""AdjudicationStep ORM model — per-step audit trail for each claim."""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Float, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.compat import GUID, JSONB_COMPAT


class AdjudicationStep(Base):
    __tablename__ = "adjudication_steps"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    claim_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("claims.id"), nullable=False, index=True
    )

    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB_COMPAT(), nullable=True)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="adjudication_steps")

    def __repr__(self) -> str:
        return f"<AdjudicationStep {self.step_number}: {self.step_name} (passed={self.passed})>"
