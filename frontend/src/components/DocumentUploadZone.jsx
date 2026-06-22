import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDocument } from '../api';

const DocumentUploadZone = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(null);

  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) {
      setError('Please upload a PDF file');
      return;
    }

    const file = acceptedFiles[0];

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported');
      return;
    }

    setError(null);
    setUploading(true);
    setProgress(0);

    try {
      const response = await uploadDocument(file);

      // Simulate progress
      for (let i = 0; i <= 100; i += 20) {
        setProgress(i);
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      setProgress(null);
      onUploadSuccess(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Upload failed. Please try again.'
      );
      setProgress(null);
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    disabled: uploading,
  });

  return (
    <div className="card">
      <h2>Upload Financial Statement</h2>
      <p style={{ color: '#666', marginTop: '10px' }}>
        Upload a German annual financial statement (Jahresabschluss) PDF
      </p>

      {error && <div className="error" style={{ marginTop: '15px' }}>{error}</div>}

      <div
        {...getRootProps()}
        className={`upload-zone ${isDragActive ? 'active' : ''} ${uploading ? 'disabled' : ''}`}
        style={{ marginTop: '20px', opacity: uploading ? 0.6 : 1 }}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <>
            <div className="spinner"></div>
            <p>Uploading and extracting... {progress}%</p>
          </>
        ) : isDragActive ? (
          <p>📁 Drop your PDF here</p>
        ) : (
          <>
            <p style={{ fontSize: '24px', marginBottom: '10px' }}>📄</p>
            <p><strong>Drag and drop your PDF here</strong></p>
            <p>or click to select a file</p>
            <p style={{ fontSize: '12px', marginTop: '10px', color: '#999' }}>
              Max file size: 50MB
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default DocumentUploadZone;
