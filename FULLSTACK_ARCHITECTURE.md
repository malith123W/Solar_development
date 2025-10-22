# Electrical Data Analyzer - Full Stack Architecture

## Overview

The Electrical Data Analyzer has been restructured into a modern full-stack application with a **Python Flask API backend** and a **React frontend**. This separation provides better scalability, maintainability, and development experience.

## Architecture

```
┌─────────────────┐    HTTP/REST API    ┌─────────────────┐
│                 │ ◄─────────────────► │                 │
│  React Frontend │                     │  Flask Backend  │
│  (Port 3000)    │                     │  (Port 5000)    │
│                 │                     │                 │
└─────────────────┘                     └─────────────────┘
```

## Project Structure

```
Solar_development/
├── backend/                    # Python Flask API Backend
│   ├── app.py                 # Main Flask application
│   ├── requirements.txt       # Python dependencies
│   ├── run.py                 # Backend startup script
│   ├── run.bat               # Windows backend startup
│   ├── uploads/              # File upload directory
│   ├── data_processing.py    # Data processing modules
│   ├── visualization.py      # Graph generation
│   ├── power_quality.py      # Power quality analysis
│   ├── pdf_generation.py     # PDF report generation
│   ├── nmd_analysis.py       # NMD analysis features
│   ├── utils.py              # Utility functions
│   └── test_nmd_analysis.py  # Test suite
│
├── frontend/                  # React Frontend Application
│   ├── public/               # Static assets
│   ├── src/                  # React source code
│   │   ├── components/       # React components
│   │   │   ├── Navbar.js     # Navigation component
│   │   │   ├── Dashboard.js  # Main dashboard
│   │   │   ├── NMDAnalysis.js # NMD analysis page
│   │   │   ├── NMDAnalysisNew.js # Advanced NMD analysis
│   │   │   └── PowerQuality.js # Power quality analysis
│   │   ├── services/         # API services
│   │   │   └── api.js        # API client
│   │   ├── config.js         # Configuration
│   │   ├── App.js            # Main App component
│   │   └── index.js          # Entry point
│   ├── package.json          # Node.js dependencies
│   └── start.bat            # Frontend startup script
│
├── LECO/                     # Data files (unchanged)
├── start_fullstack.bat      # Full stack launcher
└── README.md                # Main documentation
```

## Backend API (Flask)

### Features
- **RESTful API** with JSON responses
- **CORS enabled** for frontend communication
- **File upload handling** for CSV files
- **Session management** for data processing
- **Graph generation** with Plotly
- **PDF report generation**
- **Modular architecture** with separate processors

### API Endpoints

#### Health Check
- `GET /api/health` - API health status

#### General Data Processing
- `POST /api/upload` - Upload CSV file
- `POST /api/generate_graph` - Generate interactive graph
- `POST /api/download_graph` - Download graph as image/PDF

#### NMD Analysis
- `POST /api/nmd/upload` - Upload NMD data
- `POST /api/nmd/generate_graph` - Generate NMD analysis graph

#### Power Quality Analysis
- `POST /api/power-quality/upload-feeder-nmd` - Upload feeder NMD
- `POST /api/power-quality/upload-consumer` - Upload consumer data
- `POST /api/power-quality/generate-report` - Generate PQ report
- `POST /api/power-quality/download-report` - Download JSON report
- `POST /api/power-quality/download-pdf` - Download PDF report

#### Advanced NMD Analysis
- `POST /api/nmd-analysis/upload-feeder` - Upload feeder for correlation
- `POST /api/nmd-analysis/upload-customers` - Upload customer files
- `POST /api/nmd-analysis/analyze` - Perform correlation analysis
- `POST /api/nmd-analysis/visualization` - Generate correlation visualization

### Dependencies
```
Flask==2.3.3
Flask-CORS==4.0.0
pandas==2.2.3
plotly==5.17.0
numpy>=2.0.0
scipy>=1.11.0
scikit-learn>=1.3.0
reportlab==4.0.7
matplotlib==3.8.2
```

## Frontend (React)

### Features
- **Modern React 18** with hooks
- **Material-UI** for beautiful components
- **React Router** for navigation
- **Axios** for API communication
- **Plotly.js** for interactive graphs
- **Responsive design** for all devices
- **File upload** with drag & drop
- **Real-time feedback** and error handling

### Components

#### Navigation
- **Navbar** - Main navigation with routing

#### Pages
- **Dashboard** - Main data upload and visualization
- **NMD Analysis** - Network Metering Data analysis
- **NMD Analysis (New)** - Advanced correlation analysis
- **Power Quality** - Power quality metrics and reports

#### Features
- **File Upload** - Drag & drop CSV file upload
- **Interactive Graphs** - Plotly.js visualizations
- **Date Range Selection** - Filter data by date
- **Parameter Selection** - Choose voltage, current, power, frequency
- **Download Options** - PNG, JPG, PDF, SVG formats
- **Real-time Status** - Upload progress and error handling

### Dependencies
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.20.1",
  "@mui/material": "^5.14.20",
  "@mui/icons-material": "^5.14.19",
  "@mui/x-date-pickers": "^6.18.1",
  "axios": "^1.6.2",
  "plotly.js": "^2.27.0",
  "react-plotly.js": "^2.6.0",
  "dayjs": "^1.11.10"
}
```

## Getting Started

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Git** (optional)

### Quick Start

#### Option 1: Full Stack Launcher (Recommended)
```bash
# Windows
start_fullstack.bat

# This will start both backend and frontend automatically
```

#### Option 2: Manual Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python app.py
# Backend runs on http://localhost:5000
```

**Frontend:**
```bash
cd frontend
npm install
npm start
# Frontend runs on http://localhost:3000
```

### Access Points
- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Health Check**: http://localhost:5000/api/health

## Development

### Backend Development
- Modify `backend/app.py` for new API endpoints
- Add new processors in separate Python files
- Update `backend/requirements.txt` for new dependencies

### Frontend Development
- Modify React components in `frontend/src/components/`
- Update API calls in `frontend/src/services/api.js`
- Add new routes in `frontend/src/App.js`

### API Integration
- All API calls use Axios with proper error handling
- CORS is configured for localhost development
- File uploads use FormData with multipart/form-data
- Responses are JSON with consistent error format

## Deployment

### Backend Deployment
- Use production WSGI server (Gunicorn, uWSGI)
- Set environment variables for production
- Configure reverse proxy (Nginx, Apache)
- Use production database if needed

### Frontend Deployment
- Build production bundle: `npm run build`
- Serve static files with web server
- Configure API URL for production backend
- Use CDN for better performance

## Benefits of New Architecture

### Separation of Concerns
- **Backend**: Pure API logic, data processing, business rules
- **Frontend**: User interface, user experience, client-side logic

### Scalability
- **Independent scaling** of frontend and backend
- **Microservices ready** - can split backend into multiple services
- **CDN deployment** for frontend static assets

### Development Experience
- **Hot reloading** in React development
- **API testing** with tools like Postman
- **Independent deployment** cycles
- **Team collaboration** - frontend and backend teams can work separately

### Technology Benefits
- **Modern React** with hooks and functional components
- **Material-UI** for consistent, professional design
- **TypeScript ready** - can be added for better type safety
- **Testing ready** - both Jest for frontend and pytest for backend

## Migration Notes

### What Changed
- **HTML templates** → **React components**
- **Server-side rendering** → **Client-side rendering**
- **Template inheritance** → **Component composition**
- **Form submissions** → **API calls with Axios**

### What Stayed the Same
- **All Python processing logic** remains unchanged
- **Data processing algorithms** are identical
- **File upload handling** works the same way
- **Graph generation** uses the same Plotly backend
- **PDF generation** remains server-side

### Data Flow
1. **User uploads file** in React frontend
2. **Frontend sends file** to Flask API via Axios
3. **Backend processes file** using existing Python modules
4. **Backend returns JSON** with processed data
5. **Frontend displays results** using React components and Plotly

This architecture provides a solid foundation for future enhancements while maintaining all existing functionality.
