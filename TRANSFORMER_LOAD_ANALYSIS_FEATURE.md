# Transformer Load Analysis Feature

## Overview
A comprehensive transformer load analysis feature has been successfully implemented in the Power Quality Analysis section. This feature analyzes transformer loading behavior and identifies overload conditions based on KVA and KW readings.

## Features Implemented

### 1. Data Input
- ✅ **File Upload**: Upload transformer load CSV files (e.g., AZ1303.csv)
- ✅ **Data Preview**: Display uploaded file in a paginated table format (10 rows per page)
- ✅ **Data Validation**: Automatic detection of KVA and KW columns
- ✅ **Capacity Input**: Input field for transformer rated capacity (kVA)

### 2. Data Processing and Analysis
- ✅ **Load Percentage Calculation**: `Load % = (KVA or KW / Rated Capacity) × 100`
- ✅ **Overload Detection**: Identify periods where Load % > 100%
- ✅ **Statistical Analysis**:
  - Maximum load (kVA/kW) and percentage
  - Average load (kVA/kW) and percentage
  - Minimum load (kVA/kW) and percentage
  - Total overload duration (hours)
  - Number of overload events
- ✅ **Overload Event Tracking**: Identifies consecutive overload periods with:
  - Start and end timestamps
  - Maximum load during event
  - Event duration

### 3. Visualization
- ✅ **KVA vs Time Graph**: Interactive Plotly chart showing KVA load over time
- ✅ **KW vs Time Graph**: Interactive Plotly chart showing KW load over time
- ✅ **Overload Highlighting**: Red markers/points for overload conditions
- ✅ **Capacity Line**: Dashed line showing rated capacity for reference
- ✅ **Interactive Features**: Hover tooltips, zoom, pan capabilities

### 4. Output Summary
- ✅ **Summary Statistics Display**:
  - Color-coded cards for max, avg, and min loads
  - Visual indicators for overload conditions (red/green)
  - Rated capacity and analysis period information
- ✅ **Overload Events Table**: Detailed table showing top overload events
- ✅ **Export Options**:
  - CSV export with complete analysis summary
  - PDF export with formatted report

## UI Design

### Layout
- **Collapsible Section**: Expandable/collapsible card titled "Transformer Load Analysis"
- **Description Panel**: Short explanation of the feature
- **Responsive Design**: Grid-based layout that adapts to screen size
- **Clear Labeling**: All data fields and axes clearly labeled

### Components
1. **Upload Area**: Drag-and-drop style file upload
2. **Data Preview Table**: Paginated table showing first 100 rows
3. **Analysis Input**: Capacity input field with validation
4. **Summary Cards**: Color-coded statistics cards
5. **Overload Events Table**: Detailed event listing
6. **Visualization Charts**: Interactive Plotly graphs
7. **Export Buttons**: CSV and PDF download options

## Technical Implementation

### Backend (Python/Flask)

#### New Endpoints:
1. `POST /api/transformer_load/upload`
   - Upload and validate transformer load CSV
   - Detect KVA and KW columns
   - Parse timestamps
   - Return preview data

2. `POST /api/transformer_load/analyze`
   - Process load data
   - Calculate load percentages
   - Identify overload events
   - Generate visualization data
   - Return comprehensive analysis

3. `POST /api/transformer_load/export_csv`
   - Export analysis summary as CSV
   - Include all statistics and overload events

4. `POST /api/transformer_load/export_pdf`
   - Generate formatted PDF report
   - Include tables and statistics
   - Professional layout with ReportLab

#### Key Functions:
- `generate_transformer_load_pdf()`: Creates comprehensive PDF reports
- Automatic time column parsing from DATE/TIME columns
- Overload event detection algorithm
- Load percentage calculations

### Frontend (React)

#### New State Variables:
- `transformerLoadFile`: Uploaded file
- `transformerLoadData`: Parsed CSV data
- `ratedCapacity`: User-entered capacity
- `loadAnalysis`: Analysis results
- `currentPage`: Table pagination
- `showTransformerLoad`: Section visibility

#### New Functions:
- `handleTransformerLoadUpload()`: File upload handler
- `handleAnalyzeTransformerLoad()`: Analysis trigger
- `handleExportLoadCsv()`: CSV export
- `handleExportLoadPdf()`: PDF export

#### New API Calls (services/api.js):
- `transformerLoadUpload()`
- `transformerLoadAnalyze()`
- `transformerLoadExportCsv()`
- `transformerLoadExportPdf()`

## Usage Instructions

### Step 1: Upload Transformer Load Data
1. Navigate to **Power Quality Analysis** page
2. Click to expand the **Transformer Load Analysis** section
3. Click the upload area to select a CSV file
4. Supported format: CSV with columns like:
   - `DATE`, `TIME`, `TIMESTAMP`
   - `AVG._IMPORT_KVA (kVA)`
   - `AVG._IMPORT_KW (kW)`

### Step 2: Preview Data
- View the first 100 rows in a paginated table
- Use Previous/Next buttons to navigate pages
- Verify KVA and KW columns are detected (✓ indicators)

### Step 3: Enter Transformer Capacity
- Input the transformer rated capacity in kVA
- Example: 500 kVA, 1000 kVA, etc.

### Step 4: Run Analysis
- Click **Analyze Load** button
- Wait for processing (indicated by spinner)
- View comprehensive results

### Step 5: Review Results
- **Summary Cards**: View max, avg, min loads with percentages
- **Overload Events**: Check if any overload conditions occurred
- **Event Details**: Review specific overload event timestamps and magnitudes
- **Visualizations**: Examine KVA and KW load profiles over time

### Step 6: Export Results
- **Export CSV**: Download detailed analysis in CSV format
- **Export PDF**: Generate professional PDF report

## Data Format Example

### Input CSV Format:
```csv
SERIAL,CUSTOMER_REF,DATE,TIME,AVG._IMPORT_KW (kW),AVG._IMPORT_KVA (kVA)
000020401123,073/AZ1303,2025-10-10,13:30:00,123.318,129.084
000020401123,073/AZ1303,2025-10-10,13:15:00,122.634,127.794
...
```

### Analysis Output:
- **KVA Analysis**: Max, Avg, Min loads with percentages
- **Overload Events**: List of events with timestamps and magnitudes
- **Duration**: Total hours in overload condition
- **Visualization Data**: Time series for graphing

## Color Coding

### Status Indicators:
- 🔴 **Red**: Overload condition (>100%)
- 🟢 **Green**: Normal operation (<100%)
- 🟠 **Orange**: Average load indicator
- 🔵 **Blue**: General information

### Chart Colors:
- **Blue Line**: KVA load profile
- **Green Line**: KW load profile
- **Red Dashed Line**: Rated capacity limit
- **Red Points**: Overload data points

## Files Modified

### Backend:
- `backend/app.py`: Added 4 new routes and PDF generation function

### Frontend:
- `frontend/src/services/api.js`: Added 4 new API functions
- `frontend/src/components/PowerQuality.js`: Added complete UI section

### Documentation:
- `TRANSFORMER_LOAD_ANALYSIS_FEATURE.md`: This file

## Benefits

1. **Proactive Maintenance**: Identify transformer overload conditions before failure
2. **Capacity Planning**: Understand actual load vs. rated capacity
3. **Load Profiling**: Visualize load patterns over time
4. **Compliance**: Document overload events for regulatory purposes
5. **Optimization**: Identify opportunities for load balancing
6. **Reporting**: Generate professional reports for stakeholders

## Future Enhancements (Optional)

- Real-time load monitoring
- Predictive overload warnings
- Load forecasting using historical data
- Multi-transformer comparison
- Custom overload thresholds
- Email alerts for overload events
- Integration with SCADA systems

## Testing

### Test with Sample Data:
1. Use provided file: `LECO/AZ1303.csv`
2. Set capacity: 150 kVA
3. Run analysis
4. Verify overload detection
5. Check visualizations
6. Export reports

### Expected Results:
- File should upload successfully
- Analysis should complete within seconds
- Overload events should be detected (if any)
- Charts should render with overload highlighting
- CSV/PDF exports should download properly

## Support

For issues or questions:
1. Check console for error messages
2. Verify CSV file format matches expected structure
3. Ensure rated capacity is a positive number
4. Check that KVA or KW columns exist in the CSV

## Success Criteria ✅

All requirements have been successfully implemented:
- ✅ File upload and data preview
- ✅ Transformer capacity input
- ✅ Load percentage calculation
- ✅ Overload detection (>100%)
- ✅ Statistical summary (max, avg, duration, count)
- ✅ KVA and KW visualizations
- ✅ Overload highlighting in charts
- ✅ CSV and PDF export
- ✅ Responsive UI design
- ✅ Collapsible section
- ✅ Clear labeling and descriptions

## Conclusion

The Transformer Load Analysis feature is now fully operational and integrated into the Power Quality Analysis section. Users can upload transformer load data, analyze overload conditions, visualize load profiles, and export comprehensive reports in both CSV and PDF formats.


