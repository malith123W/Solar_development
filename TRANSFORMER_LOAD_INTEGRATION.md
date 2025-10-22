# Transformer Load Data Integration - Smart Load Balancing & Forecasting

## Overview

This update adds comprehensive transformer load data analysis and forecasting capabilities to the Smart Load Balancing & Forecasting section. The system now accepts transformer load data (e.g., AZ0621.csv files) and uses it for advanced analysis and predictive modeling.

---

## What Was Added

### 1. Backend Module Updates

#### `backend/load_balancing.py`
- **Updated `analyze_current_balance()` method**: Now accepts optional `transformer_data` parameter
- **Added `_analyze_transformer_load()` method**: Comprehensive analysis including:
  - Phase current analysis (Phase A, B, C)
  - Current imbalance calculation
  - Voltage statistics per phase
  - Voltage imbalance calculation
  - Active power (kW) and apparent power (kVA) statistics
  - Power factor analysis
  - Transformer utilization calculation (peak load vs capacity)

#### `backend/load_forecasting.py`
- **Added `forecast_transformer_load()` method**: Forecasts transformer load using historical data
  - Supports ARIMA, Prophet, and LSTM models
  - Automatically prepares transformer data for forecasting
  - Handles datetime conversion from DATE/TIME columns
- **Added `_prepare_transformer_data_for_forecast()` helper**: Processes transformer CSV data for forecasting models

#### `backend/app.py` - New API Endpoints
1. **`POST /api/smart-grid/upload-transformer`**
   - Upload transformer load CSV files
   - Validates data format (requires kW, voltage, or current columns)
   - Stores data in session for analysis
   - Returns basic statistics

2. **Updated `POST /api/smart-grid/analyze-balance`**
   - Now includes transformer data analysis in results
   - Transformer analysis appears in `overall_stats.transformer_analysis`

3. **Updated `POST /api/smart-grid/forecast`**
   - Added `use_transformer` parameter
   - Enables transformer load forecasting when set to `true`
   - Works independently of customer/feeder forecasting

4. **Updated `GET /api/smart-grid/dashboard-data`**
   - Returns `has_transformer_data` flag
   - Includes `transformer_summary` with file info

---

### 2. Frontend Updates

#### `frontend/src/components/SmartGrid.js`

**New State Variables:**
- `transformerFile`: Stores uploaded transformer file
- `transformerInputRef`: Reference for file input
- `use_transformer`: Flag in forecast settings

**New UI Components:**

1. **Transformer Upload Section** (Step 1)
   - Optional upload area for transformer data
   - Distinctive blue styling to indicate optional nature
   - File name display upon successful upload

2. **Transformer Forecasting Option** (Step 4)
   - Checkbox to enable transformer load forecasting
   - Only appears when transformer data is uploaded
   - Automatically disables customer/feeder ID inputs when selected
   - Clear visual indication with blue theme

3. **Transformer Analysis Display** (Step 3 - Balance Analysis)
   - **Phase Current Analysis**
     - Average, max, min current for each phase
     - Current imbalance percentage with color coding
   - **Load Statistics**
     - Active Power (kW): avg, max, min
     - Apparent Power (kVA): avg, max, min
   - **Transformer Utilization**
     - Capacity, peak load, utilization percentage
     - Color-coded utilization (green < 80%, red ≥ 80%)
     - Available capacity
   - **Power Factor**
     - Average power factor
     - Min-max range

**New Functions:**
- `handleTransformerUpload()`: Handles transformer file upload
- Updated `runForecast()`: Supports transformer forecasting

---

## How to Use

### Step 1: Upload Transformer Data

1. Navigate to "Smart Load Balancing & Forecasting"
2. In Step 1, scroll to the optional "Upload Transformer Data" section
3. Click the upload area and select a transformer CSV file (e.g., AZ0621.csv)
4. The system validates the file has required columns (kW, voltage, or current)
5. Success message confirms upload

### Step 2: Analyze Load Balance with Transformer Data

1. Upload feeder NMD and customer data as usual
2. Click "Analyze Data"
3. Navigate to Step 3: Load Balancing
4. Click "Analyze Balance"
5. **New**: If transformer data was uploaded, see "⚡ Transformer Load Analysis" section
6. Review:
   - Phase current distribution and imbalance
   - Load statistics (kW and kVA)
   - Transformer utilization percentage
   - Power factor metrics

### Step 3: Forecast Transformer Load

1. Navigate to Step 4: Load Forecasting
2. **New**: Check the "⚡ Use Transformer Load Data for Forecasting" checkbox
   - This option only appears if transformer data is uploaded
   - Customer ID and Feeder ID inputs are disabled when selected
3. Select forecasting model (ARIMA, Prophet, or LSTM)
4. Set forecast periods (default: 168 hours = 1 week)
5. Click "Run Forecast"
6. View forecast results including:
   - Predicted transformer load
   - Confidence intervals
   - Model metrics (MAE, RMSE, MAPE)

---

## Data Format Requirements

### Transformer CSV Format

The transformer CSV file should contain:

**Required Columns (at least one):**
- Load data: `AVG._IMPORT_KW (kW)` or similar kW column
- Voltage data: `PHASE_A_INST._VOLTAGE`, `PHASE_B_INST._VOLTAGE`, `PHASE_C_INST._VOLTAGE`
- Current data: `PHASE_A_INST._CURRENT`, `PHASE_B_INST._CURRENT`, `PHASE_C_INST._CURRENT`

**Optional but Recommended:**
- `AVG._IMPORT_KVA (kVA)`: Apparent power
- `INST._POWER_FACTOR`: Power factor
- `DATE` and `TIME`: Timestamp columns

**Example (AZ0621.csv format):**
```csv
SERIAL,CUSTOMER_REF,TIMESTAMP,DATE,TIME,AVG._IMPORT_KW (kW),AVG._IMPORT_KVA (kVA),PHASE_A_INST._CURRENT (A),PHASE_B_INST._CURRENT (A),PHASE_C_INST._CURRENT (A),PHASE_A_INST._VOLTAGE (V),PHASE_B_INST._VOLTAGE (V),PHASE_C_INST._VOLTAGE (V),INST._POWER_FACTOR
000023400476,071/AZ0621,1.75231E+12,2025-07-12,13:30:00,32.15,50.51,77.9,112.4,94,237.47,236.45,236.62,0.85
...
```

---

## Benefits

### 1. Comprehensive Analysis
- **Full transformer visibility**: Understand actual transformer loading patterns
- **Phase imbalance detection**: Identify unbalanced phases at the transformer level
- **Utilization monitoring**: Track transformer capacity usage to prevent overloading
- **Power quality insights**: Monitor power factor and voltage stability

### 2. Enhanced Forecasting
- **Direct transformer forecasting**: Predict future transformer load without aggregating customer data
- **Better accuracy**: Use actual transformer measurements instead of estimated loads
- **Capacity planning**: Forecast when transformer capacity limits will be reached

### 3. Integration with Existing Features
- **Works alongside customer/feeder analysis**: Doesn't replace existing functionality
- **Optional enhancement**: System works fully without transformer data
- **Consistent UI/UX**: Follows existing design patterns and workflows

---

## Technical Details

### Transformer Analysis Metrics

1. **Current Imbalance**
   ```
   Imbalance = (Max Phase Current - Avg Current) / Avg Current × 100%
   ```
   - Threshold: > 15% indicates significant imbalance

2. **Voltage Imbalance**
   ```
   Imbalance = (Max Phase Voltage - Avg Voltage) / Avg Voltage × 100%
   ```

3. **Transformer Utilization**
   ```
   Utilization = (Peak Load kVA / Transformer Capacity kVA) × 100%
   ```
   - Default capacity: 100 kVA (configurable)
   - Warning threshold: > 80%

### Forecasting Models

All three AI/ML models support transformer data:

1. **ARIMA**: Best for short-term forecasts with stable patterns
2. **Prophet**: Handles seasonality and trends well
3. **LSTM**: Deep learning for complex patterns

---

## API Reference

### Upload Transformer Data
```http
POST /api/smart-grid/upload-transformer
Content-Type: multipart/form-data

Parameters:
  - file: CSV file
  - session_id: Session identifier

Response:
{
  "success": true,
  "filename": "AZ0621.csv",
  "row_count": 3977,
  "columns": [...],
  "statistics": {
    "load": {
      "avg_kw": 85.43,
      "max_kw": 145.35,
      "min_kw": 0.0
    }
  }
}
```

### Forecast Transformer Load
```http
POST /api/smart-grid/forecast
Content-Type: application/json

{
  "session_id": "smart_grid_123",
  "model_type": "prophet",
  "forecast_periods": 168,
  "use_transformer": true
}

Response:
{
  "success": true,
  "model_type": "Prophet",
  "source": "transformer",
  "forecast": {
    "timestamps": [...],
    "values": [...],
    "lower_bound": [...],
    "upper_bound": [...]
  },
  "metrics": {
    "mae": 5.23,
    "rmse": 7.14,
    "mape": 6.8
  }
}
```

---

## Files Modified

### Backend
- `backend/load_balancing.py` (+147 lines)
- `backend/load_forecasting.py` (+85 lines)
- `backend/app.py` (+88 lines)

### Frontend
- `frontend/src/components/SmartGrid.js` (+120 lines)

### Documentation
- `TRANSFORMER_LOAD_INTEGRATION.md` (this file)

---

## Future Enhancements

Potential improvements for future versions:

1. **Configurable transformer capacity**: Allow users to specify transformer rating
2. **Historical trends**: Show transformer load trends over time
3. **Alarm thresholds**: Customizable warning levels for utilization and imbalance
4. **Multiple transformers**: Support analysis of multiple transformers simultaneously
5. **Comparison view**: Compare forecasted vs actual transformer loads
6. **Export reports**: Generate PDF reports with transformer analysis

---

## Testing

### Test with Sample Data

Use the provided transformer data file:
```
LECO/AZ0621.csv
```

This file contains:
- 3,977 records
- Date range: Multiple days of data
- All required columns for full analysis
- Realistic load patterns for testing

### Test Scenarios

1. **Upload Only**: Upload transformer data and verify statistics
2. **Analysis with Transformer**: Upload all data and run balance analysis
3. **Forecasting**: Test all three models (ARIMA, Prophet, LSTM)
4. **Mixed Analysis**: Use both customer and transformer data simultaneously

---

## Support

For questions or issues related to transformer load analysis:
1. Check that CSV file has required columns
2. Verify DATE and TIME columns for forecasting
3. Ensure data has sufficient historical records (50+ for forecasting)
4. Check browser console for detailed error messages

---

## Summary

The transformer load data integration enhances the Smart Load Balancing & Forecasting system with:
- ✅ Transformer-level load analysis
- ✅ Phase imbalance detection
- ✅ Utilization monitoring
- ✅ AI/ML-based transformer load forecasting
- ✅ Seamless integration with existing features
- ✅ Optional, non-breaking enhancement

This addition provides comprehensive insights into transformer performance and enables proactive capacity planning and load management.

