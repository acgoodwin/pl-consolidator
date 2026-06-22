import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DocumentUploadZone from '../components/DocumentUploadZone';
import DocumentList from '../components/DocumentList';

const DashboardPage = () => {
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const navigate = useNavigate();

  const handleUploadSuccess = (data) => {
    setUploadSuccess(data);
    setRefreshKey(prev => prev + 1);

    // Auto-navigate to balance sheet after upload
    if (data.extraction_status === 'SUCCESS' || data.extraction_status === 'PENDING') {
      setTimeout(() => {
        navigate(`/balance-sheet/${data.document_id}`);
      }, 1000);
    }
  };

  return (
    <div className="container">
      <DocumentUploadZone onUploadSuccess={handleUploadSuccess} />

      {uploadSuccess && (
        <div className="success" style={{ marginTop: '20px' }}>
          ✓ Document uploaded successfully! Extraction status: {uploadSuccess.extraction_status}
        </div>
      )}

      <DocumentList key={refreshKey} />
    </div>
  );
};

export default DashboardPage;
