"""Document ORM model — uploaded file metadata."""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.compat import GUID


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    claim_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("claims.id"), nullable=False, index=True
    )

    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # mime type
    document_category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # prescription, bill, diagnostic_report, pharmacy_bill

    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document {self.document_category}: {self.file_name}>"
