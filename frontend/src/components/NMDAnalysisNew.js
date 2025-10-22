import React, { useState, useRef } from 'react';
import Plot from 'react-plotly.js';
import NetworkGraph from './NetworkGraph';
import { 
  nmdAnalysisUploadFeeder, 
  nmdAnalysisUploadCustomers, 
  nmdAnalysisAnalyze, 
  nmdAnalysisVisualization,
  nmdAnalysisGetCorrectedData,
  nmdAnalysisGetNetworkGraph
} from '../services/api';

const NMDAnalysisNew = () => {
  const [sessionId] = useState(`nmd_analysis_${Date.now()}`);
  const [feederFile, setFeederFile] = useState(null);
  const [customerFiles, setCustomerFiles] = useState([]);
  const [isUploadingFeeder, setIsUploadingFeeder] = useState(false);
  const [isUploadingCustomers, setIsUploadingCustomers] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGeneratingVisualization, setIsGeneratingVisualization] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [visualizationData, setVisualizationData] = useState(null);
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [selectedFeeder, setSelectedFeeder] = useState('FEEDER_001');
  const [availableCustomers, setAvailableCustomers] = useState([]);
  const [availableFeeders, setAvailableFeeders] = useState(['FEEDER_001']);
  const [correctedData, setCorrectedData] = useState(null);
  const [isGeneratingCorrectedData, setIsGeneratingCorrectedData] = useState(false);
  const [networkGraphData, setNetworkGraphData] = useState(null);
  const [isGeneratingNetworkGraph, setIsGeneratingNetworkGraph] = useState(false);
  const [transformerName, setTransformerName] = useState('Transformer');
  
  const feederInputRef = useRef(null);
  const customerInputRef = useRef(null);

  const handleFeederUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }

    setIsUploadingFeeder(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await nmdAnalysisUploadFeeder(file, sessionId);
      setFeederFile(file);
      setSuccess(`Feeder file "${file.name}" uploaded successfully!`);
      
      if (response.data && response.data.feeders) {
        setAvailableFeeders(response.data.feeders);
        if (response.data.feeders.length > 0) {
          setSelectedFeeder(response.data.feeders[0]);
        }
      }
      
      // Also check for feeder_info in the response
      if (response.data && response.data.feeder_info && response.data.feeder_info.all_feeder_refs) {
        setAvailableFeeders(response.data.feeder_info.all_feeder_refs);
        if (response.data.feeder_info.all_feeder_refs.length > 0) {
          setSelectedFeeder(response.data.feeder_info.all_feeder_refs[0]);
        }
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to upload feeder file');
    } finally {
      setIsUploadingFeeder(false);
    }
  };

  const handleCustomerUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    const invalidFiles = files.filter(file => !file.name.endsWith('.csv'));
    if (invalidFiles.length > 0) {
      setError('Please upload only CSV files');
      return;
    }

    setIsUploadingCustomers(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await nmdAnalysisUploadCustomers(files, sessionId);
      setCustomerFiles(prev => [...prev, ...files]);
      setSuccess(`${files.length} customer file(s) uploaded successfully!`);
      
      if (response.data && response.data.customers) {
        setAvailableCustomers(response.data.customers);
        if (response.data.customers.length > 0) {
          setSelectedCustomer(response.data.customers[0]);
        }
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to upload customer files');
    } finally {
      setIsUploadingCustomers(false);
    }
  };

  const handleAnalyze = async () => {
    if (!feederFile || customerFiles.length === 0) {
      setError('Please upload both feeder and customer files');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await nmdAnalysisAnalyze({
        session_id: sessionId,
      });

      setAnalysisData(response.data);
      setSuccess('Correlation analysis completed successfully!');
      
      // Automatically generate network graph after analysis
      // Don't wait for state update, generate immediately
      generateNetworkGraph();
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to perform analysis');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const generateNetworkGraph = async () => {
    setIsGeneratingNetworkGraph(true);

    try {
      const response = await nmdAnalysisGetNetworkGraph({
        session_id: sessionId,
        transformer_name: transformerName
      });

      if (response.data && response.data.graph_data) {
        setNetworkGraphData(response.data.graph_data);
        console.log('Network graph data:', response.data.graph_data);
      } else {
        console.error('No graph data in response');
      }
    } catch (error) {
      console.error('Network graph error:', error);
      // Don't show error to user, just log it
    } finally {
      setIsGeneratingNetworkGraph(false);
    }
  };

  const handleGenerateNetworkGraph = async () => {
    if (!analysisData) {
      setError('Please run analysis first');
      return;
    }
    await generateNetworkGraph();
  };

  const handleGenerateVisualization = async () => {
    if (!selectedCustomer) {
      setError('Please select a customer for visualization');
      return;
    }

    setIsGeneratingVisualization(true);
    setError(null);

    try {
      const response = await nmdAnalysisVisualization({
        session_id: sessionId,
        customer_id: selectedCustomer,
        feeder_id: selectedFeeder,
      });

      if (response.data && response.data.plot_data) {
        setVisualizationData(JSON.parse(response.data.plot_data));
        setSuccess('Visualization generated successfully!');
      } else {
        setError('Failed to generate visualization data');
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to generate visualization');
    } finally {
      setIsGeneratingVisualization(false);
    }
  };

  const handleGenerateCorrectedData = async () => {
    if (!analysisData) {
      setError('Please run analysis first');
      return;
    }

    setIsGeneratingCorrectedData(true);
    setError(null);

    try {
      const response = await nmdAnalysisGetCorrectedData(sessionId);
      setCorrectedData(response.data);
      setSuccess('Corrected data generated successfully!');
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to generate corrected data');
    } finally {
      setIsGeneratingCorrectedData(false);
    }
  };

  const removeCustomerFile = (index) => {
    setCustomerFiles(prev => prev.filter((_, i) => i !== index));
  };

  const getCorrelationColor = (value) => {
    const absValue = Math.abs(value);
    if (absValue > 0.7) return '#28a745'; // Strong correlation - green
    if (absValue > 0.5) return '#ffc107'; // Moderate correlation - yellow
    return '#6c757d'; // Weak correlation - gray
  };

  const getCorrelationStrength = (value) => {
    const absValue = Math.abs(value);
    if (absValue > 0.7) return 'Strong';
    if (absValue > 0.5) return 'Moderate';
    if (absValue > 0.3) return 'Weak';
    return 'Very Weak';
  };

  return (
    <div className="container">
      <div className="paper">
        {/* Header */}
        <div className="header">
          <h1>NMD Analysis - Feeder-Customer Correlation</h1>
          <p>Advanced correlation analysis between customers and feeders</p>
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
          {/* Feeder Upload */}
          <div className="card">
            <div className="card-header">
              <span>📤</span>
              Upload Feeder NMD
            </div>
            
            <div
              className="upload-area"
              onClick={() => feederInputRef.current?.click()}
            >
              <input
                ref={feederInputRef}
                type="file"
                accept=".csv"
                onChange={handleFeederUpload}
                style={{ display: 'none' }}
              />
              
              {isUploadingFeeder ? (
                <div className="loading">
                  <div className="spinner"></div>
                  <span>Uploading...</span>
                </div>
              ) : (
                <>
                  <div className="upload-icon">📁</div>
                  <div className="upload-text">Upload Feeder NMD File</div>
                  <div className="upload-subtext">Upload feeder network metering data</div>
                </>
              )}
            </div>

            {feederFile && (
              <div style={{ marginTop: '1rem' }}>
                <div className="file-name">✓ {feederFile.name} uploaded</div>
              </div>
            )}
          </div>

          {/* Customer Upload */}
          <div className="card">
            <div className="card-header">
              <span>📤</span>
              Upload Customer Data
            </div>
            
            <div
              className="upload-area"
              onClick={() => customerInputRef.current?.click()}
            >
              <input
                ref={customerInputRef}
                type="file"
                accept=".csv"
                multiple
                onChange={handleCustomerUpload}
                style={{ display: 'none' }}
              />
              
              {isUploadingCustomers ? (
                <div className="loading">
                  <div className="spinner"></div>
                  <span>Uploading...</span>
                </div>
              ) : (
                <>
                  <div className="upload-icon">📁</div>
                  <div className="upload-text">Upload Customer Files</div>
                  <div className="upload-subtext">Upload multiple customer data files</div>
                </>
              )}
            </div>

            {customerFiles.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <div className="file-name">✓ {customerFiles.length} file(s) uploaded</div>
                <ul className="file-list">
                  {customerFiles.map((file, index) => (
                    <li key={index} className="file-item">
                      <span className="file-name">{file.name}</span>
                      <button 
                        className="file-remove"
                        onClick={() => removeCustomerFile(index)}
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Analysis Controls */}
        <div className="card">
          <div className="card-header">
            <span>🔬</span>
            Correlation Analysis
          </div>

          <button
            className="btn btn-primary"
            onClick={handleAnalyze}
            disabled={!feederFile || customerFiles.length === 0 || isAnalyzing}
            style={{ width: '100%' }}
          >
            {isAnalyzing ? (
              <div className="loading">
                <div className="spinner"></div>
                <span>Analyzing...</span>
              </div>
            ) : (
              <>
                <span>🔬</span>
                Perform Correlation Analysis
              </>
            )}
          </button>

          {analysisData && analysisData.results && (
            <div style={{ marginTop: '2rem' }}>
              <div className="card-header">
                <span>📊</span>
                Analysis Results
              </div>
              
              {/* Summary Statistics */}
              {analysisData.results.summary_stats && (
                <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#e3f2fd', borderRadius: '8px' }}>
                  <h4>Summary Statistics:</h4>
                  <div className="grid grid-3" style={{ marginTop: '0.5rem' }}>
                    <div className="stat-item">
                      <strong>Avg Correlation:</strong> {analysisData.results.summary_stats.avg_correlation.toFixed(3)}
                    </div>
                    <div className="stat-item">
                      <strong>Max Correlation:</strong> {analysisData.results.summary_stats.max_correlation.toFixed(3)}
                    </div>
                    <div className="stat-item">
                      <strong>Avg RMSE:</strong> {analysisData.results.summary_stats.avg_rmse.toFixed(2)}V
                    </div>
                  </div>
                </div>
              )}

              {/* Customer Assignments Table */}
              {analysisData.results.assignments && analysisData.results.assignments.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  <h4>Customer-Feeder Assignments:</h4>
                  <div className="table-container">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Customer ID</th>
                          <th>Assigned Feeder</th>
                          <th>Correlation</th>
                          <th>RMSE (V)</th>
                          <th>Aligned Points</th>
                          <th>Quality</th>
                          <th>Phase Analysis</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analysisData.results.assignments.map((assignment, index) => (
                          <tr key={index}>
                            <td>{assignment.customer_id}</td>
                            <td>{assignment.assigned_feeder}</td>
                            <td>
                              <span 
                                className="correlation-badge"
                                style={{ 
                                  backgroundColor: getCorrelationColor(assignment.correlation),
                                  color: 'white',
                                  padding: '0.25rem 0.5rem',
                                  borderRadius: '4px',
                                  fontSize: '0.875rem'
                                }}
                              >
                                {assignment.correlation.toFixed(3)}
                              </span>
                            </td>
                            <td>{assignment.rmse.toFixed(2)}</td>
                            <td>{assignment.aligned_points}</td>
                            <td>
                              <span 
                                className="quality-badge"
                                style={{ 
                                  backgroundColor: getCorrelationColor(assignment.correlation),
                                  color: 'white',
                                  padding: '0.25rem 0.5rem',
                                  borderRadius: '4px',
                                  fontSize: '0.875rem'
                                }}
                              >
                                {getCorrelationStrength(assignment.correlation)}
                              </span>
                            </td>
                            <td>
                              {assignment.phase_assignments && assignment.phase_assignments.length > 0 ? (
                                <div style={{ fontSize: '0.8rem' }}>
                                  {assignment.phase_assignments.map((phase, idx) => (
                                    <div key={idx} style={{ marginBottom: '0.25rem' }}>
                                      <strong>{phase.customer_phase}</strong> → {phase.assigned_feeder_phase}
                                      <br />
                                      <span style={{ color: '#666' }}>
                                        r={phase.correlation.toFixed(3)}, RMSE={phase.rmse.toFixed(1)}V
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <span style={{ color: '#999' }}>No phase data</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Feeder-wise Grouping */}
              {analysisData.results.feeder_summary && Object.keys(analysisData.results.feeder_summary).length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  <h4>Feeder-wise Customer Grouping:</h4>
                  {Object.entries(analysisData.results.feeder_summary).map(([feederId, customers]) => (
                    <div key={feederId} style={{ marginTop: '0.5rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                      <h5>Feeder: {feederId} ({customers.length} customers)</h5>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
                        {customers.map((customer, index) => (
                          <div
                            key={index}
                            className="chip"
                            style={{ 
                              backgroundColor: getCorrelationColor(customer.correlation),
                              color: 'white',
                              cursor: 'default'
                            }}
                          >
                            {customer.customer_id} (r={customer.correlation.toFixed(3)})
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Network Graph Section */}
              <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h4 style={{ margin: 0 }}>🌳 Network Hierarchy Graph</h4>
                  <button
                    onClick={handleGenerateNetworkGraph}
                    disabled={isGeneratingNetworkGraph || !analysisData}
                    style={{
                      padding: '0.5rem 1rem',
                      backgroundColor: isGeneratingNetworkGraph ? '#6c757d' : '#007bff',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: isGeneratingNetworkGraph ? 'not-allowed' : 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    {isGeneratingNetworkGraph ? '⏳ Generating...' : '🔄 Generate Network Graph'}
                  </button>
                </div>
                
                {networkGraphData ? (
                  <NetworkGraph 
                    graphData={networkGraphData} 
                    width={1200} 
                    height={800} 
                  />
                ) : !isGeneratingNetworkGraph ? (
                  <div style={{ padding: '20px', textAlign: 'center', color: '#6c757d', backgroundColor: 'white', borderRadius: '4px' }}>
                    <p>📊 Click "Generate Network Graph" to visualize the transformer → feeder → phase → customer hierarchy</p>
                  </div>
                ) : (
                  <div style={{ padding: '20px', textAlign: 'center', color: '#007bff', backgroundColor: 'white', borderRadius: '4px' }}>
                    <p>⏳ Generating network graph...</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Corrected Data Generation */}
        {analysisData && (
          <div className="card">
            <div className="card-header">
              <span>🔄</span>
              Phase Correction & Data Export
            </div>

            <div style={{ padding: '1rem' }}>
              <p style={{ marginBottom: '1rem', color: '#666' }}>
                Generate corrected customer data with proper phase labels based on correlation analysis.
                Single-phase customers will be assigned to the correct feeder phase, and three-phase 
                customers will have their phases properly aligned.
              </p>

              <button
                className="btn btn-primary"
                onClick={handleGenerateCorrectedData}
                disabled={isGeneratingCorrectedData}
                style={{ width: '100%' }}
              >
                {isGeneratingCorrectedData ? (
                  <div className="loading">
                    <div className="spinner"></div>
                    <span>Generating...</span>
                  </div>
                ) : (
                  <>
                    <span>🔄</span>
                    Generate Corrected Data
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Corrected Data Display */}
        {correctedData && (
          <div className="card">
            <div className="card-header">
              <span>📊</span>
              Corrected Customer Data
            </div>

            <div style={{ padding: '1rem' }}>
              <div style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#e8f5e8', borderRadius: '8px' }}>
                <h4>✅ Phase Corrections Applied</h4>
                <p>Customer data has been corrected with proper phase labels based on correlation analysis.</p>
                <p><strong>Total customers processed:</strong> {correctedData.total_customers}</p>
              </div>

              {Object.entries(correctedData.corrected_customers).map(([customerId, customerData]) => (
                <div key={customerId} style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                  <h5>Customer: {customerId}</h5>
                  <p><strong>Filename:</strong> {customerData.filename}</p>
                  
                  {customerData.phase_assignments && customerData.phase_assignments.length > 0 ? (
                    <div>
                      <h6>Phase Corrections:</h6>
                      <ul style={{ marginLeft: '1rem' }}>
                        {customerData.phase_assignments.map((assignment, idx) => (
                          <li key={idx}>
                            <strong>{assignment.customer_phase}</strong> → <strong>{assignment.assigned_feeder_phase}</strong>
                            <span style={{ color: '#666', marginLeft: '0.5rem' }}>
                              (Correlation: {assignment.correlation.toFixed(3)}, RMSE: {assignment.rmse.toFixed(1)}V)
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : (
                    <p style={{ color: '#999' }}>No phase corrections needed</p>
                  )}
                </div>
              ))}

              <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#e3f2fd', borderRadius: '8px' }}>
                <h5>📥 Export Options</h5>
                <p>Corrected data is available for download. The system has:</p>
                <ul style={{ marginLeft: '1rem' }}>
                  <li>Renamed customer phase columns to match feeder phases</li>
                  <li>Maintained all original data integrity</li>
                  <li>Applied corrections based on statistical correlation analysis</li>
                </ul>
                <button 
                  className="btn btn-secondary"
                  onClick={() => {
                    const dataStr = JSON.stringify(correctedData, null, 2);
                    const dataBlob = new Blob([dataStr], {type: 'application/json'});
                    const url = URL.createObjectURL(dataBlob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `corrected_customer_data_${sessionId}.json`;
                    link.click();
                    URL.revokeObjectURL(url);
                  }}
                  style={{ marginTop: '0.5rem' }}
                >
                  📥 Download Corrected Data (JSON)
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Visualization Controls */}
        {analysisData && (
          <div className="card">
            <div className="card-header">
              <span>📈</span>
              Visualization
            </div>

            <div className="grid grid-2" style={{ alignItems: 'end' }}>
              <div className="form-group">
                <label className="form-label">Customer</label>
                <select
                  className="form-select"
                  value={selectedCustomer}
                  onChange={(e) => setSelectedCustomer(e.target.value)}
                >
                  {availableCustomers.map((customer) => (
                    <option key={customer} value={customer}>
                      {customer}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Feeder</label>
                <select
                  className="form-select"
                  value={selectedFeeder}
                  onChange={(e) => setSelectedFeeder(e.target.value)}
                >
                  {availableFeeders.map((feeder) => (
                    <option key={feeder} value={feeder}>
                      {feeder}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              className="btn btn-primary"
              onClick={handleGenerateVisualization}
              disabled={!selectedCustomer || isGeneratingVisualization}
              style={{ width: '100%', marginTop: '1rem' }}
            >
              {isGeneratingVisualization ? (
                <div className="loading">
                  <div className="spinner"></div>
                  <span>Generating...</span>
                </div>
              ) : (
                <>
                  <span>📈</span>
                  Generate Visualization
                </>
              )}
            </button>
          </div>
        )}

        {/* Visualization Display */}
        {visualizationData && visualizationData.visualization_data && (
          <div className="card">
            <div className="card-header">
              <span>📊</span>
              Customer vs Feeder Voltage Correlation - {selectedCustomer}
            </div>
            
            {/* Visualization Info */}
            <div style={{ padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px', marginBottom: '1rem' }}>
              <div className="grid grid-3">
                <div>
                  <strong>Aligned Points:</strong> {visualizationData.visualization_data.aligned_points}
                </div>
                <div>
                  <strong>Customer ID:</strong> {visualizationData.visualization_data.customer_id}
                </div>
                <div>
                  <strong>Feeder ID:</strong> {visualizationData.visualization_data.feeder_id}
                </div>
              </div>
            </div>

            {/* Voltage Comparison Plot */}
            <div style={{ height: '500px' }}>
              <Plot
                data={[
                  {
                    x: visualizationData.visualization_data.customer_times,
                    y: visualizationData.visualization_data.customer_voltage,
                    mode: 'lines',
                    name: `Customer ${selectedCustomer}`,
                    type: 'scatter',
                    line: { color: '#ff7f0e', width: 2 }
                  },
                  {
                    x: visualizationData.visualization_data.feeder_times,
                    y: visualizationData.visualization_data.feeder_voltage,
                    mode: 'lines',
                    name: `Feeder ${selectedFeeder}`,
                    type: 'scatter',
                    line: { color: '#1f77b4', width: 2 }
                  }
                ]}
                layout={{
                  title: `Voltage Correlation: ${selectedCustomer} vs ${selectedFeeder}`,
                  xaxis: { title: 'Time' },
                  yaxis: { title: 'Voltage (V)' },
                  hovermode: 'closest',
                  showlegend: true,
                  autosize: true,
                  height: 500,
                }}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
              />
            </div>

            {/* Correlation Scatter Plot */}
            <div style={{ height: '400px', marginTop: '2rem' }}>
              <Plot
                data={[
                  {
                    x: visualizationData.visualization_data.customer_voltage,
                    y: visualizationData.visualization_data.feeder_voltage,
                    mode: 'markers',
                    name: 'Voltage Correlation',
                    type: 'scatter',
                    marker: { 
                      color: '#2ca02c', 
                      size: 6,
                      opacity: 0.7
                    }
                  }
                ]}
                layout={{
                  title: `Voltage Correlation Scatter Plot: ${selectedCustomer} vs ${selectedFeeder}`,
                  xaxis: { title: `Customer ${selectedCustomer} Voltage (V)` },
                  yaxis: { title: `Feeder ${selectedFeeder} Voltage (V)` },
                  hovermode: 'closest',
                  showlegend: false,
                  autosize: true,
                  height: 400,
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
            About Advanced NMD Analysis with Phase Identification
          </div>
          <div style={{ lineHeight: '1.6' }}>
            <p><strong>Advanced NMD Analysis</strong> provides sophisticated VOLTAGE-ONLY correlation analysis with automatic phase identification:</p>
            <ul style={{ marginLeft: '2rem', marginTop: '1rem' }}>
              <li><strong>Phase Identification:</strong> Automatically identifies correct feeder phase for each customer</li>
              <li><strong>Voltage-Only Correlation:</strong> Statistical correlation using only voltage data between customers and feeders</li>
              <li><strong>Single-Phase Correction:</strong> Assigns single-phase customers to correct feeder phase (A, B, or C)</li>
              <li><strong>Three-Phase Alignment:</strong> Properly aligns three-phase customer phases with feeder phases</li>
              <li><strong>Data Correction:</strong> Generates corrected CSV/JSON with proper phase labels</li>
              <li><strong>Pattern Recognition:</strong> Identify similar voltage patterns</li>
              <li><strong>Visualization:</strong> Interactive graphs showing correlations</li>
            </ul>
            
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f0f8ff', borderRadius: '8px' }}>
              <h5>🔄 Phase Identification Process:</h5>
              <ol style={{ marginLeft: '1rem' }}>
                <li><strong>Voltage Data Analysis:</strong> Compare customer voltage patterns with all feeder voltage phases</li>
                <li><strong>Voltage Correlation Calculation:</strong> Calculate Pearson correlation and RMSE using only voltage data for each phase combination</li>
                <li><strong>Best Match Selection:</strong> Assign customer to feeder phase with highest correlation and lowest RMSE</li>
                <li><strong>Phase Renaming:</strong> Rename customer phase columns to match assigned feeder phase</li>
                <li><strong>Data Export:</strong> Generate corrected data with proper phase labels</li>
              </ol>
            </div>
            
            <p style={{ marginTop: '1rem' }}>
              <strong>Correlation Strength Guide:</strong>
            </p>
            <ul style={{ marginLeft: '2rem' }}>
              <li><span style={{ color: '#28a745' }}>● Strong (0.7-1.0):</span> Very high correlation - likely correct phase assignment</li>
              <li><span style={{ color: '#ffc107' }}>● Moderate (0.5-0.7):</span> Good correlation - probable phase assignment</li>
              <li><span style={{ color: '#6c757d' }}>● Weak (0.3-0.5):</span> Low correlation - uncertain phase assignment</li>
              <li><span style={{ color: '#6c757d' }}>● Very Weak (0.0-0.3):</span> Minimal correlation - likely incorrect phase</li>
            </ul>
            
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#fff3cd', borderRadius: '8px' }}>
              <h5>⚠️ Important Notes:</h5>
              <ul style={{ marginLeft: '1rem' }}>
                <li>Single-phase customers labeled as "Phase A" may actually be connected to Phase B or C</li>
                <li>Three-phase customers may have phases misaligned with feeder phases</li>
                <li>Correlation analysis helps identify the correct phase connections</li>
                <li>Always verify results with field measurements when possible</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NMDAnalysisNew;