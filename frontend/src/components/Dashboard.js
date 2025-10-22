import React, { useState, useRef } from 'react';
import Plot from 'react-plotly.js';
import { uploadFile, generateGraph, downloadGraph, testEndpoint } from '../services/api';

const Dashboard = () => {
  const [sessionId] = useState(`session_${Date.now()}`);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [parameterType, setParameterType] = useState('voltage');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [formatType, setFormatType] = useState('png');
  const [availableParameters, setAvailableParameters] = useState([]);
  
  const fileInputRef = useRef(null);

  const parameterTypes = [
    { value: 'voltage', label: 'Voltage' },
    { value: 'current', label: 'Current' },
    { value: 'power_factor', label: 'Power Factor' },
    { value: 'power', label: 'Power (kW)' },
    { value: 'energy', label: 'Energy (kWh)' },
    { value: 'reactive_power', label: 'Reactive Power (kvarh)' },
    { value: 'apparent_power', label: 'Apparent Power (kVA)' },
  ];

  const formatTypes = [
    { value: 'png', label: 'PNG' },
    { value: 'jpg', label: 'JPG' },
    { value: 'pdf', label: 'PDF' },
    { value: 'svg', label: 'SVG' },
  ];

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
    setAvailableParameters([]);

    try {
      console.log('Uploading file:', file.name, 'Session ID:', sessionId);
      const response = await uploadFile(file, sessionId);
      console.log('Upload response:', response);
      setUploadedFile(file);
      setSuccess(`File "${file.name}" uploaded successfully!`);
      
      // Set default date range if available
      if (response.data && response.data.time_range) {
        const timeRange = response.data.time_range;
        if (timeRange.min_date && timeRange.max_date) {
          setStartDate(timeRange.min_date);
          setEndDate(timeRange.max_date);
        }
      }
      
      // Set available parameters based on data info
      if (response.data && response.data.data_info) {
        const dataInfo = response.data.data_info;
        const available = [];
        
        Object.keys(dataInfo).forEach(key => {
          if (dataInfo[key].available) {
            const paramType = parameterTypes.find(p => p.value === key);
            if (paramType) {
              available.push(paramType);
            }
          }
        });
        
        setAvailableParameters(available);
        
        // Set first available parameter as default if current one is not available
        if (available.length > 0 && !available.find(p => p.value === parameterType)) {
          setParameterType(available[0].value);
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      console.error('Error response:', error.response);
      setError(error.response?.data?.error || error.message || 'Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  };

  const handleGenerateGraph = async () => {
    if (!uploadedFile) {
      setError('Please upload a file first');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      console.log('Generating graph with data:', {
        session_id: sessionId,
        parameter_type: parameterType,
        start_date: startDate || null,
        end_date: endDate || null,
      });

      const response = await generateGraph({
        session_id: sessionId,
        parameter_type: parameterType,
        start_date: startDate || null,
        end_date: endDate || null,
      });

      console.log('Graph generation response:', response);

      if (response.data && response.data.plot_data) {
        setGraphData(JSON.parse(response.data.plot_data));
        setSuccess('Graph generated successfully!');
      } else {
        console.error('No plot_data in response:', response.data);
        setError('Failed to generate graph data - no plot data received');
      }
    } catch (error) {
      console.error('Graph generation error:', error);
      console.error('Error response:', error.response);
      setError(error.response?.data?.error || error.message || 'Failed to generate graph');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      console.log('Testing API connection...');
      const response = await testEndpoint({ test: 'data', timestamp: Date.now() });
      console.log('Test response:', response);
      setSuccess('API connection test successful!');
    } catch (error) {
      console.error('Test connection error:', error);
      setError('API connection test failed: ' + (error.message || 'Unknown error'));
    }
  };

  const handleDownloadGraph = async () => {
    if (!uploadedFile) {
      setError('Please upload a file first');
      return;
    }

    setIsDownloading(true);
    setError(null);

    try {
      const response = await downloadGraph({
        session_id: sessionId,
        parameter_type: parameterType,
        format: formatType,
        start_date: startDate || null,
        end_date: endDate || null,
      });

      // Create download link
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `graph_${parameterType}_${Date.now()}.${formatType}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setSuccess('Graph downloaded successfully!');
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to download graph');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="container">
      <div className="paper">
        {/* Header */}
        <div className="header">
          <h1>Electrical Data Analyzer</h1>
          <p>Upload CSV files and generate interactive visualizations</p>
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
              Upload Data
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
                  <div className="upload-text">Click to upload CSV file</div>
                  <div className="upload-subtext">or drag and drop your file here</div>
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
              Graph Controls
            </div>

            <div className="form-group">
              <label className="form-label">Parameter Type</label>
              <select
                className="form-select"
                value={parameterType}
                onChange={(e) => setParameterType(e.target.value)}
              >
                {(availableParameters.length > 0 ? availableParameters : parameterTypes).map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Format</label>
              <select
                className="form-select"
                value={formatType}
                onChange={(e) => setFormatType(e.target.value)}
              >
                {formatTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
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

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
              <button
                className="btn btn-primary"
                onClick={handleGenerateGraph}
                disabled={!uploadedFile || isGenerating}
                style={{ flex: 1 }}
              >
                {isGenerating ? (
                  <div className="loading">
                    <div className="spinner"></div>
                    <span>Generating...</span>
                  </div>
                ) : (
                  <>
                    <span>📊</span>
                    Generate Graph
                  </>
                )}
              </button>
              
              <button
                className="btn btn-outline"
                onClick={handleDownloadGraph}
                disabled={!uploadedFile || isDownloading}
                style={{ flex: 1 }}
              >
                {isDownloading ? (
                  <div className="loading">
                    <div className="spinner"></div>
                    <span>Downloading...</span>
                  </div>
                ) : (
                  <>
                    <span>💾</span>
                    Download
                  </>
                )}
              </button>
            </div>

            <div style={{ marginTop: '1rem' }}>
              <button
                className="btn btn-secondary"
                onClick={handleTestConnection}
                style={{ width: '100%' }}
              >
                <span>🔧</span>
                Test API Connection
              </button>
            </div>
          </div>
        </div>

        {/* Graph Display */}
        {graphData && (
          <div className="card">
            <div className="card-header">
              <span>📈</span>
              Generated Graph
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

        {/* Features Overview */}
        <div className="card">
          <div className="card-header">
            <span>🚀</span>
            Available Features
          </div>
          <div className="feature-grid">
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <div className="feature-title">Dashboard</div>
              <div className="feature-description">
                Upload CSV files and generate interactive visualizations with customizable parameters and date ranges.
              </div>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📈</div>
              <div className="feature-title">NMD Analysis</div>
              <div className="feature-description">
                Analyze Network Metering Data with customer-specific visualizations and time-series analysis.
              </div>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔬</div>
              <div className="feature-title">Advanced NMD</div>
              <div className="feature-description">
                Perform correlation analysis between customers and feeders with statistical insights.
              </div>
            </div>
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <div className="feature-title">Power Quality</div>
              <div className="feature-description">
                Comprehensive power quality analysis with PDF report generation and multi-consumer support.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;