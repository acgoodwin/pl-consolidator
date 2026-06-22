from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID


class AccountBase(BaseModel):
    code: str
    name: str
    level: int
    account_type: str
    amount_current_year: Optional[float] = None
    amount_prior_year: Optional[float] = None


class AccountCreate(AccountBase):
    document_id: UUID
    parent_code: Optional[str] = None
    order_seq: int
    is_subtotal: bool = False
    is_header: bool = False


class AccountResponse(AccountBase):
    id: UUID
    document_id: UUID
    parent_code: Optional[str]
    order_seq: int
    is_subtotal: bool
    is_header: bool
    variance_amount: Optional[float]
    variance_pct: Optional[float]
    variance_status: Optional[str]

    class Config:
        from_attributes = True


class AccountHierarchical(AccountResponse):
    """Account with nested children for hierarchical display."""
    children: List["AccountHierarchical"] = []


AccountHierarchical.model_rebuild()


class BalanceSheetResponse(BaseModel):
    document_id: UUID
    company_name: Optional[str]
    fiscal_year: int
    extraction_status: str
    validation_status: str
    assets: List[AccountHierarchical]
    liabilities: List[AccountHierarchical]
    equity: List[AccountHierarchical]
    total_assets: float
    total_liabilities: float
    total_equity: float
    balance_variance_amount: Optional[float]
    balance_variance_pct: Optional[float]
    is_balanced: bool
    extracted_date: Optional[str]


class VarianceItem(BaseModel):
    code: str
    name: str
    amount_current_year: Optional[float]
    amount_prior_year: Optional[float]
    variance_amount: float
    variance_pct: Optional[float]
    variance_status: str


class VarianceAnalysis(BaseModel):
    document_id: UUID
    high_impact_changes: List[VarianceItem]  # >20% change
    medium_impact_changes: List[VarianceItem]  # 5-20%
    low_impact_changes: List[VarianceItem]  # 1-5%
    stable_accounts: List[VarianceItem]  # <1%
