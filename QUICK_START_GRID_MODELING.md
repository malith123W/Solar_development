# Quick Start Guide: Enhanced Grid Modeling

## 🚀 Getting Started with Grid Modeling

### Prerequisites
- Backend server running (`python backend/app.py`)
- Frontend server running (`npm start` in frontend directory)
- Feeder NMD CSV file
- Customer CSV files
- Transformer load CSV file (optional, for analysis)

---

## 📋 Step-by-Step Guide

### Step 1: Upload Your Data
1. Navigate to **Smart Grid** section
2. Upload your **Feeder NMD file** (required)
3. Upload **Customer files** (required, can upload multiple)
4. Upload **Transformer load file** (optional)
5. Click **"Analyze Data"** button

### Step 2: Configure Transformer Parameters
In the **Grid Modeling** section, configure your transformer:

**Example 1: Small Distribution Transformer**
```
Capacity: 1000 kVA
Primary Voltage: 11000 V (11 kV)
Secondary Voltage: 400 V
```

**Example 2: Medium Distribution Transformer**
```
Capacity: 5000 kVA
Primary Voltage: 11000 V (11 kV)
Secondary Voltage: 400 V
```

**Example 3: Large Distribution Transformer**
```
Capacity: 10000 kVA
Primary Voltage: 33000 V (33 kV)
Secondary Voltage: 415 V
```

### Step 3: Generate GLM File
1. Click **"Generate GLM File"** button
2. The system will create a GridLAB-D model file with your custom parameters
3. View the generated file path and customer count
4. **Transformer analysis is automatically included** (if transformer file uploaded):
   - Load statistics
   - Voltage analysis  
   - Power factor
   - Smart recommendations

### Step 4: Run Simulation (Optional)
If you have GridLAB-D installed:
1. Click **"Run Simulation"** button
2. View voltage profiles and power losses
3. Analyze the results

---

## 📊 Understanding Transformer Analysis Results

### Load Analysis Card (Blue)
```
Average: 3,245.5 kVA    ← Typical load
Peak: 4,850.2 kVA       ← Maximum load observed
Min: 1,234.8 kVA        ← Minimum load
```

**What it means:**
- If Peak > 80% of capacity → Warning
- If Peak > 90% of capacity → Critical

### Voltage Analysis Card (Yellow)
```
Phase A: 230.5V (±2.3V)
Phase B: 229.8V (±2.1V)
Phase C: 231.2V (±2.5V)
```

**What it means:**
- Deviation > 5% → Voltage imbalance detected
- Check phase connections

### Power Factor Card (Green)
```
Average: 0.92
Range: 0.88 - 0.95
```

**What it means:**
- PF < 0.85 → Consider power factor correction
- PF > 0.90 → Good

### Recommendations Section
Color-coded alerts:
- 🟡 **Yellow (Warning)**: Attention needed
- 🔵 **Blue (Info)**: Informational tips

---

## 💡 Common Scenarios

### Scenario 1: Overloaded Transformer
**Symptoms:**
- High utilization warning
- Peak load > 80% of capacity

**Actions:**
1. Review load distribution
2. Consider load balancing (use Load Balancing tab)
3. Plan transformer upgrade if needed

### Scenario 2: Voltage Imbalance
**Symptoms:**
- Voltage imbalance warning
- Phase voltage deviation > 5%

**Actions:**
1. Check phase connections
2. Review customer distribution across phases
3. Use Load Balancing suggestions

### Scenario 3: Low Power Factor
**Symptoms:**
- Low power factor alert
- PF < 0.85

**Actions:**
1. Consider installing capacitor banks
2. Review reactive power consumption
3. Optimize inductive loads

---

## 🎯 Best Practices

### 1. Transformer Parameter Selection
- **Match real equipment**: Use actual transformer specifications
- **Voltage levels**: Ensure primary/secondary voltages match your network
- **Capacity**: Set appropriate kVA rating

### 2. Data Quality
- **Clean CSV files**: Ensure no missing data
- **Consistent timestamps**: Use standard date/time formats
- **Complete columns**: Include kW, kVA, voltage, current data

### 3. Regular Monitoring
- **Upload new data periodically**: Keep analysis current
- **Track trends**: Compare analysis over time
- **Act on recommendations**: Address warnings promptly

---

## 🔧 Troubleshooting

### Issue: "No transformer data uploaded"
**Solution:** Upload transformer load CSV file first, then click analyze

### Issue: "GridLAB-D not installed" 
**Solution:** 
- You can still use GLM generation, Load Balancing, and Forecasting
- Install GridLAB-D from https://www.gridlabd.org/ for simulations

### Issue: Analysis shows errors
**Solution:**
- Check CSV file format
- Ensure columns contain numeric data
- Verify column names include keywords: KW, KVA, VOLTAGE, CURRENT

---

## 📈 Example Workflow

### Complete Analysis Workflow:
```
1. Upload Files
   └─ Feeder NMD: AZ0887.csv
   └─ Customers: 5 files
   └─ Transformer: transformer_load.csv

2. Analyze Data
   └─ Click "Analyze Data"
   └─ Wait for completion
   └─ View network topology

3. Analyze Transformer
   └─ Click "Analyze Transformer Load"
   └─ Review results:
      • Load: Peak 4,200 kVA (84% utilization)
      • Voltage: 3% imbalance
      • PF: 0.89 (good)
      • Recommendation: Monitor load, consider balancing

4. Configure Grid Model
   └─ Set Capacity: 5000 kVA
   └─ Set Primary: 11000 V
   └─ Set Secondary: 400 V

5. Generate GLM
   └─ Click "Generate GLM File"
   └─ File created with 45 customers

6. Optimize (Optional)
   └─ Go to Load Balancing tab
   └─ Get balancing suggestions
   └─ Apply recommendations
```

---

## 🎓 Tips & Tricks

### Tip 1: Use Realistic Values
Always input transformer parameters that match your actual equipment specifications.

### Tip 2: Regular Analysis
Upload new transformer load data weekly or monthly to track performance trends.

### Tip 3: Combine Features
Use Grid Modeling + Load Balancing + Forecasting together for comprehensive analysis.

### Tip 4: Export Results
Use the "Export PDF" feature to save analysis reports.

### Tip 5: Monitor Recommendations
Pay attention to color-coded recommendations - they indicate priority levels.

---

## 📞 Support

For issues or questions:
1. Check `GRID_MODELING_ENHANCEMENT.md` for detailed documentation
2. Review `SMART_GRID_LOAD_BALANCING_README.md` for overall Smart Grid features
3. Ensure all CSV files have proper format and data

---

## ✅ Success Checklist

- [ ] Data uploaded successfully
- [ ] Data analysis completed
- [ ] Transformer load analyzed (if applicable)
- [ ] Transformer parameters configured
- [ ] GLM file generated
- [ ] Results reviewed
- [ ] Recommendations noted
- [ ] Actions planned

---

**Ready to start? Navigate to the Smart Grid section and begin your analysis!** 🚀

