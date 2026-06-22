from sqlalchemy import Column, String, Integer, DECIMAL, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(20), nullable=False)  # A.I.1, A.I.2, A.II, etc.
    name = Column(String(255), nullable=False)
    level = Column(Integer, nullable=False)  # 1 (A, B), 2 (A.I, A.II), 3 (A.I.1, A.I.2)
    parent_code = Column(String(20))  # Reference to parent code
    order_seq = Column(Integer, nullable=False)  # Maintains PDF order
    account_type = Column(String(20), nullable=False)  # ASSET, LIABILITY, EQUITY, ITEM
    is_subtotal = Column(Boolean, default=False)
    is_header = Column(Boolean, default=False)  # True for "AKTIVA", "PASSIVA"

    # Values
    amount_current_year = Column(DECIMAL(15, 2))
    amount_prior_year = Column(DECIMAL(15, 2))

    # Variance
    variance_amount = Column(DECIMAL(15, 2))
    variance_pct = Column(DECIMAL(5, 2))
    variance_status = Column(String(20))  # STABLE, IMPROVED, DECLINED

    # Tracking
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_accounts_document_id", "document_id"),
        Index("idx_accounts_code", "code"),
        Index("idx_accounts_parent_code", "parent_code"),
        Index("idx_accounts_account_type", "account_type"),
        Index("idx_accounts_document_code", "document_id", "code", unique=True),
    )

    # Relationships
    document = relationship("Document", back_populates="accounts")
