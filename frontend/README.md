# P&L Consolidator Frontend

React frontend for German financial statement analysis and consolidation.

## Setup

```bash
npm install
```

## Running Locally

The frontend runs on **port 3001** (configured in `.env.local`):

```bash
npm start
```

Then open: **http://localhost:3001**

Make sure the backend is running on port 8000:
```bash
cd ../backend
python -m app.main
```

## Building for Production

```bash
npm run build
```

## Features

- **Dashboard**: Upload German Jahresabschluss PDFs (annual financial statements)
- **Balance Sheet Viewer**: Interactive hierarchical P&L and balance sheet display
- **Variance Analysis**: Side-by-side comparison with Current Year vs Prior Year
- **German Formatting**: Proper number formatting (1.234.567,89 EUR)
- **Responsive Design**: Works on mobile, tablet, and desktop

## API Integration

Frontend communicates with backend API at `http://localhost:8000`:

- `POST /api/v1/documents/upload` - Upload PDF
- `GET /api/v1/documents` - List documents
- `GET /api/v1/balances/{id}` - Get balance sheet
- `GET /api/v1/variance/{id}` - Get variance analysis

See `src/api.js` for all API methods.

## Project Structure

```
src/
├── pages/          # Page components (Dashboard, BalanceSheet)
├── components/     # Reusable components (Upload, BalanceSheet, AccountRow)
├── api.js          # Axios API client
├── App.jsx         # Router setup
├── index.css       # Global styling
└── index.js        # React entry point
```

## Environment Variables

`.env.local`:
```
PORT=3001
BROWSER=none
```

## Technologies

- React 18
- React Router v6
- Axios
- react-dropzone (file upload)
- CSS Grid for layout
