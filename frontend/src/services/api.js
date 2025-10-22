import axios from 'axios';
import { API_CONFIG } from '../config';

const API_BASE_URL = API_CONFIG.BASE_URL;

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout for file uploads
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Health check
export const healthCheck = () => api.get('/health');

// Test endpoint
export const testEndpoint = (data) => api.post('/test', data);

// Dashboard/General Data Processing
export const uploadFile = (file, sessionId = 'default') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  
  return api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const generateGraph = (data) => api.post('/generate_graph', data);
export const downloadGraph = (data) => api.post('/download_graph', data);

// NMD Analysis
export const nmdUploadFile = (file, sessionId = 'default') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  
  return api.post('/nmd_upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const nmdGenerateGraph = (data) => api.post('/nmd_generate_graph', data);

// Power Quality Analysis
export const pqUploadFeederNmd = (file, sessionId = 'default') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  
  return api.post('/pq_upload_feeder_nmd', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const pqUploadConsumer = (file, sessionId, consumerId, feederRef) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  formData.append('consumer_id', consumerId);
  formData.append('feeder_ref', feederRef);
  
  return api.post('/pq_upload_consumer', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const pqGenerateReport = (data) => api.post('/pq_generate_report', data);
export const pqDownloadReport = (data) => api.post('/pq_download_report', data);
export const pqDownloadPdf = (data) => api.post('/pq_download_pdf', data);
export const pqNetworkGraph = (data) => api.post('/pq_network_graph', data);

// NMD Analysis (New Feature)
export const nmdAnalysisUploadFeeder = (file, sessionId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  
  return api.post('/nmd-analysis/upload-feeder', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const nmdAnalysisUploadCustomers = (files, sessionId) => {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });
  formData.append('session_id', sessionId);
  
  return api.post('/nmd-analysis/upload-customers', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const nmdAnalysisAnalyze = (data) => api.post('/nmd-analysis/analyze', data);
export const nmdAnalysisVisualization = (data) => api.post('/nmd-analysis/visualization', data);

export const nmdAnalysisGetResults = (sessionId = 'default') => 
  api.get(`/nmd-analysis/results?session_id=${sessionId}`);

export const nmdAnalysisGetCorrectedData = (sessionId = 'default') => 
  api.get(`/nmd-analysis/corrected-data?session_id=${sessionId}`);

export const nmdAnalysisGetNetworkGraph = (data) => 
  api.post('/nmd-analysis/network-graph', data);

// Transformer Load Analysis
export const transformerLoadUpload = (file, sessionId = 'default') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  
  return api.post('/transformer_load/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const transformerLoadAnalyze = (data) => api.post('/transformer_load/analyze', data);
export const transformerLoadExportCsv = (data) => api.post('/transformer_load/export_csv', data);
export const transformerLoadExportPdf = (data) => api.post('/transformer_load/export_pdf', data);

export default api;
