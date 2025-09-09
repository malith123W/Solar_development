# 🎯 LOAD_PROFILE Format Support

## ⚡ Your File is Now Fully Supported!

The Electrical Data Analyzer has been **specifically updated** to handle your `LOAD_PROFILE_HISTORICAL_READINGS_INVENTORY_25_08_2025.csv` file format.

## 📊 Your File Structure

Your CSV file contains:
- **Filename**: `LOAD_PROFILE_HISTORICAL_READINGS_INVENTORY_25_08_2025.csv`
- **Size**: ~444KB
- **Rows**: 2,813 data points
- **Columns**: 21 columns including electrical measurements
- **Time Interval**: 15-minute intervals
- **Date Range**: Multiple days of electrical data

## 🔍 Key Columns for Analysis

### **Time Columns (Automatically Combined)**
- `DATE`: YYYY-MM-DD format (e.g., "2025-06-30")
- `TIME`: HH:MM:SS format (e.g., "09:00:00")

### **Voltage Columns (Primary Data)**
- `PHASE_A_INST._VOLTAGE (V)`: Phase A instantaneous voltage
- `PHASE_B_INST._VOLTAGE (V)`: Phase B instantaneous voltage  
- `PHASE_C_INST._VOLTAGE (V)`: Phase C instantaneous voltage

### **Additional Electrical Data**
- `PHASE_A_INST._CURRENT (A)`: Phase A current
- `PHASE_B_INST._CURRENT (A)`: Phase B current
- `PHASE_C_INST._CURRENT (A)`: Phase C current
- `POWER_FACTOR`: Power factor measurements
- `AVG._IMPORT_KW (kW)`: Average import power
- `AVG._EXPORT_KW (kW)`: Average export power

## 🚀 How the App Handles Your File

### **1. Automatic Format Detection**
- ✅ Recognizes your file as LOAD_PROFILE format
- ✅ Identifies the correct voltage column names
- ✅ Maps columns to internal processing names

### **2. Time Processing**
- ✅ Combines DATE + TIME columns automatically
- ✅ Creates proper datetime x-axis for graphs
- ✅ Handles YYYY-MM-DD HH:MM:SS format

### **3. Data Extraction**
- ✅ Extracts voltage data from all three phases
- ✅ Processes 2,813 rows efficiently
- ✅ Handles large datasets up to 100MB

### **4. Visualization**
- ✅ Generates time-series voltage graphs
- ✅ Shows all three phases with different colors
- ✅ Interactive zoom, pan, and hover features

## 📈 What You'll See

### **Graph Display**
- **X-Axis**: Time (combined from DATE + TIME)
- **Y-Axis**: Voltage in Volts
- **Three Lines**: Phase A (Blue), Phase B (Orange), Phase C (Green)
- **Data Points**: 2,813 voltage measurements over time

### **Statistics Dashboard**
- **Min/Max Voltage**: For each phase
- **Average Voltage**: Mean voltage per phase
- **Standard Deviation**: Voltage variation per phase

### **Interactive Features**
- **Phase Selection**: Show/hide individual phases
- **Zoom & Pan**: Explore specific time periods
- **Hover Information**: Exact voltage values at timestamps
- **Export Options**: Download graphs as PNG/JPEG

## 🎯 How to Use

### **Step 1: Start the Application**
```bash
python app.py
# or double-click run.bat
```

### **Step 2: Open Browser**
Navigate to: `http://localhost:5000`

### **Step 3: Upload Your File**
- Click "Choose CSV File"
- Select `LOAD_PROFILE_HISTORICAL_READINGS_INVENTORY_25_08_2025.csv`
- Click "Upload & Analyze"

### **Step 4: View Results**
- **Format Detected**: LOAD_PROFILE
- **File Info**: Shows rows, columns, and format type
- **Graph**: Interactive voltage vs. time visualization
- **Statistics**: Min, max, average for each phase

## 🔧 Technical Details

### **File Size Support**
- **Maximum**: 100MB (your file: 444KB ✅)
- **Rows**: Unlimited (your file: 2,813 rows ✅)
- **Columns**: Flexible (your file: 21 columns ✅)

### **Performance Optimizations**
- **Memory Efficient**: Handles large datasets
- **Fast Processing**: Optimized for electrical data
- **Responsive UI**: Works smoothly with thousands of points

### **Data Validation**
- **Column Detection**: Automatically finds voltage columns
- **Format Validation**: Ensures proper DATE/TIME format
- **Error Handling**: Clear messages for any issues

## 🎉 Benefits for Your Analysis

### **1. Complete Data Coverage**
- All 2,813 data points visualized
- 15-minute intervals preserved
- Multiple days of data in one view

### **2. Professional Visualizations**
- Publication-quality graphs
- Interactive exploration tools
- Export capabilities for reports

### **3. Statistical Insights**
- Voltage trends over time
- Phase-to-phase comparisons
- Anomaly detection through statistics

### **4. Easy Sharing**
- Download graphs as images
- Use in presentations and reports
- Share insights with colleagues

## 🚨 Troubleshooting

### **If Upload Fails**
1. **Check file size**: Must be under 100MB ✅
2. **Verify format**: Must be CSV ✅
3. **Check columns**: Must have voltage columns ✅

### **If Graph Doesn't Display**
1. **Check browser console** for errors
2. **Verify data format** in your CSV
3. **Ensure voltage columns** contain numerical data

### **For Large Files**
1. **Close other browser tabs** to free memory
2. **Wait for processing** - large files take time
3. **Check upload progress** in the interface

## 🎯 Ready to Analyze!

Your application is now **100% ready** to handle your LOAD_PROFILE file:

- ✅ **Format Supported**: LOAD_PROFILE with voltage columns
- ✅ **File Size**: Handles up to 100MB (your file: 444KB)
- ✅ **Data Processing**: 2,813 rows efficiently processed
- ✅ **Visualization**: Beautiful time-series graphs
- ✅ **Analysis**: Comprehensive statistics and insights

**Start analyzing your electrical data now!** ⚡📊

---

**Need help?** Check the main README.md or QUICK_START.md for additional guidance.
