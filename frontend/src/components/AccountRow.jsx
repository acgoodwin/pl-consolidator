import React, { useState } from 'react';

const AccountRow = ({ account }) => {
  const [expanded, setExpanded] = useState(false);
  const hasChildren = account.children && account.children.length > 0;

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '—';
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const getVarianceClass = (status) => {
    switch (status) {
      case 'IMPROVED':
        return 'variance-improved';
      case 'DECLINED':
        return 'variance-declined';
      case 'STABLE':
      default:
        return 'variance-stable';
    }
  };

  const formatVariance = (amount, pct) => {
    if (pct === null || pct === undefined) return '—';
    const sign = amount >= 0 ? '+' : '';
    return `${sign}${pct.toFixed(1)}%`;
  };

  const rowClass = account.is_subtotal
    ? 'account-row subtotal'
    : account.is_header
    ? 'account-row header'
    : 'account-row';

  const indent = (account.level - 1) * 20;

  return (
    <>
      <div className={rowClass} style={{ paddingLeft: `${indent}px` }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {hasChildren && (
            <span
              className="expand-toggle"
              onClick={() => setExpanded(!expanded)}
              style={{ cursor: 'pointer' }}
            >
              {expanded ? '▼' : '▶'}
            </span>
          )}
          <div className="account-name">
            {account.name}
          </div>
        </div>

        <div className="account-value">
          {formatCurrency(account.amount_current_year)}
        </div>

        <div className="account-value">
          {formatCurrency(account.amount_prior_year)}
        </div>

        <div className={`variance-amount ${getVarianceClass(account.variance_status)}`}>
          {formatVariance(account.variance_amount, account.variance_pct)}
        </div>
      </div>

      {expanded && hasChildren && (
        <div>
          {account.children.map((child) => (
            <AccountRow key={child.id} account={child} />
          ))}
        </div>
      )}
    </>
  );
};

export default AccountRow;
