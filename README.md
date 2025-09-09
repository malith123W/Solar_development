# ⚡ Electrical Data Analyzer

A modern web application for analyzing CSV electrical data with interactive visualizations. Built with Flask (Python) and Plotly for the frontend.

## 🚀 Features

- **File Upload**: Drag & drop or click to upload CSV files (up to 100MB)
- **Interactive Graphs**: Time vs. voltage/current/power-factor plots using Plotly
- **Parameter Selection**: Voltage, Current, Power Factor
- **Time Filtering**: Pick a start/end datetime to filter graphs and stats
- **NMD Analysis**: Upload NMD CSV, select CUSTOMER_REF, view 3-phase voltages
- **Real-time Updates**: Update graphs dynamically based on phase selection
- **Data Statistics**: View min, max, average, and standard deviation for each phase
- **Export Options**: Download graphs as PNG or JPEG images
- **Responsive Design**: Works on desktop and mobile devices
- **Hover Information**: See exact voltage values at specific timestamps
- **Multiple Format Support**: Handles both new and legacy CSV formats
- **Large File Support**: Optimized for files with thousands of data points

## 📋 Requirements

- Python 3.7+
- Flask
- Pandas
- Plotly
- Kaleido (for image export)

## 🛠️ Installation

1. **Clone or download** this repository to your local machine

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

## 📁 CSV File Format

The application supports **three CSV formats**:

### 🆕 **LOAD_PROFILE Format (Your File - Recommended)**
Your CSV file must contain the following columns:
- `DATE`: Date in YYYY-MM-DD format (e.g., "2025-06-30")
- `TIME`: Time in HH:MM:SS format (e.g., "09:00:00")
- `PHASE_A_INST._VOLTAGE (V)`: Instantaneous voltage values for Phase A
- `PHASE_B_INST._VOLTAGE (V)`: Instantaneous voltage values for Phase B  
- `PHASE_C_INST._VOLTAGE (V)`: Instantaneous voltage values for Phase C

**Note**: DATE and TIME columns are automatically combined to create the x-axis timestamp.

### 🔄 **New Format**
Your CSV file must contain the following columns:
- `DATE`: Date in DD/MM/YYYY format (e.g., "30/06/2025")
- `TIME`: Time in HH:MM:SS format (e.g., "09:00:00")
- `PHASE_A_INST`: Voltage values for Phase A
- `PHASE_B_`: Voltage values for Phase B  
- `PHASE_C_`: Voltage values for Phase C

### 🔄 **Legacy Format**
Your CSV file must contain the following columns:
- `time`: Timestamp in any readable format (e.g., "2024-01-01 00:00:00")
- `Phase_A`: Voltage values for Phase A
- `Phase_B`: Voltage values for Phase B  
- `Phase_C`: Voltage values for Phase C

### Example CSV Structure (LOAD_PROFILE Format):
```csv
SERIAL,CUSTOMER_REF,TIMESTAMP,OBIS,DATE,TIME,PHASE_A_INST._VOLTAGE (V),PHASE_B_INST._VOLTAGE (V),PHASE_C_INST._VOLTAGE (V)
000021301403,0701379602,1.75125E+12,LP,2025-06-30,09:00:00,221.3,240.3,235.7001
000021301403,0701379602,1.75125E+12,LP,2025-06-30,08:45:00,215.8,230.5,225.2001
000021301403,0701379602,1.75125E+12,LP,2025-06-30,08:30:00,212.8,236.1001,233.2001
...
```

### Example CSV Structure (New Format):
```csv
SERIAL,DATE,TIME,PHASE_A_INST,PHASE_B_,PHASE_C_
21301403,30/06/2025,09:00:00,221.3,240.3,235.7001
21301403,30/06/2025,08:45:00,215.8,230.5,225.2001
21301403,30/06/2025,08:30:00,212.8,236.1001,233.2001
...
```

### Example CSV Structure (Legacy Format):
```csv
time,Phase_A,Phase_B,Phase_C
2024-01-01 00:00:00,120.5,121.2,119.8
2024-01-01 00:00:01,120.8,121.5,120.1
2024-01-01 00:00:02,121.2,121.8,120.5
...
```

## 🎯 Usage

### 1. Upload Data
- Click "Choose CSV File" or drag & drop your CSV file
- The application automatically detects the format
- Click "Upload & Analyze" to process the data

### 2. View Graph
- The application automatically displays all three phases
- Use the phase checkboxes to show/hide specific phases
- Hover over the graph to see exact values

### 2b. NMD Analysis
- Click "Go to NMD Analysis" or open `/nmd`
- Upload an NMD CSV containing `DATE`, `TIME`, `CUSTOMER_REF`, and three voltage columns
- Select a `CUSTOMER_REF` from the dropdown to filter data for that customer
- Optionally set a start/end datetime and click "Update Graph"
- The app renders an interactive three-phase voltage vs time chart

### 3. Customize Display
- Select which phases to display using the checkboxes
- Click "Update Graph" to apply changes
- View statistics for each phase below the graph

### 4. Export Graphs
- Click "Download PNG" for PNG format
- Click "Download JPEG" for JPEG format
- Images include only the currently selected phases

## 🔧 Configuration

### File Size Limits
- Maximum file size: 100MB (configurable in `app.py`)
- Supported formats: CSV only
- Optimized for large datasets with thousands of rows

### Server Settings
- Host: 0.0.0.0 (accessible from any IP)
- Port: 5000
- Debug mode: Enabled (for development)

## 🏗️ Project Structure

```
electrical-data-analyzer/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── templates/
│   └── index.html             # Frontend HTML template
│   └── nmd_analysis.html      # NMD analysis page (upload + customer graph)
├── uploads/                   # Upload directory (auto-created)
└── README.md                  # This file
```

## 🚀 Advanced Features

### Session Management
- Each upload creates a unique session
- Data is stored in memory for the session duration
- Multiple users can upload different files simultaneously

### Graph Customization
- Interactive Plotly charts with zoom, pan, and hover
- Responsive design that adapts to screen size
- Professional color scheme for different phases

### Error Handling
- Comprehensive error messages for file validation
- Graceful handling of malformed CSV files
- User-friendly feedback for all operations

### Format Detection
- Automatically detects CSV format (LOAD_PROFILE vs. new vs. legacy)
- Combines DATE and TIME columns for new format
- Maintains backward compatibility

### Large File Support
- Optimized for files with thousands of data points
- Efficient memory management
- Fast processing and visualization

## 🐛 Troubleshooting

### Common Issues

1. **"No file uploaded" error**
   - Ensure you've selected a file before clicking upload
   - Check that the file is a valid CSV

2. **"CSV must contain voltage columns" error**
   - Verify your CSV has the required voltage columns
   - Check for typos in column names
   - Ensure DATE and TIME columns exist for new format

3. **Graph not displaying**
   - Ensure your CSV contains valid numerical data
   - Check browser console for JavaScript errors
   - Verify DATE and TIME format (YYYY-MM-DD HH:MM:SS for LOAD_PROFILE)

4. **Download not working**
   - Make sure at least one phase is selected
   - Check browser download settings

5. **Large file upload issues**
   - Ensure file size is under 100MB
   - Check your internet connection
   - Try uploading during off-peak hours

### Performance Tips

- For very large datasets (>50,000 rows), consider downsampling
- Close other browser tabs to free up memory
- Use PNG format for better quality, JPEG for smaller file sizes
- The application is optimized for files up to 100MB

## 🔒 Security Notes

- This is a development application
- File uploads are not validated for malicious content
- Session data is stored in memory (not persistent)
- For production use, implement proper security measures

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this application.

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Verify your CSV format matches one of the supported formats
3. Ensure all dependencies are properly installed
4. Check the browser console for error messages
5. For large files, ensure they're under 100MB

---

**Happy Analyzing! ⚡📊**
