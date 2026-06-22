# P&L Consolidator

**Purpose:** Financial P&L consolidation platform. Phase 1: Extract German HGB annual financial statements (Jahresabschluss), display side-by-side year comparison (Current Year vs Prior Year) with variance analysis, export to Excel/CSV/PDF.

**Stack:** FastAPI + React + PostgreSQL

## Document Types Supported

### Phase 1 (MVP)
- **Jahresabschluss** (annual financial statements): Bilanz (Balance Sheet) with two years side-by-side

### Phase 2+ (Planned)
- **SUSA** (Summen und Saldi): monthly account ledger with 13 columns
- **EUE** (Entwicklungsübersicht): monthly P&L summary
- **Multi-company consolidation**: Merge P&Ls from multiple entities

## Project Structure

```
pl-consolidator/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py           # SQLAlchemy engine
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── document.py       # Document, Account, Company ORM
│   │   │   └── extraction_log.py
│   │   ├── schemas/              # Pydantic request/response models
│   │   │   ├── document.py
│   │   │   ├── balance_sheet.py
│   │   │   └── export.py
│   │   ├── services/             # Business logic
│   │   │   ├── pdf_extraction.py    # pdfplumber-based parser
│   │   │   ├── account_parser.py    # Hierarchical account code logic
│   │   │   ├── validation.py        # Balance equation checks
│   │   │   ├── export_excel.py
│   │   │   ├── export_csv.py
│   │   │   └── export_pdf.py
│   │   ├── api/
│   │   │   ├── documents.py         # POST /upload, GET /documents/{id}
│   │   │   ├── balances.py          # GET /balances/{id}, /variance
│   │   │   └── exports.py           # POST /export/*, GET /exports/*
│   │   └── utils/
│   │       └── german_locale.py     # Decimal parsing: "1.234,56" → 1234.56
│   ├── tests/
│   │   ├── fixtures/                # Sample PDFs, ground truth JSON
│   │   ├── test_extraction.py
│   │   ├── test_parsing.py
│   │   ├── test_validation.py
│   │   ├── test_export.py
│   │   └── test_api.py
│   ├── migrations/                  # Alembic database migrations
│   │   └── versions/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx           # Upload + recent docs
│   │   │   ├── BalanceSheetPage.jsx        # Main Phase 1 view
│   │   │   └── ExportPreviewPage.jsx       # Phase 1.5
│   │   ├── components/
│   │   │   ├── DocumentUploadZone.jsx      # Drag-and-drop
│   │   │   ├── BalanceSheetComparison.jsx  # Two-column view
│   │   │   ├── AccountRow.jsx              # Single line with variance
│   │   │   ├── ValidationBanner.jsx        # Balance check result
│   │   │   ├── ExportMenu.jsx              # Format selector
│   │   │   └── ExtractionLogViewer.jsx
│   │   └── hooks/
│   │       ├── useDocumentUpload.js
│   │       ├── useBalanceSheet.js
│   │       └── useExport.js
│   ├── package.json
│   └── README.md
│
├── docker-compose.yml              # Phase 1.5+
├── .gitignore
└── CLAUDE.md
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node 18+
- PostgreSQL 14+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Create PostgreSQL database
createdb pl_consolidator

# Run migrations
alembic upgrade head

# Start server
python -m app.main
# Runs on http://localhost:8000
```

### Frontend Setup

```bash
cd frontend

npm install
npm start
# Runs on http://localhost:3000
```

### Database Setup (Docker)

```bash
docker run --name pl-consolidator-db \
  -e POSTGRES_DB=pl_consolidator \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=devpass \
  -p 5432:5432 \
  postgres:15
```

## Environment Variables (.env)

```
DATABASE_URL=postgresql://app:devpass@localhost:5432/pl_consolidator
ENVIRONMENT=development
LOG_LEVEL=DEBUG
UPLOAD_FOLDER=/tmp/pl-consolidator-uploads
MAX_FILE_SIZE_MB=50
CORS_ORIGINS=http://localhost:3000
```

## Phase 1 Architecture Decisions

### PDF Extraction
- **Primary:** `pdfplumber` (excellent for structured HGB documents)
- **Fallback:** `pypdf` (handles edge cases)
- **OCR:** `pytesseract` (only for scanned PDFs)

### Data Model
- **Accounts:** Recursive DB table with `parent_code` field (A → A.I → A.I.1)
- **Variance:** Absolute (EUR) + percentage (%) + trend status
- **Decimal:** German format "1.234.567,89" parsed to float via regex replacement
- **Storage:** All amounts as DECIMAL(15,2) for precision

### Variance Calculation
1. **Absolute:** current_year - prior_year
2. **Percentage:** ((CY - PY) / |PY|) × 100
3. **Status:** STABLE (<1%), IMPROVED (CY > PY), DECLINED (CY < PY)

### Error Handling
- **CRITICAL (400):** PDF corrupted, can't open
- **WARNING (200 + log):** Amount can't parse, account code not found → skip + continue
- **INFO (200 + flag):** Balance off by EUR 0.01 → allow manual review

## Core API Endpoints

### Documents
```
POST   /api/v1/documents/upload         Upload Jahresabschluss PDF
GET    /api/v1/documents/{document_id}  Get extraction status
GET    /api/v1/documents                List all documents (with filters)
DELETE /api/v1/documents/{document_id}  Delete document
```

### Balance Sheet
```
GET    /api/v1/balances/{document_id}   Get Bilanz (hierarchical)
GET    /api/v1/variance                 Get variance analysis
```

### Export
```
POST   /api/v1/export/excel             Generate Excel file
POST   /api/v1/export/csv               Generate CSV file
POST   /api/v1/export/pdf               Generate PDF report
GET    /api/v1/extraction-logs/{doc_id} Get parsing warnings/errors
```

## Database Schema (Key Tables)

### documents
- `id` (UUID, PK)
- `company_id` (UUID, FK)
- `fiscal_year` (INT)
- `document_type` (BILANZ | P_AND_L | NOTES)
- `extraction_status` (PENDING | SUCCESS | FAILED | PARTIAL)
- `validation_status` (NOT_VALIDATED | VALID | WARNINGS | FAILED)
- `balance_variance_amount` (EUR difference if validation fails)
- `extraction_date`, `upload_date`

### accounts
- `id` (UUID, PK)
- `document_id` (FK)
- `code` (A.I.1) — indexed
- `name`, `level` (1, 2, 3)
- `parent_code` (nullable, enables hierarchy)
- `account_type` (ASSET | LIABILITY | EQUITY | ITEM)
- `amount_current_year`, `amount_prior_year`
- `variance_amount`, `variance_pct`, `variance_status`
- `is_subtotal` (true for rollup rows)
- `order_seq` (maintains PDF order)

### extraction_logs
- `id` (UUID, PK)
- `document_id` (FK)
- `log_type` (INFO | WARNING | CRITICAL)
- `source` (PDF_PARSE | AMOUNT_PARSE | VALIDATION | OCR)
- `line_number`, `raw_text`, `error_message`
- `resolution` (SKIPPED | CORRECTED | MANUAL_REVIEW | ACCEPTED)

### companies
- `id` (UUID, PK)
- `legal_name` — indexed
- `hgb_reference_number` (Commercial register number)
- `currency` (EUR, USD, etc.)
- `fiscal_year_end` (month: 12 = December)

## Frontend Components (Phase 1)

### DashboardPage
- Upload zone (drag-and-drop)
- Recent documents list
- Status indicators (extraction progress)

### BalanceSheetPage (Main)
- Two-column comparison (Current Year | Prior Year)
- Variance column (EUR + %)
- Collapsible hierarchy (click parent to expand/collapse)
- Subtotal rows highlighted
- Color-coded variance (green=improvement, red=decline, gray=stable)
- Validation banner (Assets = Liabilities + Equity check)
- Export menu (Excel, CSV, PDF)

### Detail Panel
- Variance analysis (high/medium/low impact changes)
- Extraction log viewer (warnings/errors)
- Account drill-down

## Dependencies (Version Locked)

### Backend (NEW additions for Phase 1)

```
pdfplumber==0.10.3           # PDF text extraction
pypdf==4.1.1                 # Fallback PDF parser
openpyxl==3.11.1             # Excel generation
reportlab==4.0.7             # PDF generation
alembic==1.12.1              # Database migrations
pytest==7.4.3                # Unit testing
pytest-asyncio==0.21.1       # Async test support
```

### Frontend (NEW additions)

```
react-dropzone==14.2.3       # Drag-and-drop file upload
tailwindcss==3.3.5           # CSS (optional)
recharts==2.10.0             # Charts (Phase 1.5)
```

## Testing Strategy

**Unit Tests:** German decimal parsing, account hierarchy, variance calculations, export formatting

**Integration Tests:** PDF upload → extraction → balance sheet API → validation

**E2E Tests:** Upload sample Jahresabschluss → view balance sheet → export Excel → validate content

**Test Coverage Target:** >80%

**Sample Test Data:** Anonymized real Jahresabschluss PDFs in `/backend/tests/fixtures/`

## Deployment

### Local Development
See "Getting Started" above.

### Docker Compose (Phase 1.5+)
```bash
docker-compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# PostgreSQL: localhost:5432
```

### Production Checklist
- Use environment variables for all secrets
- Configure HTTPS (SSL/TLS)
- Enable PostgreSQL backups (daily)
- Implement rate limiting on upload endpoint
- Use structured JSON logging (audit trail)
- Deploy health check endpoint for orchestrators
- Store large PDFs in S3/Azure (not database BYTEA)

## Status

**Phase:** 1 (Implementation scheduled)

**Database:** 4 core tables designed, Alembic migrations planned

**Backend:** PDF extraction service + API endpoints + validation logic (in progress)

**Frontend:** Upload zone + Balance sheet comparison view (in progress)

**Export:** Excel, CSV, PDF engines (in progress)

**Target:** Week 4 of June 2026 (completion of Phase 1)
