"""RejectionReason ORM model."""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.compat import GUID


class RejectionReason(Base):
    __tablename__ = "rejection_reasons"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    claim_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("claims.id"), nullable=False, index=True
    )

    reason_code: Mapped[str] = mapped_column(String(50), nullable=False)
    reason_description: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    claim: Mapped["Claim"] = relationship("Claim", back_populates="rejection_reasons")

    def __repr__(self) -> str:
        return f"<RejectionReason {self.reason_code}>"
