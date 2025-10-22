import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';

const VoltageVariation = ({ voltageData, width = 1200, height = 800 }) => {
  const [selectedGraph, setSelectedGraph] = useState('overview');
  const [selectedFeeders, setSelectedFeeders] = useState([]);

  useEffect(() => {
    if (voltageData && voltageData.analysis && voltageData.analysis.feeder_analysis) {
      const feeders = Object.keys(voltageData.analysis.feeder_analysis);
      setSelectedFeeders(feeders);
    }
  }, [voltageData]);

  if (!voltageData || !voltageData.analysis) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#7F8C8D' }}>
        <p>No voltage variation data available</p>
      </div>
    );
  }

  const { analysis, graphs, profile, report } = voltageData;
  const { feeder_analysis, overall_stats, voltage_limits } = analysis;

  const renderOverviewGraph = () => {
    if (!graphs || !graphs.graph_data) {
      return <div>No overview graph data available</div>;
    }

    return (
      <Plot
        data={graphs.graph_data.data}
        layout={{
          ...graphs.graph_data.layout,
          width: width,
          height: height,
          title: {
            ...graphs.graph_data.layout.title,
            font: { size: 18 }
          }
        }}
        config={{
          displayModeBar: true,
          modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
          displaylogo: false
        }}
      />
    );
  };

  const renderVoltageProfile = () => {
    if (!profile || !profile.graph_data) {
      return <div>No voltage profile data available</div>;
    }

    return (
      <Plot
        data={profile.graph_data.data}
        layout={{
          ...profile.graph_data.layout,
          width: width,
          height: 600,
          title: {
            ...profile.graph_data.layout.title,
            font: { size: 18 }
          }
        }}
        config={{
          displayModeBar: true,
          modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
          displaylogo: false
        }}
      />
    );
  };

  const renderSummaryCards = () => {
    if (!report || !report.summary) {
      return null;
    }

    const { summary } = report;
    
    return (
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '15px', 
        marginBottom: '20px' 
      }}>
        <div style={{ 
          backgroundColor: '#E8F5E8', 
          padding: '15px', 
          borderRadius: '8px', 
          border: '1px solid #4CAF50',
          textAlign: 'center'
        }}>
          <h4 style={{ margin: '0 0 5px 0', color: '#2E7D32' }}>Total Feeders</h4>
          <p style={{ margin: '0', fontSize: '24px', fontWeight: 'bold', color: '#1B5E20' }}>
            {summary.total_feeders}
          </p>
        </div>
        
        <div style={{ 
          backgroundColor: '#FFF3E0', 
          padding: '15px', 
          borderRadius: '8px', 
          border: '1px solid #FF9800',
          textAlign: 'center'
        }}>
          <h4 style={{ margin: '0 0 5px 0', color: '#E65100' }}>Avg Voltage Drop</h4>
          <p style={{ margin: '0', fontSize: '24px', fontWeight: 'bold', color: '#BF360C' }}>
            {summary.overall_voltage_drop_mean?.toFixed(1)}V
          </p>
        </div>
        
        <div style={{ 
          backgroundColor: '#FFEBEE', 
          padding: '15px', 
          borderRadius: '8px', 
          border: '1px solid #F44336',
          textAlign: 'center'
        }}>
          <h4 style={{ margin: '0 0 5px 0', color: '#C62828' }}>Max Voltage Drop</h4>
          <p style={{ margin: '0', fontSize: '24px', fontWeight: 'bold', color: '#B71C1C' }}>
            {summary.overall_voltage_drop_max?.toFixed(1)}V
          </p>
        </div>
        
        <div style={{ 
          backgroundColor: '#E3F2FD', 
          padding: '15px', 
          borderRadius: '8px', 
          border: '1px solid #2196F3',
          textAlign: 'center'
        }}>
          <h4 style={{ margin: '0 0 5px 0', color: '#1565C0' }}>Voltage Variation</h4>
          <p style={{ margin: '0', fontSize: '24px', fontWeight: 'bold', color: '#0D47A1' }}>
            {summary.overall_voltage_variation?.toFixed(1)}V
          </p>
        </div>
      </div>
    );
  };

  const renderFeederTable = () => {
    if (!feeder_analysis) {
      return null;
    }

    const feeders = Object.entries(feeder_analysis).map(([feeder, data]) => ({
      feeder,
      voltageDrop: data.overall_voltage_drop_mean,
      voltageVariation: data.overall_voltage_variation,
      readings: data.total_readings,
      consumers: data.consumer_count
    }));

    return (
      <div style={{ marginTop: '20px' }}>
        <h4 style={{ marginBottom: '15px', color: '#333' }}>Feeder Analysis Details</h4>
        <div style={{ 
          backgroundColor: 'white', 
          borderRadius: '8px', 
          overflow: 'hidden',
          border: '1px solid #e9ecef'
        }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            fontSize: '14px'
          }}>
            <thead>
              <tr style={{ backgroundColor: '#f8f9fa' }}>
                <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #dee2e6' }}>Feeder</th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>Voltage Drop (V)</th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>Variation (V)</th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>Readings</th>
                <th style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>Consumers</th>
              </tr>
            </thead>
            <tbody>
              {feeders.map((feeder, index) => (
                <tr key={feeder.feeder} style={{ 
                  backgroundColor: index % 2 === 0 ? 'white' : '#f8f9fa' 
                }}>
                  <td style={{ padding: '12px', borderBottom: '1px solid #dee2e6' }}>
                    <strong>{feeder.feeder}</strong>
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right', 
                    borderBottom: '1px solid #dee2e6',
                    color: feeder.voltageDrop > 10 ? '#d32f2f' : '#2e7d32'
                  }}>
                    {feeder.voltageDrop.toFixed(1)}V
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right', 
                    borderBottom: '1px solid #dee2e6',
                    color: feeder.voltageVariation > 5 ? '#d32f2f' : '#2e7d32'
                  }}>
                    {feeder.voltageVariation.toFixed(1)}V
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                    {feeder.readings}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right', borderBottom: '1px solid #dee2e6' }}>
                    {feeder.consumers}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderRecommendations = () => {
    if (!report || !report.recommendations || report.recommendations.length === 0) {
      return null;
    }

    return (
      <div style={{ marginTop: '20px' }}>
        <h4 style={{ marginBottom: '15px', color: '#333' }}>Recommendations</h4>
        <div style={{ 
          backgroundColor: '#FFF3E0', 
          padding: '15px', 
          borderRadius: '8px', 
          border: '1px solid #FF9800'
        }}>
          <ul style={{ margin: '0', paddingLeft: '20px' }}>
            {report.recommendations.map((rec, index) => (
              <li key={index} style={{ marginBottom: '8px', color: '#E65100' }}>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  const renderVoltageLimits = () => {
    if (!voltage_limits) {
      return null;
    }

    return (
      <div style={{ marginTop: '20px' }}>
        <h4 style={{ marginBottom: '15px', color: '#333' }}>Voltage Limits Reference</h4>
        <div style={{ 
          backgroundColor: '#F5F5F5', 
          padding: '15px', 
          borderRadius: '8px', 
          border: '1px solid #BDBDBD'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
            <div>
              <strong>Nominal:</strong> {voltage_limits.nominal}V
            </div>
            <div>
              <strong>Min Standard:</strong> {voltage_limits.min_standard}V
            </div>
            <div>
              <strong>Max Standard:</strong> {voltage_limits.max_standard}V
            </div>
            <div>
              <strong>Min Strict:</strong> {voltage_limits.min_strict}V
            </div>
            <div>
              <strong>Max Strict:</strong> {voltage_limits.max_strict}V
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div style={{ 
      width: '100%', 
      backgroundColor: '#F8F9FA', 
      borderRadius: '8px',
      padding: '20px',
      marginTop: '20px'
    }}>
      <h3 style={{ marginBottom: '20px', color: '#2C3E50', fontWeight: 'bold' }}>
        ⚡ Voltage Variation Analysis
      </h3>
      
      {/* Summary Cards */}
      {renderSummaryCards()}
      
      {/* Graph Selection Tabs */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ 
          display: 'flex', 
          gap: '10px', 
          marginBottom: '15px',
          borderBottom: '1px solid #dee2e6'
        }}>
          <button
            onClick={() => setSelectedGraph('overview')}
            style={{
              padding: '10px 20px',
              border: 'none',
              backgroundColor: selectedGraph === 'overview' ? '#007BFF' : '#E9ECEF',
              color: selectedGraph === 'overview' ? 'white' : '#495057',
              borderRadius: '4px 4px 0 0',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: selectedGraph === 'overview' ? 'bold' : 'normal'
            }}
          >
            Overview Analysis
          </button>
          <button
            onClick={() => setSelectedGraph('profile')}
            style={{
              padding: '10px 20px',
              border: 'none',
              backgroundColor: selectedGraph === 'profile' ? '#007BFF' : '#E9ECEF',
              color: selectedGraph === 'profile' ? 'white' : '#495057',
              borderRadius: '4px 4px 0 0',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: selectedGraph === 'profile' ? 'bold' : 'normal'
            }}
          >
            Voltage Profile
          </button>
        </div>
        
        {/* Graph Content */}
        <div style={{ 
          backgroundColor: 'white', 
          borderRadius: '8px', 
          padding: '20px',
          border: '1px solid #dee2e6'
        }}>
          {selectedGraph === 'overview' && renderOverviewGraph()}
          {selectedGraph === 'profile' && renderVoltageProfile()}
        </div>
      </div>
      
      {/* Feeder Analysis Table */}
      {renderFeederTable()}
      
      {/* Recommendations */}
      {renderRecommendations()}
      
      {/* Voltage Limits Reference */}
      {renderVoltageLimits()}
    </div>
  );
};

export default VoltageVariation;
