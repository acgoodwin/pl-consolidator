import axios from 'axios';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Document API
export const uploadDocument = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const getDocument = (documentId) => {
  return api.get(`/documents/${documentId}`);
};

export const listDocuments = (skip = 0, limit = 10, companyId = null) => {
  const params = { skip, limit };
  if (companyId) params.company_id = companyId;
  return api.get('/documents', { params });
};

export const deleteDocument = (documentId) => {
  return api.delete(`/documents/${documentId}`);
};

// Balance Sheet API
export const getBalanceSheet = (documentId) => {
  return api.get(`/balances/${documentId}`);
};

export const getVarianceAnalysis = (documentId) => {
  return api.get(`/variance/${documentId}`);
};

export default api;
