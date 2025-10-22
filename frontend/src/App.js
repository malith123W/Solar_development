import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Import components
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import NMDAnalysis from './components/NMDAnalysis';
import PowerQuality from './components/PowerQuality';
// Removed NMDAnalysisNew and SmartGrid

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/nmd" element={<NMDAnalysis />} />
            <Route path="/power-quality" element={<PowerQuality />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;