"""ExtractedData ORM model — structured JSON extracted from documents."""
import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.compat import GUID, JSONB_COMPAT


class ExtractedData(Base):
    __tablename__ = "extracted_data"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    claim_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("claims.id"), nullable=False, index=True
    )

    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # prescription, bill, diagnostic_report, pharmacy_bill

    structure_json: Mapped[dict] = mapped_column(JSONB_COMPAT(), nullable=False, default=dict)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="extracted_data")

    def __repr__(self) -> str:
        return f"<ExtractedData {self.document_type} for claim>"
