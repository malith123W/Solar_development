import React, { useState, useRef } from 'react';
import Plot from 'react-plotly.js';
import { 
  pqUploadFeederNmd, 
  pqUploadConsumer, 
  pqGenerateReport, 
  pqDownloadReport, 
  pqDownloadPdf,
  pqNetworkGraph,
  transformerLoadUpload
} from '../services/api';
import FeederWiseUpload from './FeederWiseUpload';
import NetworkGraph from './NetworkGraph';
import VoltageVariation from './VoltageVariation';

const PowerQuality = () => {
  const [sessionId] = useState(`pq_session_${Date.now()}`);
  const [feederFile, setFeederFile] = useState(null);
  const [consumerFiles, setConsumerFiles] = useState([]);
  const [feederWiseConsumerFiles, setFeederWiseConsumerFiles] = useState({});
  const [isUploadingFeeder, setIsUploadingFeeder] = useState(false);
  const [isUploadingConsumer, setIsUploadingConsumer] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [availableFeeders, setAvailableFeeders] = useState([]);
  const [reportData, setReportData] = useState(null);
  const [transformerNumber, setTransformerNumber] = useState('T-001');
  const [transformerCapacity, setTransformerCapacity] = useState('');
  
  // Network Graph states
  const [networkGraphData, setNetworkGraphData] = useState(null);
  const [isGeneratingNetworkGraph, setIsGeneratingNetworkGraph] = useState(false);
  
  // Transformer Load Analysis states
  const [transformerLoadFile, setTransformerLoadFile] = useState(null);
  const [transformerLoadData, setTransformerLoadData] = useState(null);
  const [isUploadingLoad, setIsUploadingLoad] = useState(false);
  
  const feederInputRef = useRef(null);
  const consumerInputRef = useRef(null);
  const transformerLoadInputRef = useRef(null);

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
      const response = await pqUploadFeederNmd(file, sessionId);
      setFeederFile(file);
      setSuccess(`Feeder NMD file "${file.name}" uploaded successfully!`);
      
      if (response.data && response.data.feeders) {
        setAvailableFeeders(response.data.feeders);
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to upload feeder file');
    } finally {
      setIsUploadingFeeder(false);
    }
  };

  const handleConsumerUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    const invalidFiles = files.filter(file => !file.name.endsWith('.csv'));
    if (invalidFiles.length > 0) {
      setError('Please upload only CSV files');
      return;
    }

    setIsUploadingConsumer(true);
    setError(null);
    setSuccess(null);

    try {
      const uploadPromises = files.map((file, index) => 
        pqUploadConsumer(
          file, 
          sessionId, 
          file.name.replace('.csv', ''), 
'FEEDER_001'
        )
      );

      await Promise.all(uploadPromises);
      setConsumerFiles(prev => [...prev, ...files]);
      setSuccess(`${files.length} consumer file(s) uploaded successfully!`);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to upload consumer files');
    } finally {
      setIsUploadingConsumer(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!feederFile) {
      setError('Please upload feeder NMD file');
      return;
    }

    if (!transformerLoadFile) {
      setError('Please upload transformer load data file');
      return;
    }

    const capacity = parseFloat(transformerCapacity);
    if (!capacity || capacity <= 0) {
      setError('Please enter a valid transformer rated capacity (kVA)');
      return;
    }

    setIsGeneratingReport(true);
    setError(null);

    try {
      const response = await pqGenerateReport({
        session_id: sessionId,
        feeders_to_use: availableFeeders,
        transformer_capacity: capacity
      });

      setReportData(response.data.report);
      setSuccess('Comprehensive power quality report generated successfully!');
      
      // Automatically generate network graph after report generation
      if (response.data.report && response.data.report.network_graph) {
        setNetworkGraphData(response.data.report.network_graph);
      } else {
        // Generate network graph separately if not included in report
        generateNetworkGraph();
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to generate report');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const generateNetworkGraph = async () => {
    if (!feederFile) {
      setError('Please upload feeder NMD file first');
      return;
    }

    setIsGeneratingNetworkGraph(true);
    setError(null);

    try {
      const response = await pqNetworkGraph({
        session_id: sessionId,
        transformer_name: transformerNumber
      });

      if (response.data.success) {
        setNetworkGraphData(response.data.graph_data);
        setSuccess('Network topology graph generated successfully!');
      } else {
        setError(response.data.error || 'Failed to generate network graph');
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to generate network graph');
    } finally {
      setIsGeneratingNetworkGraph(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!reportData) {
      setError('Please generate a report first');
      return;
    }

    setIsDownloading(true);
    setError(null);

    try {
      const response = await pqDownloadReport({
        session_id: sessionId,
        filename: `power_quality_report_${sessionId}.json`,
      });

      // Create download link
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { 
        type: 'application/json' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `power_quality_report_${sessionId}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setSuccess('Report downloaded successfully!');
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to download report');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!reportData) {
      setError('Please generate a report first');
      return;
    }

    setIsDownloading(true);
    setError(null);

    try {
      const response = await pqDownloadPdf({
        session_id: sessionId,
        transformer_number: transformerNumber,
      });

      // Create download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `power_quality_report_${transformerNumber}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setSuccess('PDF report downloaded successfully!');
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to download PDF');
    } finally {
      setIsDownloading(false);
    }
  };

  const removeConsumerFile = (index) => {
    setConsumerFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleFeederWiseConsumerUpload = (feederName, files) => {
    setFeederWiseConsumerFiles(prev => ({
      ...prev,
      [feederName]: [...(prev[feederName] || []), ...files]
    }));
  };


  // Transformer Load Analysis Handlers
  const handleTransformerLoadUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }

    setIsUploadingLoad(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await transformerLoadUpload(file, sessionId);
      setTransformerLoadFile(file);
      setTransformerLoadData(response.data);
      setSuccess(`Transformer load file "${file.name}" uploaded successfully! ${response.data.row_count} records loaded.`);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to upload transformer load file');
    } finally {
      setIsUploadingLoad(false);
    }
  };


  return (
    <div className="container">
      <div className="paper">
        {/* Header */}
        <div className="header">
          <h1>Power Quality Analysis</h1>
          <p>Analyze power quality metrics and generate comprehensive reports</p>
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

        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          {/* Step 1: Feeder Upload */}
          <div className="card">
            <div className="card-header">
              <span>1️⃣</span>
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
                  <div className="upload-text">Upload Feeder NMD</div>
                  <div className="upload-subtext">Feeder network metering data</div>
                </>
              )}
            </div>

            {feederFile && (
              <div style={{ marginTop: '1rem' }}>
                <div className="file-name">✓ {feederFile.name}</div>
              </div>
            )}
          </div>


          {/* Step 2: Transformer Load Upload */}
          <div className="card">
            <div className="card-header">
              <span>2️⃣</span>
              <span>⚡</span>
              Transformer Load Data
            </div>
            
            <div
              className="upload-area"
              onClick={() => transformerLoadInputRef.current?.click()}
            >
              <input
                ref={transformerLoadInputRef}
                type="file"
                accept=".csv"
                onChange={handleTransformerLoadUpload}
                style={{ display: 'none' }}
              />
              
              {isUploadingLoad ? (
                <div className="loading">
                  <div className="spinner"></div>
                  <span>Uploading...</span>
                </div>
              ) : (
                <>
                  <div className="upload-icon">📁</div>
                  <div className="upload-text">Upload Load Data</div>
                  <div className="upload-subtext">Transformer KVA/KW data</div>
                </>
              )}
            </div>

            {transformerLoadFile && (
              <div style={{ marginTop: '1rem' }}>
                <div className="file-name">✓ {transformerLoadFile.name}</div>
                <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.5rem' }}>
                  {transformerLoadData?.row_count} records |
                  KVA: {transformerLoadData?.has_kva ? '✓' : '✗'} |
                  KW: {transformerLoadData?.has_kw ? '✓' : '✗'}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Step 2: Consumer Upload - Feeder Wise */}
        <div className="card" style={{ marginTop: '1rem' }}>
          <div className="card-header">
            <span>2️⃣</span>
            <span>📤</span>
            Upload Consumer Data by Feeder (Optional)
          </div>
          
          <FeederWiseUpload 
            sessionId={sessionId}
            availableFeeders={availableFeeders}
            onConsumerUpload={handleFeederWiseConsumerUpload}
          />
        </div>


        {/* Report Generation */}
        <div className="card">
          <div className="card-header">
            <span>3️⃣</span>
            <span>📊</span>
            Generate Comprehensive Report
          </div>

          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', alignItems: 'end' }}>
            <div className="form-group">
              <label className="form-label">Transformer Number</label>
              <input
                type="text"
                className="form-control"
                value={transformerNumber}
                onChange={(e) => setTransformerNumber(e.target.value)}
                placeholder="T-001"
              />
            </div>
            
            <div className="form-group">
              <label className="form-label">
                Transformer Capacity (kVA) <span style={{ color: '#f44336' }}>*</span>
              </label>
              <input
                type="number"
                className="form-control"
                value={transformerCapacity}
                onChange={(e) => setTransformerCapacity(e.target.value)}
                placeholder="Enter capacity in kVA (e.g., 500)"
                min="0"
                step="any"
                required
              />
            </div>
            
            <div>
              <button
                className="btn btn-primary"
                onClick={handleGenerateReport}
                disabled={!feederFile || !transformerLoadFile || !transformerCapacity || isGeneratingReport}
                style={{ width: '100%' }}
              >
                {isGeneratingReport ? (
                  <div className="loading">
                    <div className="spinner"></div>
                    <span>Generating...</span>
                  </div>
                ) : (
                  <>
                    <span>📊</span>
                    Generate Report
                  </>
                )}
              </button>
            </div>
          </div>

          {reportData && (
            <div style={{ marginTop: '2rem' }}>
              <div className="card-header">
                <span>✅</span>
                Report Generated Successfully!
              </div>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button
                  className="btn btn-outline"
                  onClick={handleDownloadReport}
                  disabled={isDownloading}
                >
                  {isDownloading ? (
                    <div className="loading">
                      <div className="spinner"></div>
                      <span>Downloading...</span>
                    </div>
                  ) : (
                    <>
                      <span>📄</span>
                      Download JSON
                    </>
                  )}
                </button>
                <button
                  className="btn btn-outline"
                  onClick={handleDownloadPdf}
                  disabled={isDownloading}
                >
                  {isDownloading ? (
                    <div className="loading">
                      <div className="spinner"></div>
                      <span>Downloading...</span>
                    </div>
                  ) : (
                    <>
                      <span>📋</span>
                      Download PDF
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Voltage Quality Report Display */}
          {reportData && (
            <div style={{ marginTop: '2rem' }}>
              <div className="card">
                <div className="card-header">
                  <span>📊</span>
                  {reportData.title || 'Voltage Quality Report'}
                </div>
                
                {/* Overall Summary */}
                {reportData.summary && reportData.summary.overall_analysis && (
                  <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ marginBottom: '1rem', color: '#333' }}>Overall Summary</h3>
                    
                    {/* Voltage Quality Distribution Chart */}
                    <div style={{ marginBottom: '2rem', backgroundColor: 'white', padding: '1rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                      <Plot
                        data={[
                          {
                            values: [
                              reportData.summary.overall_analysis.standard.within,
                              reportData.summary.overall_analysis.standard.over,
                              reportData.summary.overall_analysis.standard.under,
                              reportData.summary.overall_analysis.standard.interruptions
                            ],
                            labels: ['Within Range', 'Over Voltage', 'Under Voltage', 'Interruptions'],
                            type: 'pie',
                            marker: {
                              colors: ['#4caf50', '#ff9800', '#f44336', '#9e9e9e']
                            },
                            textinfo: 'label+percent',
                            textposition: 'outside',
                            automargin: true
                          }
                        ]}
                        layout={{
                          title: {
                            text: 'Voltage Quality Distribution (Standard Limits: 207-253V)',
                            font: { size: 16, color: '#333' }
                          },
                          paper_bgcolor: 'white',
                          autosize: true,
                          height: 400,
                          margin: { l: 40, r: 40, t: 60, b: 40 },
                          showlegend: true,
                          legend: {
                            orientation: 'h',
                            yanchor: 'bottom',
                            y: -0.2,
                            xanchor: 'center',
                            x: 0.5
                          }
                        }}
                        useResizeHandler={true}
                        style={{ width: '100%' }}
                        config={{ displayModeBar: true, responsive: true }}
                      />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                      {/* Standard Limits */}
                      <div className="card" style={{ padding: '1rem', backgroundColor: '#f8f9fa' }}>
                        <h4 style={{ marginBottom: '0.5rem', color: '#495057' }}>Standard Limits (207-253V, Nominal 230 V)</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.9rem' }}>
                          <div>Within Standard: <strong>{reportData.summary.overall_analysis.standard.within}%</strong></div>
                          <div>Over Voltage: <strong>{reportData.summary.overall_analysis.standard.over}%</strong></div>
                          <div>Under Voltage: <strong>{reportData.summary.overall_analysis.standard.under}%</strong></div>
                          <div>Interruptions: <strong>{reportData.summary.overall_analysis.standard.interruptions}%</strong></div>
                        </div>
                        <div style={{ marginTop: '0.5rem', padding: '0.25rem 0.5rem', borderRadius: '4px', backgroundColor: '#d4edda', color: '#155724', fontSize: '0.8rem' }}>
                          Status: <strong>Maintained</strong>
                        </div>
                      </div>
                      
                      {/* Strict Limits */}
                      <div className="card" style={{ padding: '1rem', backgroundColor: '#f8f9fa' }}>
                        <h4 style={{ marginBottom: '0.5rem', color: '#495057' }}>Strict Limits (216-244V)</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.9rem' }}>
                          <div>Within Strict: <strong>{reportData.summary.overall_analysis.strict.within}%</strong></div>
                          <div style={{ color: reportData.summary.overall_analysis.strict.over > 5 ? '#fd7e14' : 'inherit' }}>
                            Over Strict: <strong>{reportData.summary.overall_analysis.strict.over}%</strong>
                          </div>
                          <div style={{ color: reportData.summary.overall_analysis.strict.under > 5 ? '#fd7e14' : 'inherit' }}>
                            Under Strict: <strong>{reportData.summary.overall_analysis.strict.under}%</strong>
                          </div>
                        </div>
                        <div style={{ marginTop: '0.5rem', padding: '0.25rem 0.5rem', borderRadius: '4px', backgroundColor: '#f8d7da', color: '#721c24', fontSize: '0.8rem' }}>
                          Strict Status: <strong>Not Maintained</strong>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Network Topology Graph */}
                {networkGraphData && (
                  <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ marginBottom: '1rem', color: '#333', fontWeight: 'bold' }}>🌳 Network Topology</h3>
                    <div style={{ 
                      backgroundColor: 'white', 
                      borderRadius: '8px', 
                      padding: '1rem', 
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                      border: '1px solid #e9ecef'
                    }}>
                      <NetworkGraph 
                        graphData={networkGraphData} 
                        width={1200} 
                        height={600} 
                      />
                    </div>
                  </div>
                )}

                {/* Manual Network Graph Generation */}
                {!networkGraphData && feederFile && (
                  <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ marginBottom: '1rem', color: '#333', fontWeight: 'bold' }}>🌳 Network Topology</h3>
                    <div style={{ 
                      backgroundColor: 'white', 
                      borderRadius: '8px', 
                      padding: '1rem', 
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                      border: '1px solid #e9ecef',
                      textAlign: 'center'
                    }}>
                      <button
                        onClick={generateNetworkGraph}
                        disabled={isGeneratingNetworkGraph}
                        style={{
                          padding: '0.75rem 1.5rem',
                          backgroundColor: isGeneratingNetworkGraph ? '#6c757d' : '#007bff',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          fontSize: '0.9rem',
                          fontWeight: '500',
                          cursor: isGeneratingNetworkGraph ? 'not-allowed' : 'pointer',
                          transition: 'background-color 0.2s ease'
                        }}
                      >
                        {isGeneratingNetworkGraph ? '⏳ Generating...' : '🔄 Generate Network Graph'}
                      </button>
                      <p style={{ marginTop: '1rem', color: '#666', fontSize: '0.9rem' }}>
                        📊 Click to visualize the transformer → feeder → phase hierarchy
                      </p>
                    </div>
                  </div>
                )}

                {/* Voltage Variation Analysis */}
                {reportData.voltage_variation && (
                  <VoltageVariation 
                    voltageData={reportData.voltage_variation}
                    width={1200}
                    height={800}
                  />
                )}

                {/* Feeder-wise Analysis */}
                {reportData.feeders && Object.keys(reportData.feeders).length > 0 && (
                  <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ marginBottom: '1rem', color: '#333', fontWeight: 'bold' }}>Feeder-wise Analysis</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(600px, 1fr))', gap: '1rem' }}>
                      {Object.entries(reportData.feeders).map(([feederName, feederData]) => (
                        <div key={feederName} style={{ 
                          backgroundColor: 'white', 
                          borderRadius: '8px', 
                          padding: '1rem', 
                          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                          border: '1px solid #e9ecef'
                        }}>
                          <div style={{ marginBottom: '0.75rem', color: '#333', fontSize: '0.9rem' }}>
                            Feeder {feederName}
                          </div>
                          {feederData.voltage_quality && (
                            <>
                              <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                                <strong style={{ color: '#333' }}>Standard (207-253V):</strong> 
                                <span style={{ color: '#666' }}> Within: {feederData.voltage_quality.standard.within}% | Over: {feederData.voltage_quality.standard.over}% | Under: {feederData.voltage_quality.standard.under}%</span>
                              </div>
                              <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                                <strong style={{ color: '#333' }}>Strict (216-244V):</strong> 
                                <span style={{ color: '#666' }}> Within: {feederData.voltage_quality.strict.within}% | Over: {feederData.voltage_quality.strict.over}% | Under: {feederData.voltage_quality.strict.under}%</span>
                              </div>
                              <div style={{ fontSize: '0.8rem', color: '#888' }}>
                                Interruptions: {feederData.voltage_quality.standard.interruptions}% | 
                                Avg Current: {feederData.avg_current} A | 
                                Avg PF: {feederData.avg_pf}
                              </div>
                            </>
                          )}
                          
                          {/* Voltage Graphs for this feeder */}
                          {feederData.voltage_columns && Object.keys(feederData.voltage_columns).length > 0 && (
                            <div style={{ marginTop: '1rem' }}>
                              <h5 style={{ color: '#333', marginBottom: '0.5rem', fontSize: '0.9rem' }}>⚡ Voltage Profile</h5>
                              <div style={{ height: '300px' }}>
                                <Plot
                                  data={Object.entries(feederData.voltage_columns).map(([voltageCol, voltageData], index) => {
                                    const colors = ['#9c27b0', '#2196f3', '#4caf50', '#ff9800', '#f44336'];
                                    const phaseLabel = voltageCol.replace(/[^A-C]/g, '') || `Phase ${index + 1}`;
                                    return {
                                      x: Array.from({ length: voltageData.raw_data.length }, (_, i) => i),
                                      y: voltageData.raw_data,
                                      type: 'scatter',
                                      mode: 'lines',
                                      name: `${phaseLabel} (${voltageCol})`,
                                      line: { color: colors[index % colors.length], width: 2 },
                                      hovertemplate: `<b>${phaseLabel}</b><br>Time: %{x}<br>Voltage: %{y:.1f}V<extra></extra>`
                                    };
                                  }).concat([
                                    // Add voltage limit lines
                                    {
                                      x: [0, 1000], // Dummy x values
                                      y: [253, 253],
                                      type: 'scatter',
                                      mode: 'lines',
                                      name: 'Over Voltage Limit (253V)',
                                      line: { color: 'red', width: 2, dash: 'dash' },
                                      showlegend: true
                                    },
                                    {
                                      x: [0, 1000],
                                      y: [207, 207],
                                      type: 'scatter',
                                      mode: 'lines',
                                      name: 'Under Voltage Limit (207V)',
                                      line: { color: 'orange', width: 2, dash: 'dash' },
                                      showlegend: true
                                    },
                                    {
                                      x: [0, 1000],
                                      y: [230, 230],
                                      type: 'scatter',
                                      mode: 'lines',
                                      name: 'Nominal Voltage (230V)',
                                      line: { color: 'gray', width: 1, dash: 'dot' },
                                      showlegend: true
                                    }
                                  ])}
                                  layout={{
                                    title: `Voltage Profile - ${feederName}`,
                                    xaxis: { 
                                      title: 'Time Index',
                                      showgrid: true,
                                      gridcolor: '#f0f0f0'
                                    },
                                    yaxis: { 
                                      title: 'Voltage (V)',
                                      showgrid: true,
                                      gridcolor: '#f0f0f0',
                                      range: [180, 280]
                                    },
                                    hovermode: 'closest',
                                    showlegend: true,
                                    legend: {
                                      orientation: 'h',
                                      y: -0.2,
                                      x: 0.5,
                                      xanchor: 'center'
                                    },
                                    margin: { t: 40, b: 60, l: 50, r: 20 },
                                    height: 300,
                                    font: { size: 10 }
                                  }}
                                  style={{ width: '100%', height: '100%' }}
                                  useResizeHandler={true}
                                  config={{
                                    displayModeBar: false,
                                    responsive: true
                                  }}
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Consumer-wise Analysis */}
                {reportData.consumers && Object.keys(reportData.consumers).length > 0 && (
                  <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ marginBottom: '1rem', color: '#333', fontWeight: 'bold' }}>Consumer-wise Analysis</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '1rem' }}>
                      {Object.entries(reportData.consumers).map(([consumerId, consumerData]) => (
                        <div key={consumerId} style={{ 
                          backgroundColor: 'white', 
                          borderRadius: '8px', 
                          padding: '1rem', 
                          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                          border: '1px solid #e9ecef'
                        }}>
                          <div style={{ marginBottom: '0.75rem', color: '#333', fontSize: '0.9rem' }}>
                            Consumer {consumerId}
                          </div>
                          {consumerData.voltage_quality && (
                            <>
                              <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                                <strong style={{ color: '#333' }}>Standard (207-253V):</strong> 
                                <span style={{ color: '#666' }}> Within: {consumerData.voltage_quality.standard.within}% | Over: {consumerData.voltage_quality.standard.over}% | Under: {consumerData.voltage_quality.standard.under}%</span>
                              </div>
                              <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                                <strong style={{ color: '#333' }}>Strict (216-244V):</strong> 
                                <span style={{ color: '#666' }}> Within: {consumerData.voltage_quality.strict.within}% | Over: {consumerData.voltage_quality.strict.over}% | Under: {consumerData.voltage_quality.strict.under}%</span>
                              </div>
                              <div style={{ fontSize: '0.8rem', color: '#888' }}>
                                Interruptions: {consumerData.voltage_quality.standard.interruptions}% | 
                                Avg Current: {consumerData.avg_current} A | 
                                Avg PF: {consumerData.avg_pf}
                              </div>
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Transformer Load Analysis */}
                {reportData.transformer_load_analysis && (
                  <div style={{ marginBottom: '2rem', paddingTop: '2rem', borderTop: '2px solid #e9ecef' }}>
                    <h3 style={{ marginBottom: '1rem', color: '#333', fontWeight: 'bold' }}>⚡ Transformer Load Analysis</h3>
                    
                    <div style={{ 
                      display: 'grid', 
                      gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
                      gap: '1rem',
                      marginBottom: '1.5rem'
                    }}>
                      <div style={{ padding: '1rem', backgroundColor: '#e3f2fd', borderRadius: '8px', border: '1px solid #2196f3' }}>
                        <div style={{ fontSize: '0.85rem', color: '#555', marginBottom: '0.5rem' }}>Rated Capacity</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1976d2' }}>
                          {reportData.transformer_load_analysis.rated_capacity_kva} kVA
                        </div>
                      </div>
                      
                      <div style={{ padding: '1rem', backgroundColor: '#f3e5f5', borderRadius: '8px', border: '1px solid #9c27b0' }}>
                        <div style={{ fontSize: '0.85rem', color: '#555', marginBottom: '0.5rem' }}>Analysis Period</div>
                        <div style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#7b1fa2' }}>
                          {reportData.transformer_load_analysis.time_range.total_records} records
                        </div>
                      </div>
                    </div>

                    {/* Load Profile Graphs */}
                    {reportData.transformer_load_analysis.visualization_data && (
                      <div style={{ marginBottom: '2rem' }}>
                        <h4 style={{ color: '#333', marginBottom: '1rem' }}>📈 Load Profile Over Time</h4>
                        
                        {/* KVA Load Profile */}
                        {reportData.transformer_load_analysis.visualization_data.kva && (
                          <div style={{ marginBottom: '2rem', backgroundColor: 'white', padding: '1rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                            <Plot
                              data={[
                                {
                                  x: reportData.transformer_load_analysis.visualization_data.kva.time,
                                  y: reportData.transformer_load_analysis.visualization_data.kva.kva,
                                  type: 'scatter',
                                  mode: 'lines',
                                  name: 'KVA Load',
                                  line: { color: '#2196f3', width: 2 },
                                  fill: 'tozeroy',
                                  fillcolor: 'rgba(33, 150, 243, 0.1)'
                                },
                                {
                                  x: reportData.transformer_load_analysis.visualization_data.kva.time,
                                  y: reportData.transformer_load_analysis.visualization_data.kva.capacity_line,
                                  type: 'scatter',
                                  mode: 'lines',
                                  name: 'Rated Capacity',
                                  line: { color: '#f44336', width: 2, dash: 'dash' }
                                }
                              ]}
                              layout={{
                                title: {
                                  text: 'Transformer Load (KVA) Over Time',
                                  font: { size: 16, color: '#333' }
                                },
                                xaxis: { 
                                  title: 'Date & Time',
                                  gridcolor: '#e0e0e0'
                                },
                                yaxis: { 
                                  title: 'Load (kVA)',
                                  gridcolor: '#e0e0e0'
                                },
                                hovermode: 'x unified',
                                plot_bgcolor: '#fafafa',
                                paper_bgcolor: 'white',
                                autosize: true,
                                height: 400,
                                margin: { l: 60, r: 40, t: 60, b: 60 }
                              }}
                              useResizeHandler={true}
                              style={{ width: '100%' }}
                              config={{ displayModeBar: true, responsive: true }}
                            />
                          </div>
                        )}

                        {/* KW Load Profile */}
                        {reportData.transformer_load_analysis.visualization_data.kw && (
                          <div style={{ marginBottom: '2rem', backgroundColor: 'white', padding: '1rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                            <Plot
                              data={[
                                {
                                  x: reportData.transformer_load_analysis.visualization_data.kw.time,
                                  y: reportData.transformer_load_analysis.visualization_data.kw.kw,
                                  type: 'scatter',
                                  mode: 'lines',
                                  name: 'KW Load',
                                  line: { color: '#4caf50', width: 2 },
                                  fill: 'tozeroy',
                                  fillcolor: 'rgba(76, 175, 80, 0.1)'
                                },
                                {
                                  x: reportData.transformer_load_analysis.visualization_data.kw.time,
                                  y: reportData.transformer_load_analysis.visualization_data.kw.capacity_line,
                                  type: 'scatter',
                                  mode: 'lines',
                                  name: 'Rated Capacity',
                                  line: { color: '#f44336', width: 2, dash: 'dash' }
                                }
                              ]}
                              layout={{
                                title: {
                                  text: 'Transformer Load (KW) Over Time',
                                  font: { size: 16, color: '#333' }
                                },
                                xaxis: { 
                                  title: 'Date & Time',
                                  gridcolor: '#e0e0e0'
                                },
                                yaxis: { 
                                  title: 'Load (kW)',
                                  gridcolor: '#e0e0e0'
                                },
                                hovermode: 'x unified',
                                plot_bgcolor: '#fafafa',
                                paper_bgcolor: 'white',
                                autosize: true,
                                height: 400,
                                margin: { l: 60, r: 40, t: 60, b: 60 }
                              }}
                              useResizeHandler={true}
                              style={{ width: '100%' }}
                              config={{ displayModeBar: true, responsive: true }}
                            />
                          </div>
                        )}

                        {/* Load Percentage Timeline */}
                        {reportData.transformer_load_analysis.visualization_data.kva && (
                          <div style={{ marginBottom: '2rem', backgroundColor: 'white', padding: '1rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                            <Plot
                              data={[
                                {
                                  x: reportData.transformer_load_analysis.visualization_data.kva.time,
                                  y: reportData.transformer_load_analysis.visualization_data.kva.load_pct,
                                  type: 'scatter',
                                  mode: 'lines',
                                  name: 'Load %',
                                  line: { 
                                    color: reportData.transformer_load_analysis.visualization_data.kva.load_pct,
                                    width: 2
                                  },
                                  marker: {
                                    color: reportData.transformer_load_analysis.visualization_data.kva.load_pct.map(pct => 
                                      pct > 100 ? '#f44336' : pct > 90 ? '#ff9800' : '#4caf50'
                                    ),
                                    size: 4
                                  }
                                },
                                {
                                  x: reportData.transformer_load_analysis.visualization_data.kva.time,
                                  y: Array(reportData.transformer_load_analysis.visualization_data.kva.time.length).fill(100),
                                  type: 'scatter',
                                  mode: 'lines',
                                  name: '100% Capacity',
                                  line: { color: '#f44336', width: 2, dash: 'dash' }
                                }
                              ]}
                              layout={{
                                title: {
                                  text: 'Load Percentage Timeline',
                                  font: { size: 16, color: '#333' }
                                },
                                xaxis: { 
                                  title: 'Date & Time',
                                  gridcolor: '#e0e0e0'
                                },
                                yaxis: { 
                                  title: 'Load (%)',
                                  gridcolor: '#e0e0e0'
                                },
                                hovermode: 'x unified',
                                plot_bgcolor: '#fafafa',
                                paper_bgcolor: 'white',
                                autosize: true,
                                height: 400,
                                margin: { l: 60, r: 40, t: 60, b: 60 },
                                shapes: [{
                                  type: 'rect',
                                  xref: 'paper',
                                  yref: 'y',
                                  x0: 0,
                                  x1: 1,
                                  y0: 100,
                                  y1: Math.max(...reportData.transformer_load_analysis.visualization_data.kva.load_pct),
                                  fillcolor: '#ffebee',
                                  opacity: 0.3,
                                  line: { width: 0 }
                                }]
                              }}
                              useResizeHandler={true}
                              style={{ width: '100%' }}
                              config={{ displayModeBar: true, responsive: true }}
                            />
                          </div>
                        )}

                        {/* Hourly Load Pattern */}
                        {reportData.transformer_load_analysis.visualization_data.kva && 
                         reportData.transformer_load_analysis.visualization_data.kva.hourly_avg && (
                          <div style={{ marginBottom: '2rem', backgroundColor: 'white', padding: '1rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                            <Plot
                              data={[
                                {
                                  x: Object.keys(reportData.transformer_load_analysis.visualization_data.kva.hourly_avg).map(h => `${h}:00`),
                                  y: Object.values(reportData.transformer_load_analysis.visualization_data.kva.hourly_avg),
                                  type: 'bar',
                                  name: 'Avg Load',
                                  marker: {
                                    color: Object.values(reportData.transformer_load_analysis.visualization_data.kva.hourly_avg).map(
                                      v => (v / reportData.transformer_load_analysis.rated_capacity_kva * 100) > 100 ? '#f44336' : 
                                           (v / reportData.transformer_load_analysis.rated_capacity_kva * 100) > 90 ? '#ff9800' : '#2196f3'
                                    ),
                                    line: { color: '#1976d2', width: 1 }
                                  }
                                },
                                {
                                  x: Object.keys(reportData.transformer_load_analysis.visualization_data.kva.hourly_avg).map(h => `${h}:00`),
                                  y: Array(Object.keys(reportData.transformer_load_analysis.visualization_data.kva.hourly_avg).length).fill(
                                    reportData.transformer_load_analysis.rated_capacity_kva
                                  ),
                                  type: 'scatter',
                                  mode: 'lines',
                                  name: 'Capacity',
                                  line: { color: '#f44336', width: 2, dash: 'dash' }
                                }
                              ]}
                              layout={{
                                title: {
                                  text: 'Average Hourly Load Pattern',
                                  font: { size: 16, color: '#333' }
                                },
                                xaxis: { 
                                  title: 'Hour of Day',
                                  gridcolor: '#e0e0e0'
                                },
                                yaxis: { 
                                  title: 'Average Load (kVA)',
                                  gridcolor: '#e0e0e0'
                                },
                                hovermode: 'x unified',
                                plot_bgcolor: '#fafafa',
                                paper_bgcolor: 'white',
                                autosize: true,
                                height: 400,
                                margin: { l: 60, r: 40, t: 60, b: 60 }
                              }}
                              useResizeHandler={true}
                              style={{ width: '100%' }}
                              config={{ displayModeBar: true, responsive: true }}
                            />
                          </div>
                        )}

                        {/* Load Duration Curve */}
                        {reportData.transformer_load_analysis.visualization_data.kva && 
                         reportData.transformer_load_analysis.visualization_data.kva.load_duration_curve && (
                          <div style={{ marginBottom: '2rem', backgroundColor: 'white', padding: '1rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                            <Plot
                              data={[
                                {
                                  x: reportData.transformer_load_analysis.visualization_data.kva.load_duration_curve.duration_pct,
                                  y: reportData.transformer_load_analysis.visualization_data.kva.load_duration_curve.load,
                                  type: 'scatter',
                                  mode: 'lines',
                                  name: 'Load Duration',
                                  fill: 'tozeroy',
                                  fillcolor: 'rgba(33, 150, 243, 0.2)',
                                  line: { color: '#2196f3', width: 3 }
                                },
                                {
                                  x: [0, 100],
                                  y: [reportData.transformer_load_analysis.rated_capacity_kva, reportData.transformer_load_analysis.rated_capacity_kva],
                                  type: 'scatter',
                                  mode: 'lines',
                                  name: 'Rated Capacity',
                                  line: { color: '#f44336', width: 2, dash: 'dash' }
                                }
                              ]}
                              layout={{
                                title: {
                                  text: 'Load Duration Curve',
                                  font: { size: 16, color: '#333' }
                                },
                                xaxis: { 
                                  title: 'Duration (% of time)',
                                  gridcolor: '#e0e0e0',
                                  range: [0, 100]
                                },
                                yaxis: { 
                                  title: 'Load (kVA)',
                                  gridcolor: '#e0e0e0'
                                },
                                hovermode: 'x unified',
                                plot_bgcolor: '#fafafa',
                                paper_bgcolor: 'white',
                                autosize: true,
                                height: 400,
                                margin: { l: 60, r: 40, t: 60, b: 60 },
                                annotations: [{
                                  text: 'Shows load sorted from highest to lowest<br>Horizontal line = Rated Capacity',
                                  xref: 'paper',
                                  yref: 'paper',
                                  x: 0.5,
                                  y: 1.1,
                                  xanchor: 'center',
                                  yanchor: 'bottom',
                                  showarrow: false,
                                  font: { size: 11, color: '#666' }
                                }]
                              }}
                              useResizeHandler={true}
                              style={{ width: '100%' }}
                              config={{ displayModeBar: true, responsive: true }}
                            />
                          </div>
                        )}

                        {/* Voltage Analysis Graphs */}
                        {reportData.transformer_load_analysis.visualization_data.voltage && (
                          <div style={{ marginBottom: '2rem' }}>
                            <h4 style={{ color: '#333', marginBottom: '1rem' }}>⚡ Voltage Profile Analysis</h4>
                            
                            {/* Voltage Over Time */}
                            <div style={{ marginBottom: '2rem', backgroundColor: 'white', padding: '1rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                              <Plot
                                data={[
                                  // Add all voltage phase traces
                                  ...Object.keys(reportData.transformer_load_analysis.visualization_data.voltage)
                                    .filter(key => key.startsWith('voltage_') && key !== 'voltage_label' && key !== 'voltage')
                                    .map((key, index) => {
                                      const colors = ['#9c27b0', '#2196f3', '#4caf50'];
                                      const phaseLabel = key.replace('voltage_', '');
                                      return {
                                        x: reportData.transformer_load_analysis.visualization_data.voltage.time,
                                        y: reportData.transformer_load_analysis.visualization_data.voltage[key],
                                        type: 'scatter',
                                        mode: 'lines',
                                        name: phaseLabel,
                                        line: { color: colors[index % 3], width: 2 }
                                      };
                                    }),
                                  {
                                    x: reportData.transformer_load_analysis.visualization_data.voltage.time,
                                    y: reportData.transformer_load_analysis.visualization_data.voltage.over_limit,
                                    type: 'scatter',
                                    mode: 'lines',
                                    name: 'Over Voltage Limit',
                                    line: { color: '#f44336', width: 2, dash: 'dash' }
                                  },
                                  {
                                    x: reportData.transformer_load_analysis.visualization_data.voltage.time,
                                    y: reportData.transformer_load_analysis.visualization_data.voltage.under_limit,
                                    type: 'scatter',
                                    mode: 'lines',
                                    name: 'Under Voltage Limit',
                                    line: { color: '#ff9800', width: 2, dash: 'dash' }
                                  },
                                  {
                                    x: reportData.transformer_load_analysis.visualization_data.voltage.time,
                                    y: reportData.transformer_load_analysis.visualization_data.voltage.nominal,
                                    type: 'scatter',
                                    mode: 'lines',
                                    name: 'Nominal Voltage',
                                    line: { color: '#757575', width: 1, dash: 'dot' }
                                  }
                                ]}
                                layout={{
                                  title: {
                                    text: 'Voltage Profile Over Time (All Phases)',
                                    font: { size: 16, color: '#333' }
                                  },
                                  xaxis: { 
                                    title: 'Date & Time',
                                    gridcolor: '#e0e0e0'
                                  },
                                  yaxis: { 
                                    title: 'Voltage (V)',
                                    gridcolor: '#e0e0e0'
                                  },
                                  hovermode: 'x unified',
                                  plot_bgcolor: '#fafafa',
                                  paper_bgcolor: 'white',
                                  autosize: true,
                                  height: 400,
                                  margin: { l: 60, r: 40, t: 60, b: 60 }
                                }}
                                useResizeHandler={true}
                                style={{ width: '100%' }}
                                config={{ displayModeBar: true, responsive: true }}
                              />
                            </div>

                            {/* Voltage vs Load Correlation */}
                            <div style={{ marginBottom: '2rem', backgroundColor: 'white', padding: '1rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                              <Plot
                                data={[
                                  {
                                    x: reportData.transformer_load_analysis.visualization_data.voltage.kva_for_correlation,
                                    y: reportData.transformer_load_analysis.visualization_data.voltage.voltage,
                                    type: 'scatter',
                                    mode: 'markers',
                                    name: 'Voltage vs Load',
                                    marker: {
                                      color: reportData.transformer_load_analysis.visualization_data.voltage.voltage.map(v => {
                                        const overLimit = reportData.transformer_load_analysis.visualization_data.voltage.over_limit[0];
                                        const underLimit = reportData.transformer_load_analysis.visualization_data.voltage.under_limit[0];
                                        if (v > overLimit) return '#f44336';
                                        if (v < underLimit) return '#ff9800';
                                        return '#4caf50';
                                      }),
                                      size: 4,
                                      opacity: 0.6
                                    }
                                  }
                                ]}
                                layout={{
                                  title: {
                                    text: 'Voltage vs Transformer Load Correlation',
                                    font: { size: 16, color: '#333' }
                                  },
                                  xaxis: { 
                                    title: 'Load (kVA)',
                                    gridcolor: '#e0e0e0'
                                  },
                                  yaxis: { 
                                    title: 'Voltage (V)',
                                    gridcolor: '#e0e0e0'
                                  },
                                  hovermode: 'closest',
                                  plot_bgcolor: '#fafafa',
                                  paper_bgcolor: 'white',
                                  autosize: true,
                                  height: 400,
                                  margin: { l: 60, r: 40, t: 60, b: 60 },
                                  annotations: [{
                                    text: 'Green: Normal | Orange: Under-voltage | Red: Over-voltage',
                                    xref: 'paper',
                                    yref: 'paper',
                                    x: 0.5,
                                    y: 1.1,
                                    xanchor: 'center',
                                    yanchor: 'bottom',
                                    showarrow: false,
                                    font: { size: 11, color: '#666' }
                                  }]
                                }}
                                useResizeHandler={true}
                                style={{ width: '100%' }}
                                config={{ displayModeBar: true, responsive: true }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Voltage Statistics */}
                    {reportData.transformer_load_analysis.voltage_analysis && 
                     reportData.transformer_load_analysis.voltage_analysis.has_voltage_data && (
                      <div style={{ marginBottom: '2rem', paddingBottom: '1.5rem', borderBottom: '1px solid #e0e0e0' }}>
                        <h4 style={{ color: '#333', marginBottom: '1rem' }}>Voltage Quality Statistics</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                          <div style={{ padding: '1rem', backgroundColor: '#f3e5f5', borderRadius: '8px', border: '1px solid #9c27b0' }}>
                            <div style={{ fontSize: '0.85rem', color: '#555' }}>Nominal Voltage</div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#7b1fa2' }}>
                              {reportData.transformer_load_analysis.voltage_analysis.nominal_voltage} V
                            </div>
                          </div>
                          <div style={{ padding: '1rem', backgroundColor: '#e8f5e9', borderRadius: '8px', border: '1px solid #4caf50' }}>
                            <div style={{ fontSize: '0.85rem', color: '#555' }}>Average Voltage</div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#2e7d32' }}>
                              {reportData.transformer_load_analysis.voltage_analysis.average_voltage?.toFixed(2)} V
                            </div>
                          </div>
                          <div style={{ padding: '1rem', backgroundColor: '#ffebee', borderRadius: '8px', border: '1px solid #f44336' }}>
                            <div style={{ fontSize: '0.85rem', color: '#555' }}>Over Voltage Limit</div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#c62828' }}>
                              {reportData.transformer_load_analysis.voltage_analysis.over_voltage_limit} V
                            </div>
                          </div>
                          <div style={{ padding: '1rem', backgroundColor: '#fff3e0', borderRadius: '8px', border: '1px solid #ff9800' }}>
                            <div style={{ fontSize: '0.85rem', color: '#555' }}>Under Voltage Limit</div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#ef6c00' }}>
                              {reportData.transformer_load_analysis.voltage_analysis.under_voltage_limit} V
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* KVA Analysis */}
                    {reportData.transformer_load_analysis.kva_analysis && (
                      <div style={{ marginBottom: '1.5rem' }}>
                        <h4 style={{ color: '#333', marginBottom: '1rem' }}>KVA Load Analysis</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                          <div style={{ 
                            padding: '1rem', 
                            backgroundColor: reportData.transformer_load_analysis.kva_analysis.max_load_pct > 100 ? '#ffebee' : '#e8f5e9',
                            borderRadius: '8px',
                            border: `1px solid ${reportData.transformer_load_analysis.kva_analysis.max_load_pct > 100 ? '#f44336' : '#4caf50'}`
                          }}>
                            <div style={{ fontSize: '0.85rem', color: '#555' }}>Max Load</div>
                            <div style={{ 
                              fontSize: '1.2rem', 
                              fontWeight: 'bold', 
                              color: reportData.transformer_load_analysis.kva_analysis.max_load_pct > 100 ? '#c62828' : '#2e7d32' 
                            }}>
                              {reportData.transformer_load_analysis.kva_analysis.max_load_kva.toFixed(2)} kVA
                            </div>
                            <div style={{ fontSize: '0.9rem', color: '#666' }}>
                              {reportData.transformer_load_analysis.kva_analysis.max_load_pct.toFixed(2)}%
                            </div>
                          </div>

                          <div style={{ padding: '1rem', backgroundColor: '#fff3e0', borderRadius: '8px', border: '1px solid #ff9800' }}>
                            <div style={{ fontSize: '0.85rem', color: '#555' }}>Avg Load</div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#ef6c00' }}>
                              {reportData.transformer_load_analysis.kva_analysis.avg_load_kva.toFixed(2)} kVA
                            </div>
                            <div style={{ fontSize: '0.9rem', color: '#666' }}>
                              {reportData.transformer_load_analysis.kva_analysis.avg_load_pct.toFixed(2)}%
                            </div>
                          </div>

                          <div style={{ 
                            padding: '1rem', 
                            backgroundColor: reportData.transformer_load_analysis.kva_analysis.overload_count > 0 ? '#ffebee' : '#e8f5e9',
                            borderRadius: '8px',
                            border: `1px solid ${reportData.transformer_load_analysis.kva_analysis.overload_count > 0 ? '#f44336' : '#4caf50'}`
                          }}>
                            <div style={{ fontSize: '0.85rem', color: '#555' }}>Overload Events</div>
                            <div style={{ 
                              fontSize: '1.2rem', 
                              fontWeight: 'bold', 
                              color: reportData.transformer_load_analysis.kva_analysis.overload_count > 0 ? '#c62828' : '#2e7d32' 
                            }}>
                              {reportData.transformer_load_analysis.kva_analysis.total_overload_events}
                            </div>
                            <div style={{ fontSize: '0.9rem', color: '#666' }}>
                              {reportData.transformer_load_analysis.kva_analysis.overload_duration_hours.toFixed(2)} hours
                            </div>
                          </div>
                        </div>

                        {/* Overload Events Table */}
                        {reportData.transformer_load_analysis.kva_analysis.overload_events && 
                         reportData.transformer_load_analysis.kva_analysis.overload_events.length > 0 && (
                          <div style={{ marginTop: '1rem' }}>
                            <h5 style={{ color: '#d32f2f', marginBottom: '0.5rem' }}>⚠️ Overload Events</h5>
                            <div style={{ overflowX: 'auto' }}>
                              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                <thead>
                                  <tr style={{ backgroundColor: '#ffebee' }}>
                                    <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Start Time</th>
                                    <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>End Time</th>
                                    <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>Max Load (kVA)</th>
                                    <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>Max Load (%)</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {reportData.transformer_load_analysis.kva_analysis.overload_events.map((event, idx) => (
                                    <tr key={idx}>
                                      <td style={{ padding: '6px', border: '1px solid #ddd' }}>{event.start}</td>
                                      <td style={{ padding: '6px', border: '1px solid #ddd' }}>{event.end}</td>
                                      <td style={{ padding: '6px', border: '1px solid #ddd', textAlign: 'right', fontWeight: 'bold', color: '#d32f2f' }}>
                                        {event.max_load_kva.toFixed(2)}
                                      </td>
                                      <td style={{ padding: '6px', border: '1px solid #ddd', textAlign: 'right', fontWeight: 'bold', color: '#d32f2f' }}>
                                        {event.max_load_pct.toFixed(2)}%
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* KW Analysis */}
                    {reportData.transformer_load_analysis.kw_analysis && (
                      <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #ddd' }}>
                        <h4 style={{ color: '#333', marginBottom: '1rem' }}>KW Load Analysis</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                          <div style={{ padding: '1rem', backgroundColor: '#e8f5e9', borderRadius: '8px', border: '1px solid #4caf50' }}>
                            <div style={{ fontSize: '0.85rem', color: '#555' }}>Max Load</div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#2e7d32' }}>
                              {reportData.transformer_load_analysis.kw_analysis.max_load_kw.toFixed(2)} kW
                            </div>
                            <div style={{ fontSize: '0.9rem', color: '#666' }}>
                              {reportData.transformer_load_analysis.kw_analysis.max_load_pct.toFixed(2)}%
                            </div>
                          </div>

                          <div style={{ padding: '1rem', backgroundColor: '#fff3e0', borderRadius: '8px', border: '1px solid #ff9800' }}>
                            <div style={{ fontSize: '0.85rem', color: '#555' }}>Avg Load</div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#ef6c00' }}>
                              {reportData.transformer_load_analysis.kw_analysis.avg_load_kw.toFixed(2)} kW
                            </div>
                            <div style={{ fontSize: '0.9rem', color: '#666' }}>
                              {reportData.transformer_load_analysis.kw_analysis.avg_load_pct.toFixed(2)}%
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Information Section */}
        <div className="card">
          <div className="card-header">
            <span>ℹ️</span>
            About Power Quality Analysis
          </div>
          <div style={{ lineHeight: '1.6' }}>
            <p><strong>Power Quality Analysis</strong> provides comprehensive insights into:</p>
            <ul style={{ marginLeft: '2rem', marginTop: '1rem' }}>
              <li>Voltage and current harmonics analysis</li>
              <li>Power factor measurements</li>
              <li>Voltage sag and swell detection</li>
              <li>Frequency variations and stability</li>
              <li>THD (Total Harmonic Distortion) analysis</li>
              <li>Power quality compliance reporting</li>
              <li>Transformer load analysis and overload detection</li>
            </ul>
            <p style={{ marginTop: '1rem' }}>
              <strong>How to use:</strong> Upload feeder NMD data (required) and transformer load data (required). 
              Consumer files are optional. Enter transformer number and capacity, then generate one comprehensive report 
              that includes voltage quality analysis and transformer load analysis.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PowerQuality;
