from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class ExtractionLog(Base):
    __tablename__ = "extraction_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    log_type = Column(String(20), nullable=False)  # INFO, WARNING, CRITICAL
    source = Column(String(50))  # PDF_PARSE, AMOUNT_PARSE, VALIDATION, OCR
    line_number = Column(Integer)
    raw_text = Column(Text)
    error_message = Column(Text)
    resolution = Column(String(20))  # SKIPPED, CORRECTED, MANUAL_REVIEW, ACCEPTED
    created_at = Column(DateTime, server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_extraction_logs_document_id", "document_id"),
        Index("idx_extraction_logs_log_type", "log_type"),
    )

    # Relationships
    document = relationship("Document", back_populates="extraction_logs")
