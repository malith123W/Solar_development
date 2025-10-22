# Voltage Graphs in Transformer Load Analysis

## ✅ Feature Complete

Voltage analysis graphs have been successfully integrated into the Power Quality & Transformer Load Analysis report!

---

## 📊 New Voltage Graphs Added

### 1. **Voltage Profile Over Time** ⚡
**Purpose:** Shows how voltage varies throughout the analysis period

**Features:**
- Purple line: Actual voltage measurements
- Red dashed line: Over-voltage limit (253V or 440V)
- Orange dashed line: Under-voltage limit (207V or 360V)
- Green dotted line: Nominal voltage (230V or 400V)
- Auto-detection of single-phase (230V) vs three-phase (400V)

**Insights:**
- Identify when voltage exceeds safe limits
- Spot voltage sags and swells
- Correlate voltage issues with time of day
- See voltage stability over time

**Color Coding:**
- 🔴 **Red Zone**: Over-voltage (>253V or >440V)
- 🟠 **Orange Zone**: Under-voltage (<207V or <360V)
- 🟢 **Green Zone**: Normal voltage (within limits)

---

### 2. **Voltage vs Load Correlation Scatter Plot** 📈
**Purpose:** Shows relationship between transformer load and voltage

**Features:**
- Each point represents one measurement
- X-axis: Transformer Load (kVA)
- Y-axis: Voltage (V)
- Color-coded points:
  - Green: Normal voltage
  - Orange: Under-voltage
  - Red: Over-voltage

**Critical Insights:**
- **Voltage drop under high load**: If points are orange/red at high kVA → cable/transformer undersized
- **Voltage rise at low load**: If voltage rises when load decreases → tap setting issue
- **Consistent over-voltage**: Points always red → upstream voltage regulation problem
- **Voltage instability**: Scattered colors → power quality issues

**Use Cases:**
- Detect voltage regulation problems
- Identify cable voltage drop issues
- Assess transformer tap setting adequacy
- Plan voltage stabilization measures

---

## 📊 Voltage Quality Statistics

New statistics section displays:

| Metric | Description | Color |
|--------|-------------|-------|
| **Nominal Voltage** | Expected standard voltage (230V or 400V) | Purple |
| **Average Voltage** | Mean voltage during analysis period | Green |
| **Over Voltage Limit** | Maximum acceptable voltage (+10%) | Red |
| **Under Voltage Limit** | Minimum acceptable voltage (-10%) | Orange |

**Per-Phase Analysis** (if multi-phase):
- Average, Max, Min voltage per phase
- % of time within limits
- % of time over-voltage
- % of time under-voltage

---

## 🔧 Technical Implementation

### Backend Changes

**1. Voltage Column Detection** (`app.py`)
```python
# Auto-detects voltage columns:
- VOLTAGE, V_L1, V_L2, V_L3, VL1, VL2, VL3
- Excludes: MAX, MIN, THD, UNBALANCE, KV
```

**2. Voltage Analysis Function**
```python
def _analyze_transformer_load(df, kva_col, kw_col, rated_capacity, voltage_cols):
    # Auto-detects nominal voltage (230V or 400V)
    # Calculates over/under voltage limits (±10%)
    # Analyzes each voltage phase
    # Creates correlation data with load
```

**3. Data Structure**
```json
{
  "voltage_analysis": {
    "nominal_voltage": 230,
    "over_voltage_limit": 253,
    "under_voltage_limit": 207,
    "average_voltage": 228.5,
    "voltage_columns": {
      "V_L1": {
        "avg": 229.3,
        "max": 245.2,
        "min": 215.8,
        "over_voltage_pct": 2.5,
        "under_voltage_pct": 1.2,
        "within_pct": 96.3
      }
    }
  },
  "visualization_data": {
    "voltage": {
      "time": [...],
      "voltage": [...],
      "over_limit": [253, 253, ...],
      "under_limit": [207, 207, ...],
      "nominal": [230, 230, ...],
      "kva_for_correlation": [...]
    }
  }
}
```

---

## 📄 PDF Report Integration

The voltage analysis is **automatically included** in the PDF report:

### New PDF Sections:
1. **Voltage Quality Analysis** (new page)
   - Voltage summary table
   - Nominal, average, over/under limits
   
2. **Voltage Phase Analysis** (if multi-phase)
   - Separate table for each phase
   - Detailed statistics per phase
   - Compliance percentages

**Example PDF Content:**
```
Voltage Quality Analysis
------------------------
Parameter              | Value
----------------------|--------
Nominal Voltage       | 230 V
Average Voltage       | 228.45 V
Over Voltage Limit    | 253 V
Under Voltage Limit   | 207 V

Voltage Phase Analysis
----------------------
Phase: V_L1
Average Voltage: 229.30 V
Maximum Voltage: 245.20 V
Minimum Voltage: 215.80 V
Within Limits: 96.30%
Over Voltage: 2.50%
Under Voltage: 1.20%
```

---

## 🎯 Practical Use Cases

### **Use Case 1: Voltage Drop Investigation**
**Scenario:** Customers complain of low voltage during evening peak

**Analysis:**
1. Check **Voltage Profile Over Time** → Low voltage 18:00-21:00
2. Check **Voltage vs Load Correlation** → Orange points at high kVA
3. **Diagnosis:** Cable too small for peak load
4. **Action:** Upgrade cable or add parallel feeder

---

### **Use Case 2: Over-Voltage Problem**
**Scenario:** Equipment damage reports in area

**Analysis:**
1. Check **Voltage Profile Over Time** → Frequent red zones
2. Check **Voltage vs Load Correlation** → Red points at low load
3. **Diagnosis:** Upstream voltage too high or wrong tap setting
4. **Action:** Adjust transformer tap or request voltage reduction

---

### **Use Case 3: Transformer Sizing Validation**
**Scenario:** Validate new transformer installation

**Analysis:**
1. **Load graphs** → Check if within capacity
2. **Voltage vs Load** → Ensure voltage stable under all loads
3. **Voltage stats** → Confirm <5% over/under voltage
4. **Result:** If green points and <5% violations → properly sized

---

## 🔍 Voltage Limits Explained

### Single-Phase Systems (230V Nominal)
| Limit | Value | Standard |
|-------|-------|----------|
| Nominal | 230V | IEC 60038 |
| Maximum | 253V | +10% |
| Minimum | 207V | -10% |

### Three-Phase Systems (400V Line Voltage)
| Limit | Value | Standard |
|-------|-------|----------|
| Nominal | 400V | IEC 60038 |
| Maximum | 440V | +10% |
| Minimum | 360V | -10% |

**Auto-Detection Logic:**
- If average voltage > 350V → Three-phase system (400V)
- If average voltage ≤ 350V → Single-phase system (230V)

---

## 📊 Complete Graph Summary

The report now includes **8 comprehensive graphs**:

### Voltage Analysis (NEW):
1. ✅ Voltage Profile Over Time
2. ✅ Voltage vs Load Correlation

### Load Analysis:
3. ✅ KVA Load Profile Over Time
4. ✅ KW Load Profile Over Time
5. ✅ Load Percentage Timeline
6. ✅ Average Hourly Load Pattern
7. ✅ Load Duration Curve

### Voltage Quality:
8. ✅ Voltage Quality Distribution (Pie Chart)

---

## ⚙️ Requirements

**CSV File Must Contain:**
- ✅ KVA or KW columns (required)
- ✅ Voltage columns (optional, for voltage graphs)
  - Supported: VOLTAGE, V_L1, V_L2, V_L3, VL1, VL2, VL3
- ✅ Date/Time columns (for time-series)

**Example CSV Structure:**
```csv
DATE,TIME,KVA_IMPORT,KW_IMPORT,V_L1,V_L2,V_L3
2025-01-01,00:00:00,425.3,380.2,228.5,229.1,227.8
2025-01-01,00:15:00,431.2,385.6,227.9,228.5,227.2
...
```

---

## 🎨 Visual Design

### Graph Styling:
- **Consistent color scheme** across all graphs
- **Interactive tooltips** with exact values
- **Zoom and pan** capabilities
- **Professional layout** with clear labels
- **Responsive design** for all screen sizes

### Color Standards:
- 🟣 **Purple (#9c27b0)**: Voltage measurements
- 🔴 **Red (#f44336)**: Over-voltage, critical alerts
- 🟠 **Orange (#ff9800)**: Under-voltage, warnings
- 🟢 **Green (#4caf50)**: Normal, within limits
- 🔵 **Blue (#2196f3)**: KVA measurements
- 🟢 **Green (#4caf50)**: KW measurements

---

## 📈 Benefits

### For Operations:
- ✅ Quickly identify voltage quality issues
- ✅ Correlate voltage problems with load levels
- ✅ Plan voltage regulation improvements

### For Planning:
- ✅ Validate transformer and cable sizing
- ✅ Assess power quality compliance
- ✅ Support investment decisions

### For Compliance:
- ✅ Document voltage quality violations
- ✅ Generate regulatory reports
- ✅ Track improvement measures

---

## 🚀 Future Enhancements

Potential additions:
- [ ] Voltage unbalance analysis
- [ ] Harmonic distortion graphs (THD)
- [ ] Power factor vs load correlation
- [ ] Voltage sag/swell event detection
- [ ] Flicker analysis
- [ ] Comparison with IEEE/IEC standards

---

## ✅ Validation & Testing

**Test Scenarios:**
- ✅ Single-phase systems (230V)
- ✅ Three-phase systems (400V)
- ✅ Missing voltage columns (graceful handling)
- ✅ Multiple voltage phases (L1, L2, L3)
- ✅ PDF generation with voltage data
- ✅ JSON export with voltage analysis

---

**Version:** 1.0  
**Date:** October 13, 2025  
**Status:** Production Ready ✅  
**No Linting Errors:** Confirmed ✅

All voltage graphs are fully functional and automatically included in reports when voltage data is available in the CSV file!


