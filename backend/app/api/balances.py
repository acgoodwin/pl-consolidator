import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Document, Account, Company
from app.schemas.account import BalanceSheetResponse, VarianceAnalysis, AccountHierarchical, VarianceItem

router = APIRouter(prefix="/api/v1", tags=["balances"])


@router.get("/balances/{document_id}", response_model=BalanceSheetResponse)
async def get_balance_sheet(document_id: str, db: Session = Depends(get_db)):
    """
    Get balance sheet with hierarchical structure and variance analysis.

    Returns assets, liabilities, and equity organized hierarchically
    with current year, prior year, and variance columns.
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.extraction_status != "SUCCESS":
        raise HTTPException(
            status_code=400,
            detail=f"Document extraction not completed. Status: {document.extraction_status}"
        )

    # Get company name
    company = db.query(Company).filter(Company.id == document.company_id).first()
    company_name = company.legal_name if company else None

    # Get all accounts
    accounts = db.query(Account).filter(Account.document_id == doc_uuid).order_by(Account.order_seq).all()

    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts found for this document")

    # Build hierarchical structure
    assets = _build_hierarchy(
        [_account_to_dict(acc) for acc in accounts if acc.account_type == "ASSET"]
    )
    liabilities = _build_hierarchy(
        [_account_to_dict(acc) for acc in accounts if acc.account_type == "LIABILITY"]
    )
    equity = _build_hierarchy(
        [_account_to_dict(acc) for acc in accounts if acc.account_type == "EQUITY"]
    )

    # Calculate totals
    total_assets = sum(acc.amount_current_year or 0 for acc in accounts if acc.account_type == "ASSET")
    total_liabilities = sum(acc.amount_current_year or 0 for acc in accounts if acc.account_type == "LIABILITY")
    total_equity = sum(acc.amount_current_year or 0 for acc in accounts if acc.account_type == "EQUITY")

    is_balanced = abs(total_assets - (total_liabilities + total_equity)) < 0.01

    return BalanceSheetResponse(
        document_id=document.id,
        company_name=company_name,
        fiscal_year=document.fiscal_year,
        extraction_status=document.extraction_status,
        validation_status=document.validation_status,
        assets=assets,
        liabilities=liabilities,
        equity=equity,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        total_equity=total_equity,
        balance_variance_amount=document.balance_variance_amount,
        balance_variance_pct=document.balance_variance_pct,
        is_balanced=is_balanced,
        extracted_date=document.extracted_date.isoformat() if document.extracted_date else None
    )


@router.get("/variance/{document_id}", response_model=VarianceAnalysis)
async def get_variance_analysis(document_id: str, db: Session = Depends(get_db)):
    """
    Get variance analysis grouped by impact level.

    Groups changes into:
    - High impact: >20% change
    - Medium impact: 5-20% change
    - Low impact: 1-5% change
    - Stable: <1% change
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    accounts = db.query(Account).filter(Account.document_id == doc_uuid).all()

    high_impact = []
    medium_impact = []
    low_impact = []
    stable = []

    for acc in accounts:
        if acc.variance_pct is None:
            continue

        item = VarianceItem(
            code=acc.code,
            name=acc.name,
            amount_current_year=acc.amount_current_year,
            amount_prior_year=acc.amount_prior_year,
            variance_amount=acc.variance_amount or 0,
            variance_pct=acc.variance_pct,
            variance_status=acc.variance_status or "STABLE"
        )

        abs_variance = abs(acc.variance_pct)

        if abs_variance > 20:
            high_impact.append(item)
        elif abs_variance > 5:
            medium_impact.append(item)
        elif abs_variance > 1:
            low_impact.append(item)
        else:
            stable.append(item)

    # Sort by absolute variance
    high_impact.sort(key=lambda x: abs(x.variance_pct or 0), reverse=True)
    medium_impact.sort(key=lambda x: abs(x.variance_pct or 0), reverse=True)
    low_impact.sort(key=lambda x: abs(x.variance_pct or 0), reverse=True)

    return VarianceAnalysis(
        document_id=document.id,
        high_impact_changes=high_impact,
        medium_impact_changes=medium_impact,
        low_impact_changes=low_impact,
        stable_accounts=stable
    )


def _account_to_dict(account: Account) -> dict:
    """Convert Account ORM to dictionary."""
    return {
        "id": account.id,
        "code": account.code,
        "name": account.name,
        "level": account.level,
        "account_type": account.account_type,
        "amount_current_year": account.amount_current_year,
        "amount_prior_year": account.amount_prior_year,
        "variance_amount": account.variance_amount,
        "variance_pct": account.variance_pct,
        "variance_status": account.variance_status,
        "parent_code": account.parent_code,
        "order_seq": account.order_seq,
        "is_subtotal": account.is_subtotal,
        "is_header": account.is_header,
        "children": []
    }


def _build_hierarchy(accounts: list[dict]) -> list[AccountHierarchical]:
    """
    Build hierarchical tree structure from flat account list.

    Uses parent_code references to nest children under parents.
    """
    # Index accounts by code for quick lookup
    account_map = {acc["code"]: acc for acc in accounts}

    # Find root accounts (those without parent or parent not in this section)
    roots = [acc for acc in accounts if acc["parent_code"] is None or acc["parent_code"] not in account_map]

    # Recursively add children
    for root in roots:
        _add_children(root, account_map)

    # Convert to Pydantic models
    return [AccountHierarchical(**acc) for acc in roots]


def _add_children(parent: dict, account_map: dict) -> None:
    """Recursively add children to parent account."""
    for acc in account_map.values():
        if acc["parent_code"] == parent["code"]:
            parent["children"].append(acc)
            _add_children(acc, account_map)
