import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { label: 'Dashboard', path: '/dashboard', icon: '📊' },
    { label: 'NMD Analysis', path: '/nmd', icon: '📈' },
    { label: 'NMD Analysis (New)', path: '/nmd-analysis', icon: '🔬' },
    { label: 'Power Quality', path: '/power-quality', icon: '⚡' },
    { label: 'Smart Grid', path: '/smart-grid', icon: '🏗️' },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-content">
        <div 
          className="navbar-title"
          onClick={() => navigate('/dashboard')}
        >
          ⚡ Electrical Data Analyzer
        </div>
        
        <div className="navbar-menu">
          {menuItems.map((item) => (
            <button
              key={item.path}
              className={`navbar-item ${location.pathname === item.path ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
            >
              <span>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;