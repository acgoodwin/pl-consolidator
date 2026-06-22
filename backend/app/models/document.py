from sqlalchemy import Column, String, Integer, DateTime, DECIMAL, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legal_name = Column(String(255), nullable=False, unique=True, index=True)
    trade_name = Column(String(255))
    hgb_reference_number = Column(String(50), index=True)
    currency = Column(String(3), default="EUR")
    fiscal_year_end = Column(Integer, default=12)
    created_at = Column(DateTime, server_default=func.now())

    documents = relationship("Document", back_populates="company", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    document_type = Column(String(50), nullable=False)  # BILANZ, P_AND_L, NOTES
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer)
    upload_date = Column(DateTime, nullable=False, server_default=func.now())
    extracted_date = Column(DateTime)
    extraction_status = Column(String(20), default="PENDING", nullable=False)  # PENDING, SUCCESS, FAILED, PARTIAL
    validation_status = Column(String(20), default="NOT_VALIDATED", nullable=False)  # NOT_VALIDATED, VALID, WARNINGS, FAILED
    balance_variance_amount = Column(DECIMAL(15, 2))  # Assets - (Liabilities + Equity)
    balance_variance_pct = Column(DECIMAL(5, 2))
    created_by = Column(UUID(as_uuid=True))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_documents_company_id", "company_id"),
        Index("idx_documents_upload_date", "upload_date"),
        Index("idx_documents_company_fiscal_year", "company_id", "fiscal_year", "document_type", unique=True),
    )

    # Relationships
    company = relationship("Company", back_populates="documents")
    accounts = relationship("Account", back_populates="document", cascade="all, delete-orphan")
    extraction_logs = relationship("ExtractionLog", back_populates="document", cascade="all, delete-orphan")
