# Quick Start Guide - Full Stack Electrical Data Analyzer

## 🚀 Get Started in 3 Steps

### Step 1: Start the Full Stack Application
```bash
# Windows - Double click or run in terminal
start_fullstack.bat
```

This will automatically:
- Start the Python Flask backend API on port 5000
- Start the React frontend on port 3000
- Open both in separate command windows

### Step 2: Access the Application
- **Frontend**: Open http://localhost:3000 in your browser
- **Backend API**: Available at http://localhost:5000

### Step 3: Upload and Analyze Data
1. Go to the **Dashboard** tab
2. Upload a CSV file using drag & drop
3. Select parameters and date range
4. Click "Generate Graph" to see visualizations
5. Download graphs in various formats

## 📁 Project Structure

```
Solar_development/
├── backend/           # Python Flask API
├── frontend/          # React Application  
├── LECO/             # Your data files
└── start_fullstack.bat # One-click launcher
```

## 🔧 Manual Setup (Alternative)

If the automatic launcher doesn't work:

### Backend Only
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend Only
```bash
cd frontend
npm install
npm start
```

## 📊 Available Features

### Dashboard
- Upload CSV files
- Generate interactive graphs
- Download in PNG, JPG, PDF, SVG formats
- Filter by date range and parameters

### NMD Analysis
- Network Metering Data analysis
- Customer-specific visualizations
- Time-series analysis

### NMD Analysis (New)
- Advanced correlation analysis
- Feeder-customer relationships
- Statistical analysis with visualizations

### Power Quality
- Power quality metrics
- Comprehensive reports
- PDF report generation
- Multi-consumer analysis

## 🛠️ Troubleshooting

### Backend Issues
- Ensure Python 3.8+ is installed
- Check if port 5000 is available
- Install dependencies: `pip install -r backend/requirements.txt`

### Frontend Issues
- Ensure Node.js 16+ is installed
- Check if port 3000 is available
- Install dependencies: `npm install` in frontend folder

### API Connection Issues
- Verify backend is running on http://localhost:5000
- Check browser console for CORS errors
- Ensure both servers are running simultaneously

## 📝 API Endpoints

The backend provides these main API endpoints:
- `POST /api/upload` - Upload CSV files
- `POST /api/generate_graph` - Generate graphs
- `POST /api/nmd/upload` - Upload NMD data
- `POST /api/power-quality/upload-feeder-nmd` - Upload feeder data
- `GET /api/health` - Check API status

## 🎯 Next Steps

1. **Upload your data** - Use the Dashboard to upload CSV files
2. **Explore features** - Try different analysis types
3. **Generate reports** - Create PDF reports for documentation
4. **Customize** - Modify the code for your specific needs

## 📞 Support

- Check the main `README.md` for detailed documentation
- Review `FULLSTACK_ARCHITECTURE.md` for technical details
- All original functionality is preserved in the new architecture

---

**Happy Analyzing!** ⚡📊
