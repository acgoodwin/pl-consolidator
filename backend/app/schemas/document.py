from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class DocumentBase(BaseModel):
    fiscal_year: int
    document_type: str


class DocumentCreate(DocumentBase):
    company_id: UUID
    file_name: str
    file_path: str
    file_size_bytes: Optional[int] = None
    created_by: Optional[UUID] = None


class DocumentUpdate(BaseModel):
    extraction_status: Optional[str] = None
    validation_status: Optional[str] = None
    extracted_date: Optional[datetime] = None
    balance_variance_amount: Optional[float] = None
    balance_variance_pct: Optional[float] = None


class DocumentResponse(DocumentBase):
    id: UUID
    company_id: UUID
    file_name: str
    file_path: str
    file_size_bytes: Optional[int]
    upload_date: datetime
    extracted_date: Optional[datetime]
    extraction_status: str
    validation_status: str
    balance_variance_amount: Optional[float]
    balance_variance_pct: Optional[float]
    created_by: Optional[UUID]
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    status: str
    message: str
    extraction_status: str


class DocumentListResponse(BaseModel):
    total: int
    documents: list[DocumentResponse]
