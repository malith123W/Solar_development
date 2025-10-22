import React, { useState, useRef } from 'react';
import Plot from 'react-plotly.js';
import { nmdUploadFile, nmdGenerateGraph } from '../services/api';

const NMDAnalysis = () => {
  const [sessionId] = useState(`nmd_session_${Date.now()}`);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [customerRef, setCustomerRef] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [availableCustomers, setAvailableCustomers] = useState([]);
  
  const fileInputRef = useRef(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccess(null);
    setGraphData(null);
    setAvailableCustomers([]);

    try {
      const response = await nmdUploadFile(file, sessionId);
      setUploadedFile(file);
      setSuccess(`NMD file "${file.name}" uploaded successfully!`);
      
      // Extract customer references from response if available
      if (response.data && response.data.customer_refs) {
        setAvailableCustomers(response.data.customer_refs);
        if (response.data.customer_refs.length > 0) {
          setCustomerRef(response.data.customer_refs[0]);
        }
      }
      
      // Set default date range if available
      if (response.data && response.data.time_range) {
        const timeRange = response.data.time_range;
        if (timeRange.min_date && timeRange.max_date) {
          setStartDate(timeRange.min_date);
          setEndDate(timeRange.max_date);
        }
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to upload NMD file');
    } finally {
      setIsUploading(false);
    }
  };

  const handleGenerateGraph = async () => {
    if (!uploadedFile) {
      setError('Please upload a file first');
      return;
    }

    if (!customerRef) {
      setError('Please enter a customer reference');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await nmdGenerateGraph({
        session_id: sessionId,
        customer_ref: customerRef,
        start_date: startDate || null,
        end_date: endDate || null,
      });

      if (response.data && response.data.plot_data) {
        setGraphData(JSON.parse(response.data.plot_data));
        setSuccess('NMD graph generated successfully!');
      } else {
        setError('Failed to generate NMD graph data');
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to generate NMD graph');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="container">
      <div className="paper">
        {/* Header */}
        <div className="header">
          <h1>NMD Analysis</h1>
          <p>Analyze Network Metering Data with customer-specific visualizations</p>
        </div>

        {/* Alerts */}
        {error && (
          <div className="alert alert-error">
            <span>⚠️</span>
            <span>{error}</span>
            <button className="alert-close" onClick={() => setError(null)}>×</button>
          </div>
        )}
        {success && (
          <div className="alert alert-success">
            <span>✅</span>
            <span>{success}</span>
            <button className="alert-close" onClick={() => setSuccess(null)}>×</button>
          </div>
        )}

        <div className="grid grid-2">
          {/* Upload Section */}
          <div className="card">
            <div className="card-header">
              <span>📤</span>
              Upload NMD Data
            </div>
            
            <div
              className="upload-area"
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
              
              {isUploading ? (
                <div className="loading">
                  <div className="spinner"></div>
                  <span>Uploading...</span>
                </div>
              ) : (
                <>
                  <div className="upload-icon">📁</div>
                  <div className="upload-text">Click to upload NMD CSV file</div>
                  <div className="upload-subtext">Upload your Network Metering Data file</div>
                </>
              )}
            </div>

            {uploadedFile && (
              <div style={{ marginTop: '1rem' }}>
                <div className="file-name">✓ {uploadedFile.name} uploaded</div>
              </div>
            )}
          </div>

          {/* Controls Section */}
          <div className="card">
            <div className="card-header">
              <span>📊</span>
              Analysis Controls
            </div>

            <div className="form-group">
              <label className="form-label">Customer Reference</label>
              {availableCustomers.length > 0 ? (
                <select
                  className="form-select"
                  value={customerRef}
                  onChange={(e) => setCustomerRef(e.target.value)}
                >
                  {availableCustomers.map((customer) => (
                    <option key={customer} value={customer}>
                      {customer}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  className="form-control"
                  value={customerRef}
                  onChange={(e) => setCustomerRef(e.target.value)}
                  placeholder="Enter customer reference (e.g., 0700082108)"
                />
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Start Date</label>
              <input
                type="date"
                className="form-control"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">End Date</label>
              <input
                type="date"
                className="form-control"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>

            <button
              className="btn btn-primary"
              onClick={handleGenerateGraph}
              disabled={!uploadedFile || !customerRef || isGenerating}
              style={{ width: '100%', marginTop: '1rem' }}
            >
              {isGenerating ? (
                <div className="loading">
                  <div className="spinner"></div>
                  <span>Generating NMD Graph...</span>
                </div>
              ) : (
                <>
                  <span>📊</span>
                  Generate NMD Analysis
                </>
              )}
            </button>
          </div>
        </div>

        {/* Graph Display */}
        {graphData && (
          <div className="card">
            <div className="card-header">
              <span>📈</span>
              NMD Analysis Graph - Customer: {customerRef}
            </div>
            <div style={{ height: '500px' }}>
              <Plot
                data={graphData.data}
                layout={{
                  ...graphData.layout,
                  autosize: true,
                  height: 500,
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
              />
            </div>
          </div>
        )}

        {/* Information Section */}
        <div className="card">
          <div className="card-header">
            <span>ℹ️</span>
            About NMD Analysis
          </div>
          <div style={{ lineHeight: '1.6' }}>
            <p><strong>Network Metering Data (NMD)</strong> analysis helps you understand:</p>
            <ul style={{ marginLeft: '2rem', marginTop: '1rem' }}>
              <li>Customer-specific voltage and current patterns</li>
              <li>Time-series analysis of electrical parameters</li>
              <li>Identification of anomalies and trends</li>
              <li>Performance monitoring for specific customers</li>
            </ul>
            <p style={{ marginTop: '1rem' }}>
              <strong>How to use:</strong> Upload your NMD CSV file, select a customer reference, 
              optionally set date filters, and generate interactive visualizations.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NMDAnalysis;