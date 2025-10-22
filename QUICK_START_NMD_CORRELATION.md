# Quick Start Guide - NMD Analysis Feeder-Customer Correlation

## 🚀 Getting Started

This guide will help you quickly set up and use the NMD Analysis - Feeder-Customer Correlation feature.

## 📋 Prerequisites

- Backend server running on port 5000
- Frontend server running on port 3000
- CSV files with feeder and customer data

## 🏃‍♂️ Quick Setup

### 1. Start the Application
```bash
# Start backend
cd backend
python app.py

# Start frontend (in another terminal)
cd frontend
npm start
```

### 2. Access the Feature
1. Open your browser to `http://localhost:3000`
2. Navigate to "NMD Analysis" in the menu
3. Click on "Advanced NMD Analysis" tab

## 📊 Data Preparation

### Feeder Data Format
Your feeder CSV should have these columns:
```csv
DATE,TIME,PHASE_A_INST._VOLTAGE (V),PHASE_B_INST._VOLTAGE (V),PHASE_C_INST._VOLTAGE (V)
13/07/2025,04:00:00,228.4,236.8,0
13/07/2025,03:45:00,228.2,236.4,0
```

### Customer Data Format
Your customer CSV should have these columns:
```csv
DATE,TIME,PHASE_A_INST._VOLTAGE (V),PHASE_B_INST._VOLTAGE (V),PHASE_C_INST._VOLTAGE (V)
13/07/2025,04:00:00,230.1,235.2,0
13/07/2025,03:45:00,229.8,234.9,0
```

## 🔄 Step-by-Step Usage

### Step 1: Upload Feeder Data
1. Click "Upload Feeder NMD File"
2. Select your feeder CSV file
3. Wait for "✓ File uploaded" confirmation

### Step 2: Upload Customer Data
1. Click "Upload Customer Files"
2. Select multiple customer CSV files
3. Wait for "✓ X file(s) uploaded" confirmation

### Step 3: Run Analysis
1. Click "🔬 Perform Correlation Analysis"
2. Wait for analysis to complete
3. Review the results

### Step 4: View Results
- **Summary Statistics**: Average correlation and RMSE values
- **Assignment Table**: Customer-feeder assignments with quality scores
- **Feeder Grouping**: Customers grouped by assigned feeder

### Step 5: Generate Visualizations
1. Select a customer from the dropdown
2. Select a feeder (if multiple available)
3. Click "📈 Generate Visualization"
4. View the voltage correlation plots

## 📈 Understanding Results

### Correlation Strength
- **🟢 Strong (0.7-1.0)**: Very high correlation - likely correct assignment
- **🟡 Moderate (0.5-0.7)**: Good correlation - probable assignment
- **🔴 Weak (0.3-0.5)**: Low correlation - uncertain assignment
- **⚫ Very Weak (0.0-0.3)**: Minimal correlation - likely incorrect

### RMSE Values
- **< 10V**: Excellent match
- **10-20V**: Good match
- **20-50V**: Moderate match
- **> 50V**: Poor match

### Quality Indicators
- **Aligned Points**: Number of data points used for correlation
- **Time Window**: 15-minute alignment tolerance
- **Score**: Combined correlation and RMSE metric

## 🎯 Best Practices

### Data Quality
- Ensure consistent time intervals (15-minute recommended)
- Check for missing or invalid voltage readings
- Verify date/time format consistency
- Include sufficient data overlap (minimum 24 hours)

### Analysis Tips
- Start with high-quality, clean data
- Use multiple customers for better feeder identification
- Review low-correlation results carefully
- Cross-reference with known network topology

### Troubleshooting
- **No aligned data**: Check time ranges and formats
- **Low correlations**: Verify data quality and feeder assignment
- **Upload errors**: Check CSV format and file size
- **Analysis failures**: Ensure both feeder and customer data uploaded

## 📱 Interface Guide

### Upload Areas
- **Drag & Drop**: Drag files directly onto upload areas
- **File Selection**: Click to open file browser
- **Progress Indicators**: Shows upload status
- **Error Messages**: Clear feedback for issues

### Results Display
- **Color Coding**: Green (strong), Yellow (moderate), Red (weak)
- **Sortable Tables**: Click headers to sort
- **Responsive Design**: Works on all screen sizes
- **Export Ready**: Results can be copied or saved

### Visualizations
- **Interactive Charts**: Zoom, pan, hover for details
- **Time Series**: Shows voltage patterns over time
- **Scatter Plots**: Shows correlation relationships
- **Legend**: Identifies different data series

## 🔧 Advanced Features

### Multiple Feeders
- Upload multiple feeder files for comparison
- Select specific feeder for visualization
- Compare customer assignments across feeders

### Data Filtering
- Filter by date ranges (future feature)
- Filter by voltage ranges (future feature)
- Filter by correlation strength (future feature)

### Export Options
- Copy results to clipboard
- Save visualizations as images
- Export data as CSV (future feature)

## 🆘 Common Issues

### Upload Problems
- **File too large**: Reduce file size or split data
- **Invalid format**: Check column names and data types
- **Network timeout**: Check server connection

### Analysis Issues
- **No results**: Ensure data overlap and valid formats
- **Low quality**: Check data consistency and time alignment
- **Memory errors**: Reduce dataset size

### Visualization Problems
- **Charts not loading**: Refresh page and try again
- **Missing data**: Check customer/feeder selection
- **Performance issues**: Reduce data points or use sampling

## 📞 Support

### Getting Help
1. Check this guide for common solutions
2. Review error messages carefully
3. Verify data format requirements
4. Test with sample data first

### Sample Data
Use the provided sample CSV files in the `LECO/` directory for testing:
- `LOAD_PROFILE_HISTORICAL_READINGS_INVENTORY_*.csv` (feeder data)
- Individual customer CSV files (customer data)

### Performance Tips
- Use 15-minute intervals for best results
- Limit to 1-7 days of data for initial testing
- Process customers in batches of 10-20
- Monitor memory usage with large datasets

## 🎉 Success Indicators

You'll know the analysis is working correctly when:
- ✅ Files upload without errors
- ✅ Analysis completes with results
- ✅ Correlation values are reasonable (0.3-0.9)
- ✅ RMSE values are acceptable (< 50V)
- ✅ Visualizations show clear patterns
- ✅ Customer assignments make sense

## 🔄 Next Steps

After successful analysis:
1. Review and validate results
2. Export findings for reporting
3. Use insights for network planning
4. Schedule regular analysis updates
5. Integrate with other network tools

---

**Happy Analyzing! 🚀**

For detailed technical information, see `NMD_ANALYSIS_FEEDER_CUSTOMER_CORRELATION.md`
