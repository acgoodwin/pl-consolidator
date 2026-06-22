import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getBalanceSheet } from '../api';
import BalanceSheetComparison from '../components/BalanceSheetComparison';

const BalanceSheetPage = () => {
  const { documentId } = useParams();
  const navigate = useNavigate();
  const [balanceSheet, setBalanceSheet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBalanceSheet();
    const interval = setInterval(fetchBalanceSheet, 2000);
    return () => clearInterval(interval);
  }, [documentId]);

  const fetchBalanceSheet = async () => {
    try {
      const response = await getBalanceSheet(documentId);
      setBalanceSheet(response.data);
      setError(null);
      setLoading(false);
    } catch (err) {
      if (err.response?.status === 400 && err.response?.data?.detail?.includes('not completed')) {
        // Still extracting, retry in a moment
        setLoading(true);
      } else {
        setError(err.response?.data?.detail || 'Failed to load balance sheet');
        setLoading(false);
      }
    }
  };

  const handleExport = async (format) => {
    // Export functionality will be implemented in Step 3b
    alert(`Export to ${format} - coming soon!`);
  };

  if (loading && !balanceSheet) {
    return (
      <div className="container">
        <div className="spinner"></div>
        <p style={{ textAlign: 'center', marginTop: '20px', color: '#666' }}>
          Loading balance sheet... (refreshing every 2 seconds)
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <button onClick={() => navigate('/')} className="secondary" style={{ marginBottom: '20px' }}>
          ← Back to Dashboard
        </button>
        <div className="error">{error}</div>
      </div>
    );
  }

  if (!balanceSheet) {
    return <div className="container">No data available</div>;
  }

  return (
    <div className="container">
      <button onClick={() => navigate('/')} className="secondary" style={{ marginBottom: '20px' }}>
        ← Back to Dashboard
      </button>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1>{balanceSheet.company_name || 'Company'}</h1>
            <p style={{ color: '#666', marginTop: '5px' }}>
              Bilanz zum 31.12.{balanceSheet.fiscal_year}
            </p>
            {balanceSheet.extracted_date && (
              <p style={{ color: '#999', fontSize: '12px', marginTop: '3px' }}>
                Extracted: {new Date(balanceSheet.extracted_date).toLocaleString()}
              </p>
            )}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => handleExport('EXCEL')}>📊 Export Excel</button>
            <button onClick={() => handleExport('PDF')} className="secondary">
              📄 Export PDF
            </button>
          </div>
        </div>
      </div>

      {balanceSheet.extraction_status !== 'SUCCESS' && (
        <div className="info" style={{ marginTop: '20px' }}>
          ℹ️ Extraction Status: {balanceSheet.extraction_status} | Validation: {balanceSheet.validation_status}
        </div>
      )}

      <BalanceSheetComparison
        assets={balanceSheet.assets}
        liabilities={balanceSheet.liabilities}
        equity={balanceSheet.equity}
        totalAssets={balanceSheet.total_assets}
        totalLiabilities={balanceSheet.total_liabilities}
        totalEquity={balanceSheet.total_equity}
        isBalanced={balanceSheet.is_balanced}
      />
    </div>
  );
};

export default BalanceSheetPage;
