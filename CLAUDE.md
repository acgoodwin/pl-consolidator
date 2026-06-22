# P&L Consolidator

**Purpose:** Financial P&L consolidation platform for multi-entity income statement rollup, variance analysis, and reporting.

**Stack:** FastAPI (backend) + React (frontend) + PostgreSQL

## Project Structure

```
pl-consolidator/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/       # Endpoints
│   │   ├── models/    # Pydantic models
│   │   ├── schemas/   # DB schemas
│   │   ├── services/  # Business logic
│   │   └── config.py
│   ├── requirements.txt
│   └── README.md
├── frontend/          # React application
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   ├── pages/
│   │   └── index.css
│   ├── package.json
│   └── README.md
├── docs/              # Documentation
└── CLAUDE.md
```

## Getting Started

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

## Key Features (Planned)

- Multi-entity P&L consolidation
- Variance analysis & drill-down
- Template management
- Export to various formats
- User authentication & role-based access
- Audit trail

## Database

PostgreSQL (port assigned TBD — check /Users/andrewgoodwin/.claude/projects memory)

## Status

**Phase:** Initialization (structure created 2026-06-23)
