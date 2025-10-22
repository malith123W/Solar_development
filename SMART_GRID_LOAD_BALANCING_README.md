# Smart Load Balancing & Forecasting

## Overview

The Smart Load Balancing & Forecasting feature is a comprehensive module that enhances the Solar Development platform with advanced grid simulation, load balancing optimization, and AI/ML-based load forecasting capabilities.

## Core Features

### 1. Grid Modeling (GridLAB-D Integration)

**Purpose:** Automatically generate GridLAB-D `.glm` files from existing NMD and Customer CSV data.

**Capabilities:**
- Automatic generation of grid topology files (.glm)
- Definition of transformers, feeders, poles, and customer connections
- Phase-aware modeling based on NMD correlation analysis
- Configurable network parameters (voltage levels, line impedances, etc.)

**How it Works:**
1. Uses existing feeder-customer correlation data from NMD Analysis
2. Generates hierarchical grid structure: Transformer → Feeders → Phases → Poles → Customers
3. Assigns realistic electrical parameters based on typical distribution network values
4. Creates monitoring points for voltage and power measurements

**API Endpoint:** `POST /api/smart-grid/generate-glm`

**Example Request:**
```json
{
  "session_id": "your_session_id",
  "transformer_name": "T1",
  "model_name": "grid_model_2025"
}
```

**Example Response:**
```json
{
  "success": true,
  "glm_file": "gridlabd_models/grid_model_2025.glm",
  "message": "GLM file generated: gridlabd_models/grid_model_2025.glm",
  "transformer": "T1",
  "total_customers": 45
}
```

---

### 2. Load Flow Analysis (GridLAB-D Simulation)

**Purpose:** Run power flow simulations to analyze voltage profiles, transformer loading, and network losses.

**Capabilities:**
- Voltage profile calculation for all nodes
- Power loss calculation across feeders and phases
- Transformer loading analysis
- Identification of voltage violations and overloaded equipment

**Requirements:**
- GridLAB-D must be installed on the system
- Download from: https://www.gridlabd.org/

**API Endpoint:** `POST /api/smart-grid/run-simulation`

**Example Request:**
```json
{
  "glm_file": "gridlabd_models/grid_model_2025.glm"
}
```

**Example Response:**
```json
{
  "success": true,
  "results": {
    "transformer_power": [...],
    "meter_voltages": [...],
    "load_powers": [...]
  },
  "stdout": "GridLAB-D simulation output",
  "glm_file": "gridlabd_models/grid_model_2025.glm"
}
```

**Note:** If GridLAB-D is not installed, the response will include installation instructions.

---

### 3. Load Balancing

**Purpose:** Analyze phase imbalances and suggest customer reassignments to optimize load distribution.

#### 3.1 Balance Analysis

Analyzes current load distribution across phases for each feeder.

**Metrics:**
- Phase imbalance percentage
- Load distribution per phase
- Customer count per phase
- Voltage statistics

**Imbalance Calculation:**
```
Imbalance = max(|Load_phase - Avg_load|) / Avg_load
```

**API Endpoint:** `POST /api/smart-grid/analyze-balance`

**Example Response:**
```json
{
  "success": true,
  "analysis": {
    "feeder_analysis": {
      "FEEDER_001": {
        "phase_loads": [
          {
            "phase": "Phase A",
            "total_kw": 45.2,
            "total_kvar": 12.3,
            "customer_count": 8,
            "avg_voltage": 230.5
          },
          {
            "phase": "Phase B",
            "total_kw": 52.8,
            "total_kvar": 14.1,
            "customer_count": 10,
            "avg_voltage": 229.8
          },
          {
            "phase": "Phase C",
            "total_kw": 38.1,
            "total_kvar": 10.2,
            "customer_count": 7,
            "avg_voltage": 231.2
          }
        ],
        "imbalance_percentage": 16.5,
        "is_balanced": false,
        "total_load_kw": 136.1,
        "total_customers": 25
      }
    },
    "overall_stats": {
      "total_feeders": 3,
      "imbalanced_feeders": ["FEEDER_001"],
      "balanced_feeders": ["FEEDER_002", "FEEDER_003"]
    },
    "max_imbalance_threshold": 15.0
  }
}
```

#### 3.2 Balancing Suggestions

Provides intelligent suggestions for customer reassignments to achieve better balance.

**Algorithm:**
1. Identifies most and least loaded phases
2. Finds customers in overloaded phases
3. Calculates optimal moves to minimize imbalance
4. Estimates improvement for each suggestion

**API Endpoint:** `POST /api/smart-grid/suggest-balancing`

**Example Response:**
```json
{
  "success": true,
  "suggestions": {
    "suggestions": [
      {
        "customer_id": "CUSTOMER_12345",
        "feeder_id": "FEEDER_001",
        "from_phase": "Phase B",
        "to_phase": "Phase C",
        "customer_load_kw": 5.2,
        "reason": "Balance load distribution",
        "expected_improvement": {
          "imbalance_before": 0.165,
          "imbalance_after": 0.112,
          "imbalance_reduction": 0.053
        }
      }
    ],
    "total_suggestions": 5,
    "estimated_balanced_feeders": 2
  }
}
```

#### 3.3 Balancing Simulation

Simulates the effect of applying balancing moves before actual implementation.

**API Endpoint:** `POST /api/smart-grid/simulate-balancing`

**Example Response:**
```json
{
  "success": true,
  "simulation": {
    "before": {
      "avg_imbalance": 0.165,
      "total_load_kw": 450.2,
      "avg_voltage": 230.1
    },
    "after": {
      "avg_imbalance": 0.095,
      "total_load_kw": 450.2,
      "avg_voltage": 230.5
    },
    "improvements": {
      "imbalance_reduction": 0.07,
      "loss_reduction_percentage": 4.8,
      "voltage_improvement": 0.4
    },
    "moves_applied": 5
  }
}
```

---

### 4. Load Forecasting

**Purpose:** Predict future load demand using advanced AI/ML models.

#### 4.1 Available Models

##### ARIMA (AutoRegressive Integrated Moving Average)
- **Best for:** Stationary time series with clear trends
- **Parameters:** Auto-selected (p, d, q)
- **Pros:** Fast, interpretable, works well for short-term forecasting
- **Cons:** Struggles with complex seasonality

##### Prophet (Facebook Prophet)
- **Best for:** Time series with strong seasonal patterns
- **Features:** Automatically detects daily and weekly seasonality
- **Pros:** Handles missing data, robust to outliers, easy to use
- **Cons:** Requires more data than ARIMA

##### LSTM (Long Short-Term Memory)
- **Best for:** Complex patterns with long-term dependencies
- **Architecture:** 2-layer LSTM with dropout
- **Pros:** Captures complex non-linear patterns
- **Cons:** Requires more data and computation time

#### 4.2 Forecasting API

**API Endpoint:** `POST /api/smart-grid/forecast`

**Request Parameters:**
```json
{
  "session_id": "your_session_id",
  "model_type": "prophet",  // "arima", "prophet", or "lstm"
  "forecast_periods": 168,  // Number of periods (e.g., 168 hours = 1 week)
  "customer_id": "CUSTOMER_12345",  // OR
  "feeder_id": "FEEDER_001"  // For aggregate forecast
}
```

**Example Response:**
```json
{
  "success": true,
  "model_type": "Prophet",
  "forecast": {
    "timestamps": ["2025-10-14 00:00:00", "2025-10-14 01:00:00", ...],
    "values": [45.2, 46.1, 47.5, ...],
    "lower_bound": [42.1, 43.0, 44.3, ...],
    "upper_bound": [48.3, 49.2, 50.7, ...]
  },
  "metrics": {
    "mae": 2.34,
    "rmse": 3.12,
    "mape": 5.67
  },
  "historical": {
    "timestamps": [...],
    "values": [...],
    "fitted_values": [...]
  }
}
```

#### 4.3 Model Comparison

Compare all three models simultaneously to find the best performing model.

**API Endpoint:** `POST /api/smart-grid/compare-forecast-models`

**Example Response:**
```json
{
  "success": true,
  "comparison": {
    "models": {
      "arima": {
        "success": true,
        "metrics": {
          "mae": 2.45,
          "rmse": 3.21,
          "mape": 6.12
        }
      },
      "prophet": {
        "success": true,
        "metrics": {
          "mae": 2.34,
          "rmse": 3.12,
          "mape": 5.67
        }
      },
      "lstm": {
        "success": true,
        "metrics": {
          "mae": 2.51,
          "rmse": 3.28,
          "mape": 6.28
        }
      }
    },
    "best_model": "prophet",
    "best_mape": 5.67
  },
  "customer_id": "CUSTOMER_12345"
}
```

---

## Installation & Setup

### Backend Dependencies

Install Python dependencies:

```bash
cd backend
pip install -r requirements.txt
```

The updated `requirements.txt` includes:
- `statsmodels>=0.14.0` - For ARIMA
- `prophet>=1.1.5` - For Prophet forecasting
- `tensorflow>=2.15.0` - For LSTM neural networks

### GridLAB-D Installation

**Note:** GridLAB-D is optional but required for full simulation functionality.

#### Windows:
1. Download from https://www.gridlabd.org/
2. Follow installation instructions
3. Add GridLAB-D to system PATH

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get install gridlabd
```

#### macOS:
```bash
brew install gridlabd
```

### Frontend Dependencies

The frontend uses `react-plotly.js` for charting (already included in existing dependencies).

---

## Usage Workflow

### Complete Workflow Example

1. **Upload and Analyze Data** (NMD Analysis section)
   - Upload Feeder NMD CSV
   - Upload Customer CSV files
   - Run correlation analysis

2. **Generate Grid Model**
   - Navigate to Smart Grid section
   - Click "Generate GLM File"
   - Review generated model details

3. **Run Simulation** (Optional, requires GridLAB-D)
   - Click "Run Simulation"
   - Review voltage profiles and losses

4. **Analyze Load Balance**
   - Click "Analyze Balance"
   - Review phase imbalance metrics
   - Identify problematic feeders

5. **Get Balancing Suggestions**
   - Click "Get Balancing Suggestions"
   - Review suggested customer reassignments
   - Click "Simulate Balancing" to see expected improvements

6. **Forecast Future Loads**
   - Go to Forecasting tab
   - Select model type (ARIMA, Prophet, or LSTM)
   - Enter customer ID or feeder ID
   - Set forecast periods (e.g., 168 for 1 week hourly)
   - Click "Run Forecast"
   - Review forecast charts and metrics

7. **Compare Models** (Optional)
   - Click "Compare Models"
   - Review which model performs best for your data

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/smart-grid/generate-glm` | POST | Generate GridLAB-D .glm file |
| `/api/smart-grid/run-simulation` | POST | Run GridLAB-D simulation |
| `/api/smart-grid/analyze-balance` | POST | Analyze load balance |
| `/api/smart-grid/suggest-balancing` | POST | Get balancing suggestions |
| `/api/smart-grid/simulate-balancing` | POST | Simulate balancing effects |
| `/api/smart-grid/forecast` | POST | Run load forecast |
| `/api/smart-grid/compare-forecast-models` | POST | Compare all models |
| `/api/smart-grid/dashboard-data` | GET | Get dashboard summary |

---

## Technical Details

### Load Balancing Algorithm

The load balancing algorithm uses a greedy approach:

1. Calculate phase loads for each feeder
2. Compute imbalance: `max(|Load_i - Avg|) / Avg`
3. For imbalanced feeders:
   - Find most loaded and least loaded phases
   - Select customers from overloaded phase
   - Calculate optimal moves that minimize imbalance
4. Score each move: `Score = |r| - 0.5 × RMSE_norm`
5. Sort suggestions by expected improvement

### Loss Estimation

Power losses are estimated using:

```
Loss = I² × R
```

Where:
- `I = P / V` (current)
- `R` = feeder resistance (configurable)
- Loss percentage = `Total_Loss / Total_Load × 100`

### Forecast Metrics

- **MAE (Mean Absolute Error):** Average absolute difference between predictions and actual values
- **RMSE (Root Mean Squared Error):** Square root of average squared differences
- **MAPE (Mean Absolute Percentage Error):** Average percentage error

Lower values indicate better performance.

---

## File Structure

```
backend/
├── gridlabd_integration.py    # GridLAB-D .glm generation and simulation
├── load_balancing.py           # Load balancing algorithms
├── load_forecasting.py         # ARIMA, Prophet, LSTM forecasting
├── app.py                      # API endpoints (updated)
└── requirements.txt            # Dependencies (updated)

frontend/
└── src/
    └── components/
        └── SmartGrid.js        # Smart Grid dashboard component

gridlabd_models/                # Generated .glm files (created automatically)
```

---

## Troubleshooting

### GridLAB-D Not Found

**Error:** `GridLAB-D not installed or not in PATH`

**Solution:**
1. Install GridLAB-D from https://www.gridlabd.org/
2. Add to system PATH
3. Verify installation: `gridlabd --version`

**Alternative:** The system can still generate .glm files without GridLAB-D. You can run simulations externally.

### Prophet Installation Issues

**Error:** `Prophet not installed`

**Solution:**
```bash
# On Windows, install C++ compiler first:
pip install prophet

# On Linux/macOS:
conda install -c conda-forge prophet
# OR
pip install prophet
```

### TensorFlow Installation Issues

**Error:** `TensorFlow not installed`

**Solution:**
```bash
# CPU-only version (recommended for most users):
pip install tensorflow

# GPU version (if you have CUDA):
pip install tensorflow-gpu
```

### Insufficient Data for Forecasting

**Error:** `Insufficient data points (need at least 50)`

**Solution:**
- Ensure your CSV files have sufficient historical data
- ARIMA requires minimum 50 data points
- Prophet and LSTM work better with 100+ data points
- For hourly data, this means at least 2-3 days of history

---

## Performance Considerations

### Memory Usage

- **LSTM Training:** Can use significant memory for large datasets
- **Recommendation:** For datasets > 10,000 points, consider data sampling

### Processing Time

- **ARIMA:** ~1-5 seconds
- **Prophet:** ~5-30 seconds
- **LSTM:** ~30-120 seconds (depends on epochs and data size)
- **GridLAB-D Simulation:** ~5-60 seconds (depends on model size)

### Optimization Tips

1. **Forecasting:**
   - Start with Prophet for best balance of speed and accuracy
   - Use ARIMA for quick short-term forecasts
   - Use LSTM when you have lots of data and need high accuracy

2. **Load Balancing:**
   - Run analysis periodically, not in real-time
   - Apply suggestions in batches
   - Validate suggestions before implementation

3. **GridLAB-D:**
   - Simplify grid model for faster simulation
   - Use representative loads instead of individual customer loads
   - Run simulations during off-peak hours

---

## Future Enhancements

Potential future features:

1. **Real-time Monitoring Integration**
   - Live data feeds from SCADA systems
   - Real-time imbalance alerts

2. **Advanced Optimization**
   - Multi-objective optimization (losses, voltage, reliability)
   - Genetic algorithms for optimal reconfiguration

3. **Machine Learning Improvements**
   - Ensemble forecasting (combine multiple models)
   - Deep learning models (GRU, Transformer)
   - Transfer learning from similar networks

4. **Visualization Enhancements**
   - Interactive grid topology maps
   - 3D power flow visualization
   - Animated forecast scenarios

5. **Integration Features**
   - Export balancing suggestions to field work orders
   - Integration with GIS systems
   - Automatic report generation

---

## Support

For issues or questions:
1. Check this README
2. Review API endpoint documentation
3. Check error messages for specific guidance
4. Review example workflows in the frontend

---

## License

Part of the Solar Development Platform.

---

## Changelog

### Version 1.0.0 (October 2025)
- Initial release
- GridLAB-D integration
- Load balancing analysis and suggestions
- ARIMA, Prophet, and LSTM forecasting
- Interactive dashboard

