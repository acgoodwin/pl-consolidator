import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import BalanceSheetPage from './pages/BalanceSheetPage';
import './index.css';

function App() {
  return (
    <Router>
      <header>
        <div className="container">
          <h1>📊 P&L Consolidator</h1>
          <p>German Financial Statement Analysis & Consolidation</p>
          <nav>
            <Link to="/">Dashboard</Link>
            <a href="#help" style={{ color: '#666' }}>Help</a>
          </nav>
        </div>
      </header>

      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/balance-sheet/:documentId" element={<BalanceSheetPage />} />
        <Route path="*" element={<div className="container"><h2>Page not found</h2></div>} />
      </Routes>

      <footer style={{ textAlign: 'center', padding: '20px', color: '#999', fontSize: '12px', marginTop: '40px' }}>
        <p>P&L Consolidator v0.1.0 | German HGB Financial Statements</p>
      </footer>
    </Router>
  );
}

export default App;
