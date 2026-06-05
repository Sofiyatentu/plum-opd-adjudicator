"""FraudFlag ORM model."""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.compat import GUID


class FraudFlag(Base):
    __tablename__ = "fraud_flags"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    claim_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("claims.id"), nullable=False, index=True
    )

    flag_type: Mapped[str] = mapped_column(String(100), nullable=False)
    flag_details: Mapped[str] = mapped_column(String(500), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    claim: Mapped["Claim"] = relationship("Claim", back_populates="fraud_flags")

    def __repr__(self) -> str:
        return f"<FraudFlag {self.flag_type}>"
