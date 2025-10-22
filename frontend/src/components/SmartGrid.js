import React, { useState, useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';
import '../App.css';

const API_URL = 'http://localhost:5000/api';

// Network Graph Visualization Component
function NetworkGraphVisualization({ graphData }) {
  if (!graphData || !graphData.nodes || !graphData.edges) {
    return <div>No graph data available</div>;
  }

  const { nodes, edges } = graphData;

  // Calculate SVG dimensions
  const width = 1200;
  const height = 700;
  const padding = 60;

  // Group nodes by level
  const nodesByLevel = {};
  nodes.forEach((node) => {
    const level = node.level || 0;
    if (!nodesByLevel[level]) {
      nodesByLevel[level] = [];
    }
    nodesByLevel[level].push(node);
  });

  // Calculate node positions with proper spacing to avoid overlap
  const levelHeight = (height - 2 * padding) / Math.max(4, Object.keys(nodesByLevel).length);
  const nodePositions = {};
  
  Object.keys(nodesByLevel).forEach((level) => {
    const levelNodes = nodesByLevel[level];
    const numNodes = levelNodes.length;
    const availableWidth = width - 2 * padding;
    
    // Calculate spacing based on number of nodes
    const spacing = numNodes > 1 ? availableWidth / (numNodes + 1) : availableWidth / 2;
    
    levelNodes.forEach((node, index) => {
      const y = padding + parseInt(level) * levelHeight;
      // Distribute nodes evenly across the width
      const x = padding + spacing * (index + 1);
      nodePositions[node.id] = { x, y };
    });
  });

  return (
    <div style={{ width: '100%', overflow: 'auto', backgroundColor: '#f8f9fa', padding: '1rem', borderRadius: '8px' }}>
      <svg width={width} height={height} style={{ border: '1px solid #dee2e6', backgroundColor: 'white', borderRadius: '4px' }}>
        {/* Draw edges with curved paths */}
        {edges.map((edge, idx) => {
          const sourcePos = nodePositions[edge.source];
          const targetPos = nodePositions[edge.target];
          if (!sourcePos || !targetPos) return null;
          
          // Calculate control point for curved line
          const midY = (sourcePos.y + targetPos.y) / 2;
          const path = `M ${sourcePos.x},${sourcePos.y} Q ${sourcePos.x},${midY} ${targetPos.x},${targetPos.y}`;
          
          return (
            <path
              key={`edge-${idx}`}
              d={path}
              stroke="#95A5A6"
              strokeWidth="1.5"
              fill="none"
              opacity="0.6"
            />
          );
        })}

        {/* Draw nodes */}
        {nodes.map((node) => {
          const pos = nodePositions[node.id];
          if (!pos) return null;

          const nodeSize = node.type === 'transformer' ? 35 : node.type === 'feeder' ? 28 : node.type === 'phase' ? 24 : 18;
          const nodeColor = node.color || '#3498DB';
          const textOffset = nodeSize + 18;
          
          // Adjust label position for long labels
          const labelLength = node.label ? node.label.length : 0;
          const fontSize = labelLength > 20 ? 10 : labelLength > 15 ? 11 : 12;

          return (
            <g key={node.id}>
              {/* Node circle with shadow effect */}
              <circle
                cx={pos.x}
                cy={pos.y}
                r={nodeSize + 2}
                fill="#00000020"
              />
              <circle
                cx={pos.x}
                cy={pos.y}
                r={nodeSize}
                fill={nodeColor}
                stroke="#2C3E50"
                strokeWidth="2"
              />
              
              {/* Node label - wrapped for long text */}
              {node.label && node.label.length > 25 ? (
                <>
                  <text
                    x={pos.x}
                    y={pos.y + textOffset}
                    textAnchor="middle"
                    fill="#2C3E50"
                    fontSize={fontSize}
                    fontWeight="500"
                  >
                    {node.label.substring(0, 25)}
                  </text>
                  <text
                    x={pos.x}
                    y={pos.y + textOffset + 12}
                    textAnchor="middle"
                    fill="#2C3E50"
                    fontSize={fontSize}
                    fontWeight="500"
                  >
                    {node.label.substring(25)}
                  </text>
                </>
              ) : (
                <text
                  x={pos.x}
                  y={pos.y + textOffset}
                  textAnchor="middle"
                  fill="#2C3E50"
                  fontSize={fontSize}
                  fontWeight="500"
                >
                  {node.label}
                </text>
              )}

              {/* Customer count badge for feeders/phases */}
              {node.customer_count && node.customer_count > 0 && (
                <text
                  x={pos.x}
                  y={pos.y + 4}
                  textAnchor="middle"
                  fill="white"
                  fontSize="11"
                  fontWeight="bold"
                >
                  {node.customer_count}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div style={{ marginTop: '1rem', display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#2C3E50', border: '2px solid #2C3E50' }}></div>
          <span style={{ fontSize: '0.9rem' }}>Transformer</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#7F8C8D', border: '2px solid #2C3E50' }}></div>
          <span style={{ fontSize: '0.9rem' }}>Feeder</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#E74C3C', border: '2px solid #2C3E50' }}></div>
          <span style={{ fontSize: '0.9rem' }}>Phase A</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#F39C12', border: '2px solid #2C3E50' }}></div>
          <span style={{ fontSize: '0.9rem' }}>Phase B</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#3498DB', border: '2px solid #2C3E50' }}></div>
          <span style={{ fontSize: '0.9rem' }}>Phase C</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#27AE60', border: '2px solid #2C3E50' }}></div>
          <span style={{ fontSize: '0.9rem' }}>Customer</span>
        </div>
      </div>

      {/* Stats */}
      {graphData.stats && (
        <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#e3f2fd', borderRadius: '8px' }}>
          <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
            <div>
              <strong>Total Nodes:</strong> {graphData.stats.total_nodes}
            </div>
            <div>
              <strong>Total Feeders:</strong> {graphData.stats.total_feeders}
            </div>
            <div>
              <strong>Total Customers:</strong> {graphData.stats.total_customers}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SmartGrid() {
  const [sessionId] = useState('smart_grid_' + Date.now());
  const [dashboardData, setDashboardData] = useState(null);
  const [balanceAnalysis, setBalanceAnalysis] = useState(null);
  const [balanceSuggestions, setBalanceSuggestions] = useState(null);
  const [balanceSimulation, setBalanceSimulation] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [forecastComparison, setForecastComparison] = useState(null);
  const [glmFile, setGlmFile] = useState(null);
  const [simulationResult, setSimulationResult] = useState(null);
  const [networkGraph, setNetworkGraph] = useState(null);
  const [tempFileInfo, setTempFileInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  
  // Data upload states
  const [feederFile, setFeederFile] = useState(null);
  const [customerFiles, setCustomerFiles] = useState([]);
  const [transformerFile, setTransformerFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isDataReady, setIsDataReady] = useState(false);
  
  // Transformer parameters
  const [transformerCapacity, setTransformerCapacity] = useState(5000);
  const [primaryVoltage, setPrimaryVoltage] = useState(11000);
  const [secondaryVoltage, setSecondaryVoltage] = useState(400);
  
  // Transformer load analysis
  const [transformerAnalysis, setTransformerAnalysis] = useState(null);
  
  const feederInputRef = useRef(null);
  const customerInputRef = useRef(null);
  const transformerInputRef = useRef(null);
  
  // Forecast settings
  const [forecastSettings, setForecastSettings] = useState({
    model_type: 'prophet',
    forecast_periods: 168,
    customer_id: '',
    feeder_id: '',
    use_transformer: false
  });

  // Load dashboard data on mount
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const response = await fetch(`${API_URL}/smart-grid/dashboard-data?session_id=${sessionId}`);
      const data = await response.json();
      
      if (data.success) {
        setDashboardData(data.dashboard);
      } else if (data.error) {
        // Only log dashboard errors, don't show to user
        console.log('Dashboard status:', data.error);
      }
    } catch (err) {
      // Silently handle dashboard errors - they're not critical
      console.log('Dashboard not available:', err.message);
    }
  };

  // Handle Feeder Upload
  const handleFeederUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }

    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);

      const response = await fetch(`${API_URL}/nmd-analysis/upload-feeder`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      
      if (data.success) {
        setFeederFile(file);
        setSuccess(`Feeder file "${file.name}" uploaded successfully`);
      } else {
        setError(data.error || 'Failed to upload feeder file');
      }
    } catch (err) {
      setError('Error uploading feeder file: ' + err.message);
    }
  };

  // Handle Customer Upload
  const handleCustomerUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    const invalidFiles = files.filter(file => !file.name.endsWith('.csv'));
    if (invalidFiles.length > 0) {
      setError('Please upload only CSV files');
      return;
    }

    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));
      formData.append('session_id', sessionId);

      const response = await fetch(`${API_URL}/nmd-analysis/upload-customers`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      
      if (data.success) {
        setCustomerFiles(prev => [...prev, ...files]);
        setSuccess(`${files.length} customer file(s) uploaded successfully`);
      } else {
        setError(data.error || 'Failed to upload customer files');
      }
    } catch (err) {
      setError('Error uploading customer files: ' + err.message);
    }
  };

  // Load Network Graph
  const loadNetworkGraph = async () => {
    try {
      const response = await fetch(`${API_URL}/smart-grid/network-graph`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          transformer_name: 'Transformer'
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setNetworkGraph(data.graph_data);
      }
    } catch (err) {
      console.log('Could not load network graph:', err.message);
    }
  };

  // Perform NMD Analysis (background)
  const performAnalysis = async () => {
    if (!feederFile || customerFiles.length === 0) {
      setError('Please upload both feeder and customer files');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_URL}/nmd-analysis/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });

      const data = await response.json();
      
      if (data.success) {
        setIsDataReady(true);
        setSuccess('Data analysis completed! You can now use Grid Modeling, Load Balancing, and Forecasting features below.');
        // Reload dashboard data after analysis
        loadDashboardData();
        // Load network graph
        loadNetworkGraph();
      } else {
        setError(data.error || 'Failed to perform analysis');
      }
    } catch (err) {
      setError('Error performing analysis: ' + err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const removeCustomerFile = (index) => {
    setCustomerFiles(prev => prev.filter((_, i) => i !== index));
  };


  // Generate GLM File
  const generateGLM = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`${API_URL}/smart-grid/generate-glm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          transformer_name: 'T1',
          model_name: 'grid_model_' + Date.now(),
          transformer_capacity_kva: transformerCapacity,
          primary_voltage: primaryVoltage,
          secondary_voltage: secondaryVoltage
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setGlmFile(data);
        setTempFileInfo({
          is_temp_file: data.is_temp_file,
          temp_dir: data.temp_dir
        });
        
        // Store transformer analysis if included
        if (data.transformer_analysis) {
          setTransformerAnalysis(data.transformer_analysis);
        }
        
        setSuccess('GLM file generated successfully!' + (data.is_temp_file ? ' (Temporary file - will be cleaned up automatically)' : ''));
      } else {
        setError(data.error || 'Failed to generate GLM file');
      }
    } catch (err) {
      setError('Error generating GLM file: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Run GridLAB-D Simulation
  const runSimulation = async () => {
    if (!glmFile || !glmFile.glm_file) {
      setError('Please generate a GLM file first');
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`${API_URL}/smart-grid/run-simulation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          glm_file: glmFile.glm_file
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSimulationResult(data);
        setSuccess('Simulation completed successfully!');
      } else {
        // Store simulation result with error info for display
        setSimulationResult(data);
        // Don't show error banner for GridLAB-D not installed (already have info banner)
        if (!data.error || !data.error.includes('not installed')) {
          setError(data.error || data.message || 'Simulation failed');
        }
      }
    } catch (err) {
      setError('Error running simulation: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Analyze Load Balance
  const analyzeBalance = async () => {
    if (!glmFile) {
      setError('Please generate a GLM file first');
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`${API_URL}/smart-grid/analyze-balance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          session_id: sessionId,
          glm_file: glmFile.glm_file
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setBalanceAnalysis(data.analysis);
        setSuccess('Balance analysis completed successfully!');
        loadDashboardData();
      } else {
        setError(data.error || 'Failed to analyze balance');
      }
    } catch (err) {
      setError('Error analyzing balance: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Get Balance Suggestions
  const getSuggestions = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`${API_URL}/smart-grid/suggest-balancing`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setBalanceSuggestions(data.suggestions);
        setSuccess(`Generated ${data.suggestions.total_suggestions} balancing suggestions`);
      } else {
        setError(data.error || 'Failed to get suggestions');
      }
    } catch (err) {
      setError('Error getting suggestions: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Simulate Balancing
  const simulateBalancing = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`${API_URL}/smart-grid/simulate-balancing`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          moves: []  // Use default suggestions
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setBalanceSimulation(data.simulation);
        setSuccess('Balancing simulation completed successfully!');
      } else {
        setError(data.error || 'Failed to simulate balancing');
      }
    } catch (err) {
      setError('Error simulating balancing: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle Transformer Upload
  const handleTransformerUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }

    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);

      const response = await fetch(`${API_URL}/smart-grid/upload-transformer`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      
      if (data.success) {
        setTransformerFile(file);
        setSuccess(`Transformer data "${file.name}" uploaded successfully`);
        loadDashboardData();
      } else {
        setError(data.error || 'Failed to upload transformer data');
      }
    } catch (err) {
      setError('Error uploading transformer data: ' + err.message);
    }
  };

  // Run Forecast
  const runForecast = async () => {
    if (!forecastSettings.use_transformer && !forecastSettings.customer_id && !forecastSettings.feeder_id) {
      setError('Please enter a Customer ID, Feeder ID, or select transformer forecasting');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`${API_URL}/smart-grid/forecast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          ...forecastSettings
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setForecastData(data);
        const sourceText = data.source === 'transformer' ? 'transformer' : (forecastSettings.customer_id ? 'customer' : 'feeder');
        setSuccess(`Forecast generated for ${sourceText} using ${data.model_type} model`);
        loadDashboardData();
      } else {
        setError(data.error || 'Failed to run forecast');
      }
    } catch (err) {
      setError('Error running forecast: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Compare Forecast Models
  const compareForecastModels = async () => {
    if (!forecastSettings.customer_id) {
      setError('Please enter a customer ID for model comparison');
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`${API_URL}/smart-grid/compare-forecast-models`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          customer_id: forecastSettings.customer_id,
          forecast_periods: forecastSettings.forecast_periods
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setForecastComparison(data.comparison);
        setSuccess('Model comparison completed successfully!');
        loadDashboardData();
      } else {
        setError(data.error || 'Failed to compare models');
      }
    } catch (err) {
      setError('Error comparing models: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Download Smart Grid PDF Report
  const handleDownloadPdf = async () => {
    if (!balanceAnalysis) {
      setError('Please run analysis first');
      return;
    }

    setIsDownloadingPdf(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_URL}/smart-grid/export_pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          transformer_name: 'Smart Grid Transformer'
        })
      });

      if (!response.ok) {
        throw new Error('Failed to download PDF');
      }

      // Create download link
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `smart_grid_analysis_report_${Date.now()}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setSuccess('Smart Grid PDF report downloaded successfully!');
    } catch (error) {
      setError('Failed to download PDF: ' + error.message);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  // Clean up temporary files
  const cleanupTempFiles = async (specificFile = null) => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`${API_URL}/smart-grid/cleanup-temp-files`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: specificFile
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSuccess(data.message);
        // Update temp file info
        getTempFileInfo();
        // Clear GLM file if it was cleaned up
        if (specificFile && glmFile && glmFile.glm_file === specificFile) {
          setGlmFile(null);
          setTempFileInfo(null);
        }
      } else {
        setError(data.error || 'Failed to cleanup temporary files');
      }
    } catch (err) {
      setError('Error cleaning up temporary files: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Get temporary file information
  const getTempFileInfo = async () => {
    try {
      const response = await fetch(`${API_URL}/smart-grid/temp-file-info`);
      const data = await response.json();
      
      if (data.success) {
        setTempFileInfo(data.temp_info);
      }
    } catch (err) {
      console.error('Error getting temp file info:', err);
    }
  };

  return (
    <div className="container">
      <div className="paper">
        {/* Header */}
        <div className="header">
          <h1>Smart Load Balancing & Forecasting</h1>
          <p>Analyze, optimize, and forecast grid performance using GridLAB-D and AI/ML</p>
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

        {/* Info Banner about GridLAB-D */}
        <div style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#e3f2fd', borderRadius: '8px', border: '1px solid #90caf9' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.2rem' }}>ℹ️</span>
            <div>
              <strong style={{ color: '#1976d2' }}>Note:</strong>
              <span style={{ color: '#1976d2', marginLeft: '0.5rem' }}>
                GridLAB-D installation is optional. All features work without it, except running actual power flow simulations.
                You can still generate GLM files, analyze load balance, and run forecasts.
              </span>
            </div>
          </div>
        </div>

        {/* Step 1: Data Upload Section */}
        <div style={{ marginBottom: '2rem' }}>
          <p style={{ marginBottom: '1.5rem', color: '#666', fontSize: '1rem' }}>
            Upload feeder NMD and customer data files to enable analysis and forecasting. Optionally upload transformer data for advanced analysis.
          </p>

          <div className="grid grid-3" style={{ gap: '1.5rem' }}>
            {/* 1. Upload Feeder NMD */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '12px', 
              padding: '1.5rem',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              border: '2px solid #e0e0e0'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <div style={{ 
                  backgroundColor: '#2196F3', 
                  color: 'white', 
                  width: '28px', 
                  height: '28px', 
                  borderRadius: '50%', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  fontSize: '0.9rem'
                }}>
                  1
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <span style={{ fontSize: '1.3rem' }}>📁</span>
                  <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#333' }}>Upload Feeder NMD</h3>
                </div>
              </div>
              
              <div
                className="upload-area"
                onClick={() => feederInputRef.current?.click()}
                style={{ border: '2px dashed #2196F3', cursor: 'pointer' }}
              >
                <input
                  ref={feederInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFeederUpload}
                  style={{ display: 'none' }}
                />
                <div className="upload-icon" style={{ fontSize: '3rem' }}>📁</div>
                <div className="upload-text" style={{ fontWeight: '600', color: '#333' }}>Upload Feeder NMD</div>
                <div className="upload-subtext" style={{ color: '#666', fontSize: '0.85rem' }}>
                  Feeder network metering data
                </div>
              </div>
              
              {feederFile && (
                <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#e8f5e9', borderRadius: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#2e7d32' }}>
                    <span style={{ fontSize: '1.2rem' }}>✓</span>
                    <span style={{ fontSize: '0.9rem', fontWeight: '500' }}>{feederFile.name}</span>
                  </div>
                </div>
              )}
            </div>

            {/* 2. Upload Consumer Data */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '12px', 
              padding: '1.5rem',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              border: '2px solid #e0e0e0'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <div style={{ 
                  backgroundColor: '#2196F3', 
                  color: 'white', 
                  width: '28px', 
                  height: '28px', 
                  borderRadius: '50%', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  fontSize: '0.9rem'
                }}>
                  2
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <span style={{ fontSize: '1.3rem' }}>📁</span>
                  <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#333' }}>Upload Consumer Data (Optional)</h3>
                </div>
              </div>
              
              <div
                className="upload-area"
                onClick={() => customerInputRef.current?.click()}
                style={{ border: '2px dashed #2196F3', cursor: 'pointer' }}
              >
                <input
                  ref={customerInputRef}
                  type="file"
                  accept=".csv"
                  multiple
                  onChange={handleCustomerUpload}
                  style={{ display: 'none' }}
                />
                <div className="upload-icon" style={{ fontSize: '3rem' }}>📁</div>
                <div className="upload-text" style={{ fontWeight: '600', color: '#333' }}>Upload Consumer Files</div>
                <div className="upload-subtext" style={{ color: '#666', fontSize: '0.85rem' }}>
                  Multiple consumer data files
                </div>
              </div>
              
              {customerFiles.length > 0 && (
                <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#e8f5e9', borderRadius: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#2e7d32', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '1.2rem' }}>✓</span>
                    <span style={{ fontSize: '0.9rem', fontWeight: '500' }}>{customerFiles.length} file(s) uploaded</span>
                  </div>
                  <ul style={{ margin: 0, padding: 0, listStyle: 'none', maxHeight: '100px', overflowY: 'auto' }}>
                    {customerFiles.map((file, index) => (
                      <li key={index} style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between',
                        padding: '0.25rem 0',
                        fontSize: '0.85rem'
                      }}>
                        <span style={{ color: '#2e7d32' }}>{file.name}</span>
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            removeCustomerFile(index);
                          }}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#d32f2f',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            padding: '0.2rem 0.4rem'
                          }}
                        >
                          ✕
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* 3. Transformer Load Data */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '12px', 
              padding: '1.5rem',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              border: '2px solid #e0e0e0'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <div style={{ 
                  backgroundColor: '#2196F3', 
                  color: 'white', 
                  width: '28px', 
                  height: '28px', 
                  borderRadius: '50%', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  fontSize: '0.9rem'
                }}>
                  3
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <span style={{ fontSize: '1.3rem' }}>⚡</span>
                  <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#333' }}>Transformer Load Data</h3>
                </div>
              </div>
              
              <div
                className="upload-area"
                onClick={() => transformerInputRef.current?.click()}
                style={{ border: '2px dashed #ff9800', cursor: 'pointer', backgroundColor: '#fff8e1' }}
              >
                <input
                  ref={transformerInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleTransformerUpload}
                  style={{ display: 'none' }}
                />
                <div className="upload-icon" style={{ fontSize: '3rem' }}>📁</div>
                <div className="upload-text" style={{ fontWeight: '600', color: '#333' }}>Upload Load Data</div>
                <div className="upload-subtext" style={{ color: '#666', fontSize: '0.85rem' }}>
                  Transformer KVA/KW data
                </div>
              </div>
              
              {transformerFile && (
                <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#e8f5e9', borderRadius: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#2e7d32' }}>
                    <span style={{ fontSize: '1.2rem' }}>✓</span>
                    <span style={{ fontSize: '0.9rem', fontWeight: '500' }}>{transformerFile.name}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          <button
            className="btn btn-primary"
            onClick={performAnalysis}
            disabled={!feederFile || customerFiles.length === 0 || isAnalyzing}
            style={{ width: '100%', marginTop: '1rem' }}
          >
            {isAnalyzing ? (
              <div className="loading">
                <div className="spinner"></div>
                <span>Analyzing data...</span>
              </div>
            ) : (
              <>
                <span>🔬</span>
                {isDataReady ? 'Data Ready - Re-analyze' : 'Analyze Data'}
              </>
            )}
          </button>

          {isDataReady && (
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#d4edda', borderRadius: '8px', border: '1px solid #c3e6cb' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '1.5rem' }}>✅</span>
                <div>
                  <strong style={{ color: '#155724' }}>Data Analysis Complete!</strong>
                  <p style={{ margin: '0.25rem 0 0 0', color: '#155724', fontSize: '0.9rem' }}>
                    You can now use all features below: Grid Modeling, Load Balancing, and Forecasting
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Network Topology Graph */}
          {networkGraph && (
            <div style={{ marginTop: '1.5rem', padding: '1.5rem', backgroundColor: 'white', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
              <h3 style={{ marginBottom: '1rem', color: '#333', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '1.5rem' }}>🔌</span>
                Network Topology
              </h3>
              <NetworkGraphVisualization graphData={networkGraph} />
            </div>
          )}
        </div>

        {/* Step 2: Grid Modeling & Simulation */}
        <div className="card">
          <div className="card-header">
            <span>🏗️</span>
            Step 2: Grid Modeling & Simulation
          </div>
          
          <div className="grid grid-2">
            <div>
              <h4 style={{ marginBottom: '0.5rem' }}>Grid Modeling</h4>
              <p style={{ marginBottom: '1rem', color: '#666', fontSize: '0.9rem' }}>
                Generate GridLAB-D .glm files from NMD and customer data
              </p>
              
              {/* Transformer Parameters */}
              <div style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                <h5 style={{ marginBottom: '0.5rem', color: '#333' }}>Transformer Parameters</h5>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <div>
                    <label style={{ fontSize: '0.8rem', color: '#666' }}>Capacity (kVA)</label>
                    <input
                      type="number"
                      value={transformerCapacity}
                      onChange={(e) => setTransformerCapacity(parseFloat(e.target.value) || 5000)}
                      style={{ width: '100%', padding: '0.25rem', fontSize: '0.9rem' }}
                      min="100"
                      max="10000"
                      step="100"
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.8rem', color: '#666' }}>Primary Voltage (V)</label>
                    <input
                      type="number"
                      value={primaryVoltage}
                      onChange={(e) => setPrimaryVoltage(parseFloat(e.target.value) || 11000)}
                      style={{ width: '100%', padding: '0.25rem', fontSize: '0.9rem' }}
                      min="1000"
                      max="50000"
                      step="1000"
                    />
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#666' }}>Secondary Voltage (V)</label>
                  <input
                    type="number"
                    value={secondaryVoltage}
                    onChange={(e) => setSecondaryVoltage(parseFloat(e.target.value) || 400)}
                    style={{ width: '100%', padding: '0.25rem', fontSize: '0.9rem' }}
                    min="100"
                    max="1000"
                    step="50"
                  />
                </div>
              </div>
              
              <button
                className="btn btn-primary"
                onClick={generateGLM}
                disabled={loading || !isDataReady}
                style={{ width: '100%' }}
              >
                {loading ? (
                  <div className="loading">
                    <div className="spinner"></div>
                    <span>Generating...</span>
                  </div>
                ) : (
                  <>
                    <span>🏗️</span>
                    Generate GLM File
                  </>
                )}
              </button>
              {glmFile && (
                <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#d4edda', borderRadius: '8px' }}>
                  <div className="file-name">✓ {glmFile.glm_file}</div>
                  <p style={{ fontSize: '0.9rem', marginTop: '0.5rem', color: '#155724' }}>
                    Customers: {glmFile.total_customers}
                  </p>
                  <p style={{ fontSize: '0.8rem', marginTop: '0.25rem', color: '#155724' }}>
                    Transformer: {glmFile.transformer} ({glmFile.transformer_capacity_kva} kVA)
                  </p>
                  <p style={{ fontSize: '0.8rem', marginTop: '0.25rem', color: '#155724' }}>
                    Voltage: {glmFile.primary_voltage}V → {glmFile.secondary_voltage}V
                  </p>
                  
                </div>
              )}
            </div>

            <div>
              <h4 style={{ marginBottom: '0.5rem' }}>Load Flow Analysis</h4>
              <p style={{ marginBottom: '1rem', color: '#666', fontSize: '0.9rem' }}>
                Run GridLAB-D simulation for voltage and loss analysis
              </p>
              <button
                className="btn btn-primary"
                onClick={runSimulation}
                disabled={loading || !glmFile}
                style={{ width: '100%' }}
              >
                {loading ? (
                  <div className="loading">
                    <div className="spinner"></div>
                    <span>Running...</span>
                  </div>
                ) : (
                  <>
                    <span>⚡</span>
                    Run Simulation
                  </>
                )}
              </button>
              {simulationResult && (
                <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: simulationResult.success ? '#d4edda' : '#fff3cd', borderRadius: '8px', border: simulationResult.success ? '1px solid #c3e6cb' : '1px solid #ffc107' }}>
                  {simulationResult.success ? (
                    <div className="file-name">✓ Simulation completed</div>
                  ) : (
                    <div style={{ color: '#856404' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span>ℹ️</span>
                        <div>
                          {simulationResult.error && simulationResult.error.includes('not installed') ? (
                            <>
                              <strong>GridLAB-D not installed</strong>
                              <p style={{ fontSize: '0.85rem', marginTop: '0.25rem', marginBottom: '0.5rem' }}>
                                To run power flow simulations, install GridLAB-D from{' '}
                                <a href="https://www.gridlabd.org/" target="_blank" rel="noopener noreferrer" style={{ color: '#0056b3', textDecoration: 'underline' }}>
                                  gridlabd.org
                                </a>
                              </p>
                              <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>
                                <strong>You can still use:</strong> GLM file generation, Load Balancing, and Forecasting features.
                              </p>
                            </>
                          ) : (
                            <>
                              <div>✗ {simulationResult.error}</div>
                              {simulationResult.message && <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>{simulationResult.message}</p>}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          
        </div>

        {/* Step 3: Load Balancing Section */}
        <div className="card">
          <div className="card-header">
            <span>⚖️</span>
            Step 3: Load Balancing Analysis
          </div>
          <p style={{ marginBottom: '1rem', color: '#666' }}>
            Analyze phase imbalance and get optimization suggestions
          </p>
          <button
            className="btn btn-primary"
            onClick={analyzeBalance}
            disabled={loading || !glmFile}
            style={{ width: '100%' }}
          >
            {loading ? (
              <div className="loading">
                <div className="spinner"></div>
                <span>Analyzing...</span>
              </div>
            ) : (
              <>
                <span>⚖️</span>
                Analyze Load Balance
              </>
            )}
          </button>
          
          {!glmFile && (
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#fff3cd', borderRadius: '8px', border: '1px solid #ffc107' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#856404' }}>
                <span>ℹ️</span>
                <div>
                  <strong>Generate GLM file first</strong>
                  <p style={{ fontSize: '0.85rem', marginTop: '0.25rem', marginBottom: 0 }}>
                    Please generate a GridLAB-D .glm file in the Grid Modeling section above before running load balancing analysis.
                  </p>
                </div>
              </div>
            </div>
          )}

          {balanceAnalysis && (
            <div style={{ marginTop: '2rem' }}>
              {/* PDF Download Button */}
              <div style={{ marginBottom: '1rem', textAlign: 'center' }}>
                <button
                  className="btn btn-success"
                  onClick={handleDownloadPdf}
                  disabled={isDownloadingPdf}
                  style={{ width: 'auto', padding: '0.75rem 1.5rem' }}
                >
                  {isDownloadingPdf ? (
                    <div className="loading">
                      <div className="spinner"></div>
                      <span>Generating PDF...</span>
                    </div>
                  ) : (
                    <>
                      <span>📄</span>
                      Download PDF Report
                    </>
                  )}
                </button>
              </div>

              {/* Summary Stats */}
              <div className="grid grid-3" style={{ marginBottom: '1rem' }}>
                <div className="stat-item">
                  <strong>Total Feeders:</strong> {balanceAnalysis.overall_stats?.total_feeders || 0}
                </div>
                <div className="stat-item">
                  <strong style={{ color: '#28a745' }}>Balanced:</strong> {balanceAnalysis.overall_stats?.balanced_feeders?.length || 0}
                </div>
                <div className="stat-item">
                  <strong style={{ color: '#ffc107' }}>Imbalanced:</strong> {balanceAnalysis.overall_stats?.imbalanced_feeders?.length || 0}
                </div>
              </div>

              {/* Feeder Details */}
              <h4 style={{ marginTop: '1rem', marginBottom: '0.5rem' }}>Feeder Details:</h4>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Feeder ID</th>
                      <th>Imbalance</th>
                      <th>Total Load (kW)</th>
                      <th>Customers</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(balanceAnalysis.feeder_analysis || {}).map(([feederId, feederData]) => (
                      <tr key={feederId}>
                        <td>{feederId}</td>
                        <td>
                          <span 
                            className="correlation-badge"
                            style={{
                              backgroundColor: feederData.is_balanced ? '#28a745' : '#ffc107',
                              color: 'white',
                              padding: '0.25rem 0.5rem',
                              borderRadius: '4px'
                            }}
                          >
                            {feederData.imbalance_percentage?.toFixed(2)}%
                          </span>
                        </td>
                        <td>{feederData.total_load_kw?.toFixed(2)}</td>
                        <td>{feederData.total_customers}</td>
                        <td>
                          {feederData.is_balanced ? (
                            <span style={{ color: '#28a745' }}>✓ Balanced</span>
                          ) : (
                            <span style={{ color: '#ffc107' }}>⚠ Imbalanced</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Transformer Analysis */}
              {balanceAnalysis.overall_stats?.transformer_analysis && (
                <div style={{ marginTop: '1.5rem' }}>
                  <h4 style={{ marginBottom: '1rem', color: '#2196F3' }}>
                    ⚡ Transformer Load Analysis
                  </h4>
                  <div style={{ padding: '1rem', backgroundColor: '#f0f8ff', borderRadius: '8px', border: '1px solid #2196F3' }}>
                    
                    {/* Phase Current Analysis */}
                    {balanceAnalysis.overall_stats.transformer_analysis.phase_analysis && Object.keys(balanceAnalysis.overall_stats.transformer_analysis.phase_analysis).length > 0 && (
                      <div style={{ marginBottom: '1rem' }}>
                        <h5 style={{ marginBottom: '0.5rem' }}>Phase Current Analysis:</h5>
                        <div className="grid grid-3" style={{ gap: '1rem' }}>
                          {Object.entries(balanceAnalysis.overall_stats.transformer_analysis.phase_analysis)
                            .filter(([key]) => key.startsWith('Phase'))
                            .map(([phase, data]) => (
                            <div key={phase} style={{ padding: '0.75rem', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #90caf9' }}>
                              <h6 style={{ marginBottom: '0.5rem', color: '#1976d2' }}>{phase}</h6>
                              <div style={{ fontSize: '0.85rem' }}>
                                <div>Avg: <strong>{data.avg_current?.toFixed(2)} A</strong></div>
                                <div>Max: <strong>{data.max_current?.toFixed(2)} A</strong></div>
                                <div>Min: <strong>{data.min_current?.toFixed(2)} A</strong></div>
                              </div>
                            </div>
                          ))}
                        </div>
                        {balanceAnalysis.overall_stats.transformer_analysis.phase_analysis.current_imbalance_percentage && (
                          <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: balanceAnalysis.overall_stats.transformer_analysis.phase_analysis.current_imbalance_percentage > 15 ? '#fff3cd' : '#d4edda', borderRadius: '4px' }}>
                            <strong>Current Imbalance: </strong>
                            <span style={{ color: balanceAnalysis.overall_stats.transformer_analysis.phase_analysis.current_imbalance_percentage > 15 ? '#856404' : '#155724' }}>
                              {balanceAnalysis.overall_stats.transformer_analysis.phase_analysis.current_imbalance_percentage.toFixed(2)}%
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Load Statistics */}
                    {balanceAnalysis.overall_stats.transformer_analysis.load_statistics && (
                      <div style={{ marginBottom: '1rem' }}>
                        <h5 style={{ marginBottom: '0.5rem' }}>Load Statistics:</h5>
                        <div className="grid grid-2" style={{ gap: '1rem' }}>
                          {balanceAnalysis.overall_stats.transformer_analysis.load_statistics.kw && (
                            <div style={{ padding: '0.75rem', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #90caf9' }}>
                              <h6 style={{ color: '#1976d2' }}>Active Power (kW)</h6>
                              <div style={{ fontSize: '0.85rem' }}>
                                <div>Avg: <strong>{balanceAnalysis.overall_stats.transformer_analysis.load_statistics.kw.avg_load_kw?.toFixed(2)} kW</strong></div>
                                <div>Max: <strong>{balanceAnalysis.overall_stats.transformer_analysis.load_statistics.kw.max_load_kw?.toFixed(2)} kW</strong></div>
                                <div>Min: <strong>{balanceAnalysis.overall_stats.transformer_analysis.load_statistics.kw.min_load_kw?.toFixed(2)} kW</strong></div>
                              </div>
                            </div>
                          )}
                          {balanceAnalysis.overall_stats.transformer_analysis.load_statistics.kva && (
                            <div style={{ padding: '0.75rem', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #90caf9' }}>
                              <h6 style={{ color: '#1976d2' }}>Apparent Power (kVA)</h6>
                              <div style={{ fontSize: '0.85rem' }}>
                                <div>Avg: <strong>{balanceAnalysis.overall_stats.transformer_analysis.load_statistics.kva.avg_load_kva?.toFixed(2)} kVA</strong></div>
                                <div>Max: <strong>{balanceAnalysis.overall_stats.transformer_analysis.load_statistics.kva.max_load_kva?.toFixed(2)} kVA</strong></div>
                                <div>Min: <strong>{balanceAnalysis.overall_stats.transformer_analysis.load_statistics.kva.min_load_kva?.toFixed(2)} kVA</strong></div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Utilization */}
                    {balanceAnalysis.overall_stats.transformer_analysis.utilization && (
                      <div style={{ padding: '0.75rem', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #90caf9' }}>
                        <h5 style={{ marginBottom: '0.5rem', color: '#1976d2' }}>Transformer Utilization:</h5>
                        <div className="grid grid-2">
                          <div>
                            <div>Capacity: <strong>{balanceAnalysis.overall_stats.transformer_analysis.utilization.transformer_capacity_kva} kVA</strong></div>
                            <div>Peak Load: <strong>{balanceAnalysis.overall_stats.transformer_analysis.utilization.peak_load_kva?.toFixed(2)} kVA</strong></div>
                          </div>
                          <div>
                            <div>Utilization: <strong style={{ color: balanceAnalysis.overall_stats.transformer_analysis.utilization.utilization_percentage > 80 ? '#dc3545' : '#28a745' }}>
                              {balanceAnalysis.overall_stats.transformer_analysis.utilization.utilization_percentage?.toFixed(2)}%
                            </strong></div>
                            <div>Available: <strong>{balanceAnalysis.overall_stats.transformer_analysis.utilization.available_capacity_kva?.toFixed(2)} kVA</strong></div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Power Factor */}
                    {balanceAnalysis.overall_stats.transformer_analysis.power_factor_analysis && Object.keys(balanceAnalysis.overall_stats.transformer_analysis.power_factor_analysis).length > 0 && (
                      <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #90caf9' }}>
                        <h5 style={{ marginBottom: '0.5rem', color: '#1976d2' }}>Power Factor:</h5>
                        <div className="grid grid-2">
                          <div>Average: <strong>{balanceAnalysis.overall_stats.transformer_analysis.power_factor_analysis.avg_power_factor?.toFixed(3)}</strong></div>
                          <div>Range: <strong>{balanceAnalysis.overall_stats.transformer_analysis.power_factor_analysis.min_power_factor?.toFixed(3)} - {balanceAnalysis.overall_stats.transformer_analysis.power_factor_analysis.max_power_factor?.toFixed(3)}</strong></div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="grid grid-2" style={{ marginTop: '1rem' }}>
                <button className="btn btn-primary" onClick={getSuggestions} disabled={loading}>
                  <span>💡</span>
                  Get Balancing Suggestions
                </button>
                {balanceSuggestions && (
                  <button className="btn btn-primary" onClick={simulateBalancing} disabled={loading}>
                    <span>🔄</span>
                    Simulate Balancing
                  </button>
                )}
              </div>

              {/* Suggestions */}
              {balanceSuggestions && (
                <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#e3f2fd', borderRadius: '8px' }}>
                  <h4>Balancing Suggestions ({balanceSuggestions.total_suggestions}):</h4>
                  <div className="table-container" style={{ marginTop: '0.5rem' }}>
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Customer ID</th>
                          <th>Feeder</th>
                          <th>From Phase</th>
                          <th>To Phase</th>
                          <th>Load (kW)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {balanceSuggestions.suggestions?.slice(0, 10).map((suggestion, idx) => (
                          <tr key={idx}>
                            <td>{suggestion.customer_id}</td>
                            <td>{suggestion.feeder_id}</td>
                            <td>{suggestion.from_phase}</td>
                            <td>{suggestion.to_phase}</td>
                            <td>{suggestion.customer_load_kw?.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Simulation Results */}
              {balanceSimulation && (
                <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#d4edda', borderRadius: '8px' }}>
                  <h4>Simulation Results:</h4>
                  <div className="grid grid-2" style={{ marginTop: '0.5rem' }}>
                    <div>
                      <h5>Before Balancing:</h5>
                      <ul style={{ listStyle: 'none', padding: 0 }}>
                        <li>Avg Imbalance: <strong>{(balanceSimulation.before?.avg_imbalance * 100)?.toFixed(2)}%</strong></li>
                        <li>Total Load: <strong>{balanceSimulation.before?.total_load_kw?.toFixed(2)} kW</strong></li>
                        <li>Avg Voltage: <strong>{balanceSimulation.before?.avg_voltage?.toFixed(2)} V</strong></li>
                      </ul>
                    </div>
                    <div>
                      <h5>After Balancing:</h5>
                      <ul style={{ listStyle: 'none', padding: 0 }}>
                        <li>Avg Imbalance: <strong>{(balanceSimulation.after?.avg_imbalance * 100)?.toFixed(2)}%</strong></li>
                        <li>Total Load: <strong>{balanceSimulation.after?.total_load_kw?.toFixed(2)} kW</strong></li>
                        <li>Avg Voltage: <strong>{balanceSimulation.after?.avg_voltage?.toFixed(2)} V</strong></li>
                      </ul>
                    </div>
                  </div>
                  <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: '#155724', color: 'white', borderRadius: '4px' }}>
                    <strong>Improvements:</strong> Loss Reduction: {balanceSimulation.improvements?.loss_reduction_percentage?.toFixed(2)}%, 
                    Voltage Improvement: {balanceSimulation.improvements?.voltage_improvement?.toFixed(2)}V
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Step 4: Load Forecasting Section */}
        <div className="card">
          <div className="card-header">
            <span>📈</span>
            Step 4: Load Forecasting
          </div>
          <p style={{ marginBottom: '1rem', color: '#666' }}>
            Predict future loads using AI/ML models (ARIMA, Prophet, LSTM)
          </p>

          <div className="grid grid-2">
            <div className="form-group">
              <label className="form-label">Model Type:</label>
              <select
                className="form-select"
                value={forecastSettings.model_type}
                onChange={(e) => setForecastSettings({...forecastSettings, model_type: e.target.value})}
              >
                <option value="arima">ARIMA</option>
                <option value="prophet">Prophet</option>
                <option value="lstm">LSTM</option>
              </select>
            </div>
            
            <div className="form-group">
              <label className="form-label">Forecast Periods:</label>
              <input
                className="form-control"
                type="number"
                value={forecastSettings.forecast_periods}
                onChange={(e) => setForecastSettings({...forecastSettings, forecast_periods: parseInt(e.target.value)})}
              />
            </div>
          </div>

          <div className="grid grid-2">
            <div className="form-group">
              <label className="form-label">Customer ID:</label>
              <input
                className="form-control"
                type="text"
                value={forecastSettings.customer_id}
                onChange={(e) => setForecastSettings({...forecastSettings, customer_id: e.target.value, feeder_id: '', use_transformer: false})}
                placeholder="Enter customer ID"
                disabled={forecastSettings.use_transformer}
              />
            </div>
            
            <div className="form-group">
              <label className="form-label">Feeder ID (or leave Customer ID empty):</label>
              <input
                className="form-control"
                type="text"
                value={forecastSettings.feeder_id}
                onChange={(e) => setForecastSettings({...forecastSettings, feeder_id: e.target.value, customer_id: '', use_transformer: false})}
                placeholder="Enter feeder ID"
                disabled={forecastSettings.use_transformer}
              />
            </div>
          </div>

          {/* Transformer Forecasting Option */}
          {transformerFile && (
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f0f8ff', borderRadius: '8px', border: '1px solid #2196F3' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={forecastSettings.use_transformer}
                  onChange={(e) => setForecastSettings({
                    ...forecastSettings, 
                    use_transformer: e.target.checked,
                    customer_id: e.target.checked ? '' : forecastSettings.customer_id,
                    feeder_id: e.target.checked ? '' : forecastSettings.feeder_id
                  })}
                  style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                />
                <span style={{ fontWeight: 'bold', color: '#2196F3' }}>
                  ⚡ Use Transformer Load Data for Forecasting
                </span>
              </label>
              <p style={{ margin: '0.5rem 0 0 1.5rem', color: '#666', fontSize: '0.9rem' }}>
                Forecast transformer load using historical transformer data instead of customer/feeder data
              </p>
            </div>
          )}

          <div className="grid grid-2" style={{ marginTop: '1rem' }}>
            <button 
              className="btn btn-primary" 
              onClick={runForecast} 
              disabled={loading || (!isDataReady && !forecastSettings.use_transformer)}
            >
              {loading ? (
                <div className="loading">
                  <div className="spinner"></div>
                  <span>Forecasting...</span>
                </div>
              ) : (
                <>
                  <span>📈</span>
                  Run Forecast
                </>
              )}
            </button>
            <button className="btn btn-secondary" onClick={compareForecastModels} disabled={loading || !isDataReady}>
              <span>🔄</span>
              Compare All Models
            </button>
          </div>

          {/* Forecast Results */}
          {forecastData && forecastData.success && (
            <div style={{ marginTop: '2rem' }}>
              <h4>Forecast Results - {forecastData.model_type}</h4>
              
              <div className="grid grid-3" style={{ marginBottom: '1rem' }}>
                <div className="stat-item">
                  <strong>MAE:</strong> {forecastData.metrics?.mae?.toFixed(2)}
                </div>
                <div className="stat-item">
                  <strong>RMSE:</strong> {forecastData.metrics?.rmse?.toFixed(2)}
                </div>
                <div className="stat-item">
                  <strong>MAPE:</strong> {forecastData.metrics?.mape?.toFixed(2)}%
                </div>
              </div>

              <div style={{ height: '500px', marginTop: '1rem' }}>
                <Plot
                  data={[
                    {
                      x: forecastData.historical?.timestamps || [],
                      y: forecastData.historical?.values || [],
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Historical',
                      line: { color: '#3498db' }
                    },
                    {
                      x: forecastData.forecast?.timestamps || [],
                      y: forecastData.forecast?.values || [],
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Forecast',
                      line: { color: '#e74c3c', dash: 'dash' }
                    },
                    {
                      x: forecastData.forecast?.timestamps || [],
                      y: forecastData.forecast?.upper_bound || [],
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Upper Bound',
                      line: { color: '#95a5a6', width: 1 },
                      fill: 'tonexty',
                      fillcolor: 'rgba(231, 76, 60, 0.1)'
                    },
                    {
                      x: forecastData.forecast?.timestamps || [],
                      y: forecastData.forecast?.lower_bound || [],
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Lower Bound',
                      line: { color: '#95a5a6', width: 1 }
                    }
                  ]}
                  layout={{
                    title: 'Load Forecast',
                    xaxis: { title: 'Time' },
                    yaxis: { title: 'Load (kW)' },
                    height: 500,
                    autosize: true
                  }}
                  config={{ responsive: true }}
                  style={{ width: '100%' }}
                />
              </div>
            </div>
          )}

          {/* Model Comparison */}
          {forecastComparison && (
            <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#e3f2fd', borderRadius: '8px' }}>
              <h4>Model Comparison</h4>
              <p>Best Model: <strong>{forecastComparison.best_model?.toUpperCase()}</strong> (MAPE: {forecastComparison.best_mape?.toFixed(2)}%)</p>
              
              <div className="table-container" style={{ marginTop: '0.5rem' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Model</th>
                      <th>Status</th>
                      <th>MAE</th>
                      <th>RMSE</th>
                      <th>MAPE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(forecastComparison.models || {}).map(([modelName, result]) => (
                      <tr key={modelName}>
                        <td><strong>{modelName.toUpperCase()}</strong></td>
                        <td>
                          {result.success ? (
                            <span style={{ color: '#28a745' }}>✓ Success</span>
                          ) : (
                            <span style={{ color: '#dc3545' }}>✗ Failed</span>
                          )}
                        </td>
                        <td>{result.metrics?.mae?.toFixed(2) || 'N/A'}</td>
                        <td>{result.metrics?.rmse?.toFixed(2) || 'N/A'}</td>
                        <td>{result.metrics?.mape?.toFixed(2) || 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Information Section */}
        <div className="card">
          <div className="card-header">
            <span>ℹ️</span>
            How to Use
          </div>
          <div style={{ lineHeight: '1.6' }}>
            <h4 style={{ marginBottom: '0.5rem' }}>Complete Workflow:</h4>
            <ol style={{ marginLeft: '2rem', marginTop: '0.5rem' }}>
              <li><strong>Upload Data:</strong> Upload feeder NMD and customer CSV files</li>
              <li><strong>Analyze Data:</strong> Click "Analyze Data" to run correlation analysis (this runs in the background)</li>
              <li><strong>Grid Modeling:</strong> Generate GLM file to model your grid in GridLAB-D format</li>
              <li><strong>Load Flow:</strong> Run simulation to understand voltage profiles and losses (optional, requires GridLAB-D installed)</li>
              <li><strong>Load Balancing:</strong> Analyze phase imbalances and get optimization suggestions</li>
              <li><strong>Forecasting:</strong> Predict future loads using AI/ML models (ARIMA, Prophet, LSTM)</li>
            </ol>
            
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#fff3cd', borderRadius: '8px' }}>
              <h5 style={{ marginTop: 0 }}>📝 Note:</h5>
              <ul style={{ marginLeft: '1rem', marginBottom: 0 }}>
                <li>GridLAB-D installation is optional - only needed for running actual simulations</li>
                <li>GLM files can be generated and exported without GridLAB-D</li>
                <li>All features require data to be uploaded and analyzed first (Step 1)</li>
                <li>Forecasting models may take 30-120 seconds depending on data size</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Temporary File Management Section */}
        {tempFileInfo && tempFileInfo.use_temp_files && (
          <div className="card">
            <div className="card-header">
              <span>🗂️</span>
              Temporary File Management
            </div>
            <div style={{ padding: '1rem' }}>
              <p style={{ marginBottom: '1rem' }}>
                GLM files are stored temporarily and will be automatically cleaned up after use.
              </p>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <button 
                  onClick={() => cleanupTempFiles()}
                  className="btn btn-warning"
                  disabled={loading}
                >
                  🗑️ Clean All Temp Files
                </button>
                {glmFile && (
                  <button 
                    onClick={() => cleanupTempFiles(glmFile.glm_file)}
                    className="btn btn-outline-warning"
                    disabled={loading}
                  >
                    🗑️ Clean Current GLM
                  </button>
                )}
                <button 
                  onClick={getTempFileInfo}
                  className="btn btn-outline-info"
                  disabled={loading}
                >
                  ℹ️ Check Temp Files
                </button>
              </div>
              {tempFileInfo.temp_files && tempFileInfo.temp_files.length > 0 && (
                <div style={{ marginTop: '1rem', padding: '0.5rem', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                  <strong>Current temporary files:</strong>
                  <ul style={{ marginTop: '0.5rem', marginBottom: 0 }}>
                    {tempFileInfo.temp_files.map((file, index) => (
                      <li key={index} style={{ fontSize: '0.9rem', fontFamily: 'monospace' }}>
                        {file.split('/').pop()}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SmartGrid;
