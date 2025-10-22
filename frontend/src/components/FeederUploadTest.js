import React, { useState } from 'react';
import FeederWiseUpload from './FeederWiseUpload';

const FeederUploadTest = () => {
  const [sessionId] = useState(`test_session_${Date.now()}`);
  const [availableFeeders] = useState([
    '0700082108', '0700188511', '0700759004', '0701114909', '0701369108'
  ]);

  const handleConsumerUpload = (feederName, files) => {
    console.log(`Uploaded ${files.length} files for feeder ${feederName}:`, files);
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>Feeder-wise Upload Test</h1>
      <p>Test the feeder-wise consumer data upload functionality</p>
      
      <FeederWiseUpload 
        sessionId={sessionId}
        availableFeeders={availableFeeders}
        onConsumerUpload={handleConsumerUpload}
      />
    </div>
  );
};

export default FeederUploadTest;
