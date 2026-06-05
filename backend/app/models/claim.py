"""Claim ORM model — core claim record with adjudication results."""
import uuid
from datetime import date, datetime
from sqlalchemy import String, Boolean, Float, Date, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.compat import GUID


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    claim_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # Member FK
    member_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("members.id"), nullable=False, index=True
    )

    treatment_date: Mapped[date] = mapped_column(Date, nullable=False)
    submission_date: Mapped[date] = mapped_column(Date, nullable=False)
    claim_amount: Mapped[float] = mapped_column(Float, nullable=False)

    hospital_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_network: Mapped[bool] = mapped_column(Boolean, default=False)
    is_cashless: Mapped[bool] = mapped_column(Boolean, default=False)

    # Adjudication results
    status: Mapped[str] = mapped_column(String(30), default="submitted", nullable=False, index=True)
    # status: submitted, processing, completed
    decision: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # decision: APPROVED, REJECTED, PARTIAL, MANUAL_REVIEW
    approved_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    member: Mapped["Member"] = relationship("Member", back_populates="claims")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="claim")
    extracted_data: Mapped[list["ExtractedData"]] = relationship("ExtractedData", back_populates="claim")
    adjudication_steps: Mapped[list["AdjudicationStep"]] = relationship(
        "AdjudicationStep", back_populates="claim", order_by="AdjudicationStep.step_number"
    )
    rejection_reasons: Mapped[list["RejectionReason"]] = relationship(
        "RejectionReason", back_populates="claim"
    )
    fraud_flags: Mapped[list["FraudFlag"]] = relationship("FraudFlag", back_populates="claim")

    def __repr__(self) -> str:
        return f"<Claim {self.claim_code} [{self.decision}]>"
