import React, { useState } from 'react';
import AccountRow from './AccountRow';

const BalanceSheetComparison = ({ assets, liabilities, equity, totalAssets, totalLiabilities, totalEquity, isBalanced }) => {
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '—';
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const assetTotal = totalAssets || 0;
  const liabilityTotal = totalLiabilities || 0;
  const equityTotal = totalEquity || 0;
  const liabilityEquityTotal = liabilityTotal + equityTotal;
  const variance = assetTotal - liabilityEquityTotal;

  return (
    <div>
      {!isBalanced && (
        <div className="error" style={{ marginBottom: '20px' }}>
          ⚠️ Balance sheet does not balance. Variance: {formatCurrency(variance)}
        </div>
      )}

      <div className="balance-sheet">
        {/* Assets Column */}
        <div className="balance-section">
          <h3>AKTIVA (Assets)</h3>

          {assets.map((account) => (
            <AccountRow key={account.id} account={account} />
          ))}

          <div className="account-row subtotal">
            <div className="account-name">
              <strong>Total Assets</strong>
            </div>
            <div></div>
            <div></div>
            <div className="account-value" style={{ textAlign: 'right' }}>
              <strong>{formatCurrency(assetTotal)}</strong>
            </div>
          </div>
        </div>

        {/* Liabilities & Equity Column */}
        <div className="balance-section">
          <h3>PASSIVA (Liabilities & Equity)</h3>

          {/* Liabilities */}
          {liabilities.length > 0 && (
            <>
              <div style={{ marginTop: '15px', marginBottom: '10px' }}>
                <strong style={{ fontSize: '13px', color: '#666' }}>Liabilities</strong>
              </div>
              {liabilities.map((account) => (
                <AccountRow key={account.id} account={account} />
              ))}
            </>
          )}

          {/* Equity */}
          {equity.length > 0 && (
            <>
              <div style={{ marginTop: '15px', marginBottom: '10px' }}>
                <strong style={{ fontSize: '13px', color: '#666' }}>Equity</strong>
              </div>
              {equity.map((account) => (
                <AccountRow key={account.id} account={account} />
              ))}
            </>
          )}

          <div className="account-row subtotal" style={{ marginTop: '20px' }}>
            <div className="account-name">
              <strong>Total Liabilities & Equity</strong>
            </div>
            <div></div>
            <div></div>
            <div className="account-value" style={{ textAlign: 'right' }}>
              <strong>{formatCurrency(liabilityEquityTotal)}</strong>
            </div>
          </div>

          {!isBalanced && (
            <div className="account-row" style={{ backgroundColor: '#fff3cd', marginTop: '10px' }}>
              <div className="account-name" style={{ color: '#856404' }}>
                <strong>Balance Variance</strong>
              </div>
              <div></div>
              <div></div>
              <div className="account-value" style={{ textAlign: 'right', color: '#856404', fontWeight: 'bold' }}>
                {formatCurrency(variance)}
              </div>
            </div>
          )}
        </div>
      </div>

      {isBalanced && (
        <div className="success" style={{ marginTop: '20px', textAlign: 'center' }}>
          ✓ Balance sheet is balanced (Assets = Liabilities + Equity)
        </div>
      )}
    </div>
  );
};

export default BalanceSheetComparison;
