import React, { useState, useRef } from 'react';
import { 
  pqUploadConsumer
} from '../services/api';
// Removed unused imports

const FeederWiseUpload = ({ sessionId, availableFeeders, onConsumerUpload }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [uploadingStates, setUploadingStates] = useState({});
  const [uploadedFiles, setUploadedFiles] = useState({});
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  const fileInputRefs = useRef({});

  // Only show feeders if NMD data has been uploaded (availableFeeders is provided)
  const feederNames = availableFeeders && availableFeeders.length > 0 
    ? availableFeeders 
    : [];

  const handleFileUpload = async (feederName, event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    const invalidFiles = files.filter(file => !file.name.endsWith('.csv'));
    if (invalidFiles.length > 0) {
      setError('Please upload only CSV files');
      return;
    }

    setUploadingStates(prev => ({ ...prev, [feederName]: true }));
    setError(null);
    setSuccess(null);

    try {
      const uploadPromises = files.map((file, index) => 
        pqUploadConsumer(
          file, 
          sessionId, 
          file.name.replace('.csv', ''), 
          feederName
        )
      );

      await Promise.all(uploadPromises);
      
      setUploadedFiles(prev => ({
        ...prev,
        [feederName]: [...(prev[feederName] || []), ...files]
      }));
      
      setSuccess(`${files.length} file(s) uploaded successfully for feeder ${feederName}!`);
      
      if (onConsumerUpload) {
        onConsumerUpload(feederName, files);
      }
    } catch (error) {
      setError(error.response?.data?.error || `Failed to upload files for feeder ${feederName}`);
    } finally {
      setUploadingStates(prev => ({ ...prev, [feederName]: false }));
    }
  };

  const removeFile = (feederName, fileIndex) => {
    setUploadedFiles(prev => ({
      ...prev,
      [feederName]: prev[feederName]?.filter((_, i) => i !== fileIndex) || []
    }));
  };

  const getFileInputRef = (feederName) => {
    if (!fileInputRefs.current[feederName]) {
      fileInputRefs.current[feederName] = React.createRef();
    }
    return fileInputRefs.current[feederName];
  };

  return (
    <div className="feeder-upload-container">
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

      {/* Show message if no feeders available */}
      {feederNames.length === 0 ? (
        <div className="no-feeders-message">
          <div className="message-icon">📋</div>
          <h4>Upload Feeder NMD First</h4>
          <p>Please upload a Feeder NMD file to see available feeders for consumer data upload.</p>
        </div>
      ) : (
        /* Feeder Tabs */
        <div className="feeder-tabs">
        <div className="tab-header">
          <h3>Upload Consumer Data by Feeder</h3>
          <p>Select a feeder and upload consumer data files for that specific feeder</p>
        </div>
        
        <div className="tab-navigation">
          {feederNames.map((feederName, index) => (
            <button
              key={feederName}
              className={`tab-button ${activeTab === index ? 'active' : ''}`}
              onClick={() => setActiveTab(index)}
            >
              <span className="feeder-id">{feederName}</span>
              {uploadedFiles[feederName]?.length > 0 && (
                <span className="file-count">{uploadedFiles[feederName].length}</span>
              )}
            </button>
          ))}
        </div>

        {/* Upload Summary */}
        {Object.keys(uploadedFiles).length > 0 && (
          <div className="upload-summary">
            <div className="summary-header">
              <span className="summary-icon">✓</span>
              <span className="summary-text">Files uploaded successfully</span>
            </div>
            <div className="summary-stats">
              {Object.entries(uploadedFiles).map(([feederName, files]) => (
                files.length > 0 && (
                  <div key={feederName} className="summary-item">
                    <span className="feeder-name">{feederName}</span>
                    <span className="file-count">{files.length} file(s)</span>
                  </div>
                )
              ))}
            </div>
          </div>
        )}

        {/* Tab Content */}
        <div className="tab-content">
          {feederNames.map((feederName, index) => (
            <div
              key={feederName}
              className={`tab-panel ${activeTab === index ? 'active' : ''}`}
            >
              <div className="upload-section">
                <div className="upload-header">
                  <h4>Feeder: {feederName}</h4>
                  <p>Upload consumer data files for this feeder</p>
                </div>
                
                <div
                  className="upload-area"
                  onClick={() => getFileInputRef(feederName).current?.click()}
                >
                  <input
                    ref={getFileInputRef(feederName)}
                    type="file"
                    accept=".csv"
                    multiple
                    onChange={(e) => handleFileUpload(feederName, e)}
                    style={{ display: 'none' }}
                  />
                  
                  {uploadingStates[feederName] ? (
                    <div className="loading">
                      <div className="spinner"></div>
                      <span>Uploading...</span>
                    </div>
                  ) : (
                    <>
                      <div className="upload-icon">📁</div>
                      <div className="upload-text">Upload Consumer Files</div>
                      <div className="upload-subtext">Multiple CSV files for feeder {feederName}</div>
                    </>
                  )}
                </div>

                {/* Uploaded Files List */}
                {uploadedFiles[feederName]?.length > 0 && (
                  <div className="uploaded-files">
                    <div className="upload-success">
                      <span className="success-icon">✓</span>
                      <span className="success-text">{uploadedFiles[feederName].length} file(s) uploaded</span>
                    </div>
                    <div className="file-list-compact">
                      {uploadedFiles[feederName].map((file, fileIndex) => (
                        <div key={fileIndex} className="file-item-compact">
                          <span className="file-name-compact">{file.name}</span>
                          <button 
                            className="file-remove-compact"
                            onClick={() => removeFile(feederName, fileIndex)}
                            title="Remove file"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
      )}

      <style jsx>{`
        .feeder-upload-container {
          margin-top: 2rem;
        }

        .feeder-tabs {
          background: white;
          border-radius: 12px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          overflow: hidden;
        }

        .tab-header {
          padding: 1.5rem;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .tab-header h3 {
          margin: 0 0 0.5rem 0;
          font-size: 1.25rem;
          font-weight: 600;
        }

        .tab-header p {
          margin: 0;
          opacity: 0.9;
          font-size: 0.9rem;
        }

        .tab-navigation {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          padding: 1rem;
          background: #f8f9fa;
          border-bottom: 1px solid #e9ecef;
          max-height: 200px;
          overflow-y: auto;
        }

        .tab-button {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          border: 2px solid #e9ecef;
          border-radius: 8px;
          background: white;
          color: #495057;
          font-size: 0.9rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          position: relative;
        }

        .tab-button:hover {
          border-color: #667eea;
          color: #667eea;
          transform: translateY(-1px);
          box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
        }

        .tab-button.active {
          border-color: #667eea;
          background: #667eea;
          color: white;
          box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
        }

        .feeder-id {
          font-family: 'Courier New', monospace;
          font-weight: 600;
        }

        .file-count {
          background: #28a745;
          color: white;
          border-radius: 50%;
          width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.75rem;
          font-weight: bold;
        }

        .tab-button.active .file-count {
          background: rgba(255, 255, 255, 0.3);
          color: white;
        }

        .tab-content {
          position: relative;
        }

        .tab-panel {
          display: none;
          padding: 2rem;
        }

        .tab-panel.active {
          display: block;
        }

        .upload-section {
          max-width: 600px;
        }

        .upload-header h4 {
          margin: 0 0 0.5rem 0;
          color: #333;
          font-size: 1.1rem;
        }

        .upload-header p {
          margin: 0 0 1.5rem 0;
          color: #666;
          font-size: 0.9rem;
        }

        .upload-area {
          border: 2px dashed #ddd;
          border-radius: 12px;
          padding: 2rem;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s ease;
          background: #fafafa;
        }

        .upload-area:hover {
          border-color: #667eea;
          background: #f0f4ff;
        }

        .upload-icon {
          font-size: 3rem;
          margin-bottom: 1rem;
        }

        .upload-text {
          font-size: 1.1rem;
          font-weight: 600;
          color: #333;
          margin-bottom: 0.5rem;
        }

        .upload-subtext {
          color: #666;
          font-size: 0.9rem;
        }

        .uploaded-files {
          margin-top: 1.5rem;
          padding: 1rem;
          background: #d4edda;
          border-radius: 8px;
          border: 1px solid #c3e6cb;
        }

        .upload-success {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 1rem;
          color: #155724;
          font-weight: 500;
        }

        .success-icon {
          font-size: 1.2rem;
          color: #28a745;
        }

        .success-text {
          font-size: 0.9rem;
        }

        .file-list-compact {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .file-item-compact {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem 0.75rem;
          background: rgba(255, 255, 255, 0.7);
          border-radius: 4px;
          border: 1px solid rgba(40, 167, 69, 0.3);
        }

        .file-name-compact {
          color: #155724;
          font-weight: 500;
          font-size: 0.9rem;
          font-family: 'Courier New', monospace;
        }

        .file-remove-compact {
          background: #dc3545;
          color: white;
          border: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          font-size: 0.8rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.2s ease;
          font-weight: bold;
        }

        .file-remove-compact:hover {
          background: #c82333;
        }

        .loading {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          color: #667eea;
          font-weight: 500;
        }

        .spinner {
          width: 20px;
          height: 20px;
          border: 2px solid #f3f3f3;
          border-top: 2px solid #667eea;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .alert {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 1rem;
          border-radius: 8px;
          margin-bottom: 1rem;
          font-size: 0.9rem;
        }

        .alert-error {
          background: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
        }

        .alert-success {
          background: #d4edda;
          color: #155724;
          border: 1px solid #c3e6cb;
        }

        .alert-close {
          background: none;
          border: none;
          font-size: 1.2rem;
          cursor: pointer;
          margin-left: auto;
          opacity: 0.7;
        }

        .alert-close:hover {
          opacity: 1;
        }

        .upload-summary {
          padding: 1rem;
          background: #d4edda;
          border: 1px solid #c3e6cb;
          border-radius: 8px;
          margin: 1rem;
        }

        .summary-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 1rem;
          color: #155724;
          font-weight: 500;
        }

        .summary-icon {
          font-size: 1.2rem;
          color: #28a745;
        }

        .summary-text {
          font-size: 0.9rem;
        }

        .summary-stats {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .summary-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 0.75rem;
          background: white;
          border: 1px solid #c3e6cb;
          border-radius: 6px;
          font-size: 0.9rem;
        }

        .feeder-name {
          font-family: 'Courier New', monospace;
          font-weight: 600;
          color: #333;
        }

        .summary-item .file-count {
          background: #28a745;
          color: white;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-size: 0.8rem;
          font-weight: bold;
        }

        .no-feeders-message {
          text-align: center;
          padding: 3rem 2rem;
          background: #f8f9fa;
          border: 2px dashed #dee2e6;
          border-radius: 12px;
          color: #6c757d;
        }

        .message-icon {
          font-size: 3rem;
          margin-bottom: 1rem;
        }

        .no-feeders-message h4 {
          margin: 0 0 0.5rem 0;
          color: #495057;
          font-size: 1.2rem;
          font-weight: 600;
        }

        .no-feeders-message p {
          margin: 0;
          font-size: 1rem;
          line-height: 1.5;
        }
      `}</style>
    </div>
  );
};

export default FeederWiseUpload;
