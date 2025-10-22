# Unified Power Quality & Transformer Load Analysis Report

## Overview

The Power Quality Analysis feature has been enhanced to generate **one comprehensive report** that combines voltage quality analysis with transformer load analysis. This unified approach streamlines the workflow and provides a complete picture of transformer performance.

## ✨ New Unified Workflow

### Step-by-Step Process

1. **Upload Feeder NMD** (Required)
   - Upload feeder network metering data CSV file
   - System automatically detects available feeders

2. **Upload Consumer Data** (Required)
   - Upload one or multiple consumer data CSV files
   - Select which feeders to analyze

3. **Upload Transformer Load Data** (Optional)
   - Upload transformer load CSV file with KVA and KW data
   - System detects KVA/KW columns automatically
   - Preview uploaded data

4. **Generate Comprehensive Report**
   - Enter Transformer Number (e.g., T-001)
   - Enter Transformer Capacity in kVA (required if transformer load file is uploaded)
   - Click "Generate Report" to create one unified report

## 📊 Report Contents

The comprehensive report includes:

### Voltage Quality Analysis
- **Overall Summary**: Standard limits (207-253V) and strict limits (216-244V) analysis
- **Feeder-wise Analysis**: Voltage quality metrics for each feeder
- **Consumer-wise Analysis**: Individual consumer voltage quality reports
- **Compliance Status**: Maintained/Not Maintained indicators

### Transformer Load Analysis (if data provided)
- **Capacity Summary**: Rated capacity and analysis period
- **KVA Analysis**:
  - Maximum, Average, and Minimum load
  - Load percentages
  - Overload events detection (>100%)
  - Overload duration and count
  - Detailed overload events table
- **KW Analysis**:
  - Maximum, Average, and Minimum load
  - Load percentages
  - Overload metrics

## 🎯 Key Features

### Single Report Generation
- One button generates a complete report
- Combines voltage quality and transformer load analysis
- Automatic integration when transformer data is available

### Smart Data Detection
- Automatically identifies KVA and KW columns
- Handles multiple date/time formats
- Flexible CSV structure support

### Comprehensive Export Options
- **JSON Export**: Full report data in JSON format
- **PDF Export**: Professional PDF report including both analyses

### Visual Indicators
- Color-coded load indicators (green for normal, red for overload)
- Real-time status updates
- Required field validation

## 🔧 Backend Implementation

### New API Enhancements

**Modified `/api/pq_generate_report` Endpoint**
```python
POST /api/pq_generate_report
{
  "session_id": "pq_session_xxx",
  "feeders_to_use": ["FEEDER_001"],
  "transformer_capacity": 500  // Optional - triggers transformer load analysis
}
```

**Response includes:**
- Voltage quality analysis (existing)
- `transformer_load_analysis` object (new) when capacity is provided

### Helper Functions

**`_analyze_transformer_load(df, kva_col, kw_col, rated_capacity)`**
- Performs comprehensive load analysis
- Calculates load percentages
- Identifies overload events
- Groups consecutive overloads into events
- Generates visualization data

**Enhanced PDF Generation**
- Updated `_generate_pq_pdf_report()` to include transformer load section
- Professional formatting with tables and color coding
- Overload events highlighted in reports

## 📁 File Structure

### Backend Files
- `backend/app.py`: Main API routes and analysis logic
  - `/api/transformer_load/upload`: Upload transformer load CSV
  - `/api/pq_generate_report`: Generate unified report (enhanced)
  - `/api/pq_download_pdf`: Download PDF with both analyses

### Frontend Files
- `frontend/src/components/PowerQuality.js`: Unified UI component
- `frontend/src/services/api.js`: API integration functions

## 🎨 UI Design

### Layout
- **Three-column upload section**: Feeder | Consumer | Transformer Load
- **Feeder selection**: Chip-based multi-select
- **Report generation**: Single form with transformer number and capacity
- **Results display**: Expandable sections for each analysis type

### Visual Enhancements
- Step numbers (1️⃣ 2️⃣ 3️⃣ 4️⃣) for clear workflow
- Optional indicator for transformer load upload
- Required field marker (*) when transformer capacity is mandatory
- Color-coded load statistics (red for overload, green for normal)

## 📝 Usage Example

```javascript
// 1. Upload feeder NMD file
// 2. Upload consumer files
// 3. Upload transformer load file (optional)
// 4. Enter transformer details:
//    - Number: T-001
//    - Capacity: 500 kVA
// 5. Click "Generate Report"
// 6. View comprehensive report with both analyses
// 7. Download as JSON or PDF
```

## 🔍 Overload Detection Algorithm

### Logic
1. Calculate load percentage: `(KVA or KW / Rated Capacity) × 100`
2. Identify records where load percentage > 100%
3. Group consecutive overload records into events
4. For each event, track:
   - Start and end time
   - Maximum load during event
   - Duration (number of records)

### Assumptions
- 15-minute interval between records (for duration calculation)
- Power factor ~1 for KW comparison (simplified)

## 📊 Example Report Output

```json
{
  "title": "Voltage Quality Analysis Report",
  "summary": {
    "overall_analysis": { /* voltage quality data */ }
  },
  "feeders": { /* feeder-wise analysis */ },
  "consumers": { /* consumer-wise analysis */ },
  "transformer_load_analysis": {
    "rated_capacity_kva": 500,
    "time_range": {
      "start": "2025-01-01 00:00:00",
      "end": "2025-01-31 23:45:00",
      "total_records": 2976
    },
    "kva_analysis": {
      "max_load_kva": 523.45,
      "max_load_pct": 104.69,
      "avg_load_kva": 425.32,
      "avg_load_pct": 85.06,
      "overload_count": 156,
      "overload_duration_hours": 39.0,
      "total_overload_events": 3,
      "overload_events": [
        {
          "start": "2025-01-15 18:00:00",
          "end": "2025-01-15 21:45:00",
          "max_load_kva": 523.45,
          "max_load_pct": 104.69,
          "duration_records": 16
        }
      ]
    },
    "kw_analysis": { /* similar structure */ }
  }
}
```

## 🚀 Benefits

1. **Streamlined Workflow**: One report instead of multiple separate analyses
2. **Complete Overview**: See both voltage quality and load performance together
3. **Time Savings**: Single upload and generation process
4. **Comprehensive PDF**: All data in one professional document
5. **Better Decision Making**: Correlated insights from combined data

## 🔒 Validation

- Required fields validation (feeder + consumer files)
- Conditional requirement (capacity needed if load file uploaded)
- CSV format validation
- Numeric input validation for capacity

## 📌 Notes

- Transformer load analysis is **optional** - report can be generated without it
- If transformer load file is uploaded, capacity becomes **required**
- All existing functionality (voltage quality analysis) remains unchanged
- Backward compatible with existing workflows

## 🎯 Future Enhancements

Potential additions:
- Real-time load monitoring
- Historical trend analysis
- Predictive overload warnings
- Load forecasting integration
- Custom capacity thresholds
- Multiple transformer comparison

---

**Created**: October 2025  
**Version**: 1.0  
**Status**: Production Ready ✅


