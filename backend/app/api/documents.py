import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Document, Company, Account, ExtractionLog
from app.schemas.document import DocumentUploadResponse, DocumentResponse, DocumentListResponse
from app.services.pdf_extraction import PdfExtractionService
from app.services.account_parser import AccountParser
from app.services.validation import ValidationService
from app.config import settings
from datetime import datetime

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a German financial statement PDF.

    Supported formats:
    - Jahresabschluss (annual balance sheet with current & prior year)
    - SUSA (monthly account ledger)
    - EUE (monthly P&L)

    Returns immediately with extraction status. Extraction happens asynchronously.
    """
    try:
        # Validate file
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        if file.size and file.size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {settings.max_file_size_mb}MB)"
            )

        # Create upload directory
        os.makedirs(settings.upload_folder, exist_ok=True)

        # Save file
        file_id = str(uuid.uuid4())
        file_path = os.path.join(settings.upload_folder, f"{file_id}_{file.filename}")

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Detect document type
        extraction_service = PdfExtractionService(file_path)
        try:
            extraction_service.open()
            doc_type = extraction_service.detect_document_type()
            company_name = None

            if doc_type == "BILANZ":
                # Extract metadata from balance sheet
                bs_data = extraction_service.extract_balance_sheet_data()
                company_name = bs_data.get("company_name")
                fiscal_year = bs_data.get("fiscal_year", 2025)
            else:
                doc_type = doc_type or "BILANZ"  # Default to BILANZ
                fiscal_year = 2025

            extraction_service.close()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")

        # Find or create company
        if company_name:
            company = db.query(Company).filter(Company.legal_name == company_name).first()
            if not company:
                company = Company(legal_name=company_name)
                db.add(company)
                db.flush()
        else:
            # Create a default company for testing
            company_name = f"Company_{file_id[:8]}"
            company = Company(legal_name=company_name)
            db.add(company)
            db.flush()

        # Create document record
        document = Document(
            company_id=company.id,
            fiscal_year=fiscal_year,
            document_type=doc_type,
            file_name=file.filename,
            file_path=file_path,
            file_size_bytes=len(content),
            extraction_status="PENDING",
            validation_status="NOT_VALIDATED"
        )
        db.add(document)
        db.flush()

        # Start extraction (synchronous for now, can be made async with Celery later)
        try:
            _process_document(document.id, company.id, file_path, doc_type, db)
        except Exception as e:
            document.extraction_status = "FAILED"
            log = ExtractionLog(
                document_id=document.id,
                log_type="CRITICAL",
                source="EXTRACTION_PROCESS",
                error_message=str(e),
                resolution="FAILED"
            )
            db.add(log)

        db.commit()

        return DocumentUploadResponse(
            document_id=document.id,
            status=document.extraction_status,
            message=f"Document uploaded and processing started. Type: {doc_type}",
            extraction_status=document.extraction_status
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


def _process_document(doc_id: str, company_id: str, file_path: str, doc_type: str, db: Session):
    """Extract and process document (can be converted to async task)."""
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        return

    try:
        with PdfExtractionService(file_path) as extraction_service:
            if doc_type == "BILANZ":
                bs_data = extraction_service.extract_balance_sheet_data()
                raw_accounts = bs_data.get("accounts", [])

                if not raw_accounts:
                    raise ValueError("No accounts extracted from document")

                # Parse accounts
                parser = AccountParser()
                parsed_accounts = parser.parse_accounts(raw_accounts)
                parsed_accounts = parser.calculate_variances(parsed_accounts)

                # Validate
                validator = ValidationService()
                is_valid, warnings = validator.validate_extraction(parsed_accounts)

                # Store accounts
                for account_data in parsed_accounts:
                    account = Account(
                        document_id=document.id,
                        code=account_data["code"],
                        name=account_data["name"],
                        level=account_data["level"],
                        parent_code=account_data.get("parent_code"),
                        order_seq=account_data["order_seq"],
                        account_type=account_data["account_type"],
                        is_subtotal=account_data["is_subtotal"],
                        is_header=account_data["is_header"],
                        amount_current_year=account_data.get("amount_current_year"),
                        amount_prior_year=account_data.get("amount_prior_year"),
                        variance_amount=account_data.get("variance_amount"),
                        variance_pct=account_data.get("variance_pct"),
                        variance_status=account_data.get("variance_status")
                    )
                    db.add(account)

                # Validate balance sheet equation
                balance_is_valid, balance_variance, balance_warnings = validator.validate_balance_sheet(parsed_accounts)

                document.balance_variance_amount = balance_variance
                if balance_warnings:
                    for warning in balance_warnings:
                        log = ExtractionLog(
                            document_id=document.id,
                            log_type="WARNING",
                            source="VALIDATION",
                            error_message=warning,
                            resolution="NOTED"
                        )
                        db.add(log)

                document.extraction_status = "SUCCESS"
                document.validation_status = "VALID" if balance_is_valid else "WARNINGS"
                document.extracted_date = datetime.utcnow()

    except Exception as e:
        document.extraction_status = "FAILED"
        document.validation_status = "FAILED"
        log = ExtractionLog(
            document_id=document.id,
            log_type="CRITICAL",
            source="EXTRACTION_PROCESS",
            error_message=str(e),
            resolution="FAILED"
        )
        db.add(log)

    finally:
        db.commit()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get document details and extraction status."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse.from_orm(document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    company_id: str = Query(None),
    db: Session = Depends(get_db)
):
    """List all documents with pagination."""
    query = db.query(Document).order_by(desc(Document.upload_date))

    if company_id:
        try:
            company_uuid = uuid.UUID(company_id)
            query = query.filter(Document.company_id == company_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid company ID format")

    total = query.count()
    documents = query.offset(skip).limit(limit).all()

    return DocumentListResponse(
        total=total,
        documents=[DocumentResponse.from_orm(doc) for doc in documents]
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and all associated data."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete uploaded file
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            print(f"Warning: Could not delete file {document.file_path}: {e}")

    # Delete database record (cascades to accounts and logs)
    db.delete(document)
    db.commit()

    return None
