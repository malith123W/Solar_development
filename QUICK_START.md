# 🚀 Quick Start Guide

## ⚡ Electrical Data Analyzer - Ready to Use!

Your web application is now **fully functional** and ready to analyze CSV electrical data with support for multiple formats, including your LOAD_PROFILE files!

## 🎯 What You Can Do Right Now

1. **Upload CSV files** with electrical data in multiple formats
2. **Handle large files** up to 100MB with thousands of data points
3. **View interactive graphs** showing time vs. voltage for each phase
4. **Select specific phases** to display or compare
5. **Hover over graphs** to see exact voltage values at specific timestamps
6. **Download graphs** as PNG or JPEG images
7. **View statistics** including min, max, average, and standard deviation

## 🚀 Start the Application

### Option 1: Simple Start (Windows)
```bash
# Double-click this file or run in command prompt:
run.bat
```

### Option 2: Python Script
```bash
python run.py
```

### Option 3: Direct Start
```bash
python app.py
```

## 🌐 Access the Application

Once started, open your web browser and go to:
```
http://localhost:5000
```

## 📁 Supported CSV Formats

### 🆕 **LOAD_PROFILE Format (Your File Type)**
- **DATE**: YYYY-MM-DD (e.g., "2025-06-30")
- **TIME**: HH:MM:SS (e.g., "09:00:00")
- **PHASE_A_INST._VOLTAGE (V)**: Phase A voltage values
- **PHASE_B_INST._VOLTAGE (V)**: Phase B voltage values
- **PHASE_C_INST._VOLTAGE (V)**: Phase C voltage values

**Features**: Automatically combines DATE and TIME columns for the x-axis

### 🔄 **New Format**
- **DATE**: DD/MM/YYYY (e.g., "30/06/2025")
- **TIME**: HH:MM:SS (e.g., "09:00:00")
- **PHASE_A_INST**: Phase A voltage values
- **PHASE_B_**: Phase B voltage values
- **PHASE_C_**: Phase C voltage values

### 🔄 **Legacy Format**
- **time**: Combined timestamp
- **Phase_A**: Phase A voltage values
- **Phase_B**: Phase B voltage values
- **Phase_C**: Phase C voltage values

## 📊 Your LOAD_PROFILE File

Your file `LOAD_PROFILE_HISTORICAL_READINGS_INVENTORY_25_08_2025.csv` contains:
- **2,813 rows** of electrical data
- **15-minute intervals** over multiple days
- **Three-phase voltage measurements** (A, B, C)
- **Additional electrical parameters** (current, power factor, etc.)

The app will automatically:
- ✅ **Detect your format** as LOAD_PROFILE
- ✅ **Combine DATE + TIME** for the x-axis
- ✅ **Extract voltage data** from the correct columns
- ✅ **Generate beautiful graphs** with all phases
- ✅ **Calculate statistics** for each phase

## 🎨 Features at Your Fingertips

- **Modern UI**: Beautiful, responsive design that works on all devices
- **Format Detection**: Automatically detects and handles your CSV format
- **Large File Support**: Optimized for files up to 100MB
- **Real-time Updates**: Change phase selection and see graphs update instantly
- **Interactive Charts**: Zoom, pan, and hover for detailed analysis
- **Export Options**: Save your graphs in high-quality formats
- **Statistics Dashboard**: Comprehensive data analysis at a glance

## 🔧 Technical Details

- **Backend**: Flask (Python) with pandas for data processing
- **Frontend**: HTML5 + CSS3 + JavaScript with Plotly for charts
- **Data Formats**: Supports LOAD_PROFILE, new, and legacy CSV structures
- **File Size**: Up to 100MB CSV files supported
- **Port**: 5000 (configurable)

## 🎉 You're All Set!

Your application is now **100% compatible** with your LOAD_PROFILE CSV files:

1. **Start the app**: `python app.py` or double-click `run.bat`
2. **Open browser**: Go to `http://localhost:5000`
3. **Upload your file**: Drag & drop `LOAD_PROFILE_HISTORICAL_READINGS_INVENTORY_25_08_2025.csv`
4. **Enjoy analysis**: Beautiful time-series graphs with all three phases!

**Your data format is fully supported** - the app will automatically detect it and create perfect time-series visualizations showing voltage trends over time.

## 📋 Next Steps

1. **Upload your actual file** - it will work perfectly!
2. **Explore the data** - zoom, pan, and hover for details
3. **Customize graphs** - select which phases to display
4. **Export results** - save graphs as images for reports
5. **Analyze trends** - use the statistics dashboard

---

**Need help?** Check the main README.md for detailed documentation and troubleshooting.
