# Power Quality Report - Visualization Graphs

## ✅ Implemented Graphs

The comprehensive Power Quality & Transformer Load Analysis report now includes **6 important interactive graphs** to provide visual insights into transformer performance and voltage quality.

---

## 📊 Graph Details

### 1. **Voltage Quality Distribution (Pie Chart)**
**Location:** Overall Summary section  
**Purpose:** Shows the distribution of voltage readings across different quality categories

**Features:**
- **Within Range** (Green): Voltage within 207-253V
- **Over Voltage** (Orange): Voltage above 253V
- **Under Voltage** (Red): Voltage below 207V
- **Interruptions** (Gray): Power interruptions

**Insights:**
- Quick visual assessment of voltage compliance
- Identify if over-voltage or under-voltage is the primary issue
- See percentage of interruptions at a glance

---

### 2. **KVA Load Profile Over Time**
**Location:** Transformer Load Analysis section  
**Purpose:** Shows how transformer load (in KVA) varies over the analysis period

**Features:**
- Blue area chart showing actual KVA load
- Red dashed line showing rated capacity
- Fill-to-zero for better visual impact
- Interactive hover to see exact values
- Time-series x-axis

**Insights:**
- Identify peak load periods
- See when transformer approaches or exceeds capacity
- Understand load trends over time
- Spot unusual load patterns

---

### 3. **KW Load Profile Over Time**
**Location:** Transformer Load Analysis section  
**Purpose:** Shows transformer real power load (in KW) over time

**Features:**
- Green area chart showing actual KW load
- Red dashed line showing rated capacity
- Synchronized with KVA graph
- Interactive tooltips

**Insights:**
- Compare KW vs KVA loading
- Assess power factor indirectly (KW/KVA ratio)
- Identify real power demand patterns

---

### 4. **Load Percentage Timeline**
**Location:** Transformer Load Analysis section  
**Purpose:** Visualizes load as a percentage of rated capacity over time

**Features:**
- Color-coded markers:
  - Green: Load < 90%
  - Orange: Load 90-100%
  - Red: Load > 100% (overload)
- Red shaded area above 100% line shows overload zone
- 100% capacity reference line

**Insights:**
- **Critical:** Immediately see overload periods (red zones)
- Assess proximity to capacity limits
- Identify sustained high-load periods (orange zones)
- Plan capacity upgrades if frequently near 100%

---

### 5. **Average Hourly Load Pattern (Bar Chart)**
**Location:** Transformer Load Analysis section  
**Purpose:** Shows average load for each hour of the day (0-23)

**Features:**
- Color-coded bars:
  - Blue: Normal load (<90%)
  - Orange: High load (90-100%)
  - Red: Overload (>100%)
- Capacity reference line
- 24-hour breakdown

**Insights:**
- **Very Important:** Identify peak demand hours
- Plan load shedding or demand response
- Schedule maintenance during low-load hours
- Understand daily load patterns
- Target energy efficiency programs

**Use Cases:**
- If peak at 18:00-21:00 → Residential area
- If peak at 9:00-17:00 → Commercial/industrial area
- If flat 24/7 → Industrial continuous process

---

### 6. **Load Duration Curve**
**Location:** Transformer Load Analysis section  
**Purpose:** Shows how often the transformer operates at different load levels

**Features:**
- Sorted load from highest to lowest
- X-axis: % of time
- Y-axis: Load (kVA)
- Capacity reference line
- Area fill for visual clarity

**Insights:**
- **Critical for Planning:** See load exceeded only X% of time
- Assess transformer utilization
- Plan capacity: If load > capacity for 5% of time, needs upgrade
- Identify under-utilization: If always < 50%, oversized

**Interpretation:**
```
- Top-left: Peak loads (rare, short duration)
- Middle: Typical operating load
- Bottom-right: Minimum loads
- Where curve crosses capacity line = % of time overloaded
```

---

## 🎯 Graph Priority & Importance

### Critical Graphs (Must Review):
1. ✅ **Load Percentage Timeline** - Shows exactly when overloads occur
2. ✅ **Load Duration Curve** - Essential for capacity planning
3. ✅ **Average Hourly Pattern** - Critical for operational planning

### Important Graphs:
4. ✅ **KVA Load Profile** - Trend analysis
5. ✅ **Voltage Quality Pie Chart** - Compliance at a glance

### Supporting Graphs:
6. ✅ **KW Load Profile** - Power factor assessment

---

## 📈 Graph Features

### All Graphs Include:
- ✅ **Interactive Zoom** - Click and drag to zoom
- ✅ **Pan** - Shift+drag to pan
- ✅ **Hover Tooltips** - See exact values
- ✅ **Export** - Download as PNG
- ✅ **Responsive Design** - Adapts to screen size
- ✅ **Professional Styling** - Clean, modern appearance

### Color Coding Standard:
- 🟢 **Green (#4caf50)**: Normal/Good (< 90%)
- 🟠 **Orange (#ff9800)**: Warning (90-100%)
- 🔴 **Red (#f44336)**: Critical/Overload (> 100%)
- 🔵 **Blue (#2196f3)**: Primary data (KVA)
- 🟢 **Green (#4caf50)**: Secondary data (KW)

---

## 💡 How to Use the Graphs

### For Operations Team:
1. **Check Load Percentage Timeline** for red zones (overloads)
2. **Review Hourly Pattern** to schedule maintenance
3. **Monitor KVA Profile** for unusual spikes

### For Planning Team:
1. **Use Load Duration Curve** for capacity decisions
2. **Analyze Hourly Pattern** for demand forecasting
3. **Review Voltage Quality** for compliance reporting

### For Management:
1. **Voltage Pie Chart** - Quick compliance overview
2. **Load Duration Curve** - Capacity utilization summary
3. **Overload Count** in statistics section

---

## 📊 Backend Data Structure

```javascript
{
  "transformer_load_analysis": {
    "visualization_data": {
      "kva": {
        "time": ["2025-01-01 00:00:00", ...],
        "kva": [425.3, 431.2, ...],
        "load_pct": [85.06, 86.24, ...],
        "overload": [false, false, true, ...],
        "capacity_line": [500, 500, ...],
        "hourly_avg": {
          "0": 380.5,
          "1": 360.2,
          ...
          "23": 420.1
        },
        "load_duration_curve": {
          "load": [523.5, 515.2, ...],  // Sorted descending
          "duration_pct": [0, 0.1, 0.2, ...]
        }
      },
      "kw": { /* similar structure */ }
    }
  }
}
```

---

## 🎨 Visual Examples

### Example Scenarios:

**Scenario 1: Overloaded Transformer**
- Load Duration Curve: Crosses capacity line at 15% duration
- Hourly Pattern: Bars exceed capacity during 18:00-22:00
- Load Percentage Timeline: Multiple red zones
- **Action:** Upgrade transformer or load shedding

**Scenario 2: Under-Utilized Transformer**
- Load Duration Curve: Never exceeds 60% of capacity
- Hourly Pattern: All bars well below capacity
- **Action:** Consider smaller transformer to improve efficiency

**Scenario 3: Voltage Quality Issues**
- Pie Chart: 25% under-voltage (red slice)
- **Action:** Investigate voltage regulation, check tap settings

---

## 📥 Export Capabilities

Each graph can be:
- 📸 **Downloaded as PNG image** (via Plotly toolbar)
- 🖨️ **Included in PDF Report** (automatic)
- 📊 **Data exported in JSON** (full dataset)

---

## 🔄 Future Enhancements (Potential)

- [ ] **Real-time updating graphs** (live monitoring)
- [ ] **Comparison graphs** (month-over-month)
- [ ] **Forecast overlay** (predicted load)
- [ ] **Weather correlation** (temp vs load)
- [ ] **Power factor trend** (separate graph)
- [ ] **3D surface plot** (time vs hour vs load)

---

## 📌 Technical Details

**Graphing Library:** Plotly.js  
**Chart Types Used:**
- Scatter (line charts with fill)
- Bar charts
- Pie charts

**Performance:**
- Optimized for datasets up to 10,000 points
- Downsampling for larger datasets
- Lazy loading for better page performance

**Browser Compatibility:**
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)

---

**Created:** October 13, 2025  
**Version:** 1.0  
**Status:** Production Ready ✅

All graphs are fully functional and ready for use in production reports!


