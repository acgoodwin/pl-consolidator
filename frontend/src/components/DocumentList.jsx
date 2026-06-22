import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listDocuments, deleteDocument } from '../api';

const DocumentList = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await listDocuments(0, 20);
      setDocuments(response.data.documents);
      setError(null);
    } catch (err) {
      setError('Failed to load documents');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await deleteDocument(documentId);
      setDocuments(documents.filter(doc => doc.id !== documentId));
    } catch (err) {
      setError('Failed to delete document');
    }
  };

  const getStatusBadge = (status) => {
    const badgeClass = `badge ${status.toLowerCase()}`;
    return <span className={badgeClass}>{status}</span>;
  };

  if (loading) {
    return <div className="spinner"></div>;
  }

  return (
    <div className="card">
      <h2>Recent Documents</h2>

      {error && <div className="error">{error}</div>}

      {documents.length === 0 ? (
        <p style={{ color: '#999', marginTop: '20px' }}>
          No documents uploaded yet. Upload one to get started!
        </p>
      ) : (
        <table style={{ marginTop: '20px' }}>
          <thead>
            <tr>
              <th>Company</th>
              <th>Fiscal Year</th>
              <th>Type</th>
              <th>Extraction Status</th>
              <th>Validation</th>
              <th>Uploaded</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.file_name}</td>
                <td>{doc.fiscal_year}</td>
                <td>{doc.document_type}</td>
                <td>{getStatusBadge(doc.extraction_status)}</td>
                <td>{getStatusBadge(doc.validation_status)}</td>
                <td>{new Date(doc.upload_date).toLocaleDateString()}</td>
                <td>
                  <button
                    onClick={() => navigate(`/balance-sheet/${doc.id}`)}
                    style={{ marginRight: '10px' }}
                  >
                    View
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="danger"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default DocumentList;
