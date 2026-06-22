# P&L Consolidator - Setup Guide

## Port Configuration

- **Backend (FastAPI)**: Port **8000**
- **Frontend (React)**: Port **8001**
- Backend API: `http://localhost:8000`
- Frontend UI: `http://localhost:8001`

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Create .env (copy from .env.example)
cp .env.example .env

# Start backend
python -m app.main
```

Backend will run on **http://localhost:8000**  
API docs: **http://localhost:8000/docs**

### 2. Frontend Setup (NEW TERMINAL)

```bash
cd frontend

# Install dependencies (one time only)
npm install

# Create .env.local (already created)
# cat .env.local  # should show PORT=8001

# Start frontend
npm start
```

Frontend will run on **http://localhost:8001**  
Auto-opens at: **http://localhost:8001**

## Database Setup

### Option A: PostgreSQL (Recommended)
```bash
# Create database
createdb pl_consolidator

# Run migrations
cd backend
alembic upgrade head
```

### Option B: Docker
```bash
docker run --name pl-consolidator-db \
  -e POSTGRES_DB=pl_consolidator \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=devpass \
  -p 5432:5432 \
  postgres:15
```

## Running Tests

```bash
cd backend
pytest                      # All tests
pytest --cov=app tests/    # With coverage report
```

## Troubleshooting

### Port Already in Use

Check what's using the ports:
```bash
# macOS/Linux
lsof -i :8000
lsof -i :8001

# Find alternative ports (if needed)
for port in 8000 8001 8010 8020; do
  (echo > /dev/tcp/localhost/$port) 2>/dev/null && echo "Port $port: IN USE" || echo "Port $port: AVAILABLE"
done
```

### Frontend won't start

1. Make sure `.env.local` exists with `PORT=8001`
2. Check if npm is installed: `npm --version`
3. Clear npm cache: `npm cache clean --force`
4. Delete `node_modules` and `package-lock.json`, then `npm install` again

### Backend won't start

1. Check if Python 3.11+ is installed: `python --version`
2. Make sure all dependencies installed: `pip install -r requirements.txt`
3. Check if PostgreSQL is running and accessible
4. Run migrations: `alembic upgrade head`

### API connection fails

1. Make sure backend is running on port 8000
2. Check `CORS_ORIGINS` in backend/.env includes `http://localhost:8001`
3. Frontend `.env.local` should have `REACT_APP_API_URL=http://localhost:8000`

## Full Workflow

1. **Terminal 1 - Backend**
   ```bash
   cd ~/AG_Code/pl-consolidator/backend
   source venv/bin/activate
   python -m app.main
   # Runs on http://localhost:8000
   ```

2. **Terminal 2 - Frontend**
   ```bash
   cd ~/AG_Code/pl-consolidator/frontend
   npm start
   # Runs on http://localhost:8001
   ```

3. **Terminal 3 - Optional: Tests**
   ```bash
   cd ~/AG_Code/pl-consolidator/backend
   source venv/bin/activate
   pytest --cov=app tests/
   ```

4. **Browser**
   - Open: **http://localhost:8001**
   - Upload your Jahresabschluss PDF
   - View balance sheet with variances

## Environment Files

### Backend: `backend/.env`
```
DATABASE_URL=postgresql://app:devpass@localhost:5432/pl_consolidator
ENVIRONMENT=development
LOG_LEVEL=DEBUG
UPLOAD_FOLDER=/tmp/pl-consolidator-uploads
MAX_FILE_SIZE_MB=50
CORS_ORIGINS=http://localhost:8001,http://localhost:3000,http://localhost:3001
```

### Frontend: `frontend/.env.local`
```
PORT=8001
BROWSER=none
REACT_APP_API_URL=http://localhost:8000
```

## GitHub Repository

Push/Pull from: **https://github.com/acgoodwin/pl-consolidator**

```bash
git remote -v  # should show origin -> GitHub URL
git push origin main
git pull origin main
```

## Next Steps

1. ✅ Backend running on :8000
2. ✅ Frontend running on :8001
3. ✅ Database connected
4. 📋 Upload a test PDF
5. 📊 View balance sheet
6. 📤 Test export features (coming soon)

---

**Any issues?** Check ports, environment files, and database connection.
