"""Member ORM model — employees and dependents covered under the policy."""
import uuid
from datetime import date, datetime
from sqlalchemy import String, Boolean, Date, Float, DateTime, func, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship
from app.database import Base
from app.models.compat import GUID
import enum


class MemberRelationship(str, enum.Enum):
    EMPLOYEE = "employee"
    SPOUSE = "spouse"
    CHILD = "child"
    PARENT = "parent"


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    join_date: Mapped[date] = mapped_column(Date, nullable=False)
    relationship: Mapped[str] = mapped_column(
        String(20), nullable=False, default="employee"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ytd_claimed: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    family_floater_used: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # FK to parent employee (null for employees themselves)
    primary_member_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("members.id"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    dependents: Mapped[list["Member"]] = sa_relationship(
        "Member", back_populates="primary_member",
        foreign_keys="[Member.primary_member_id]",
    )
    primary_member: Mapped["Member | None"] = sa_relationship(
        "Member", back_populates="dependents",
        foreign_keys="[Member.primary_member_id]",
        remote_side="Member.id",
    )
    claims: Mapped[list["Claim"]] = sa_relationship("Claim", back_populates="member")

    def __repr__(self) -> str:
        return f"<Member {self.member_code} ({self.name})>"
