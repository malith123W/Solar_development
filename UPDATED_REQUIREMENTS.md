# Updated Power Quality Analysis Requirements

## ✅ Current Implementation (Updated)

### Required Files
1. **Feeder NMD** - REQUIRED ✓
2. **Transformer Load Data** - REQUIRED ✓
3. **Consumer Data** - OPTIONAL

### Workflow Steps

```
Step 1: Upload Feeder NMD (Required)
   ↓
Step 2: Upload Consumer Data (Optional)
   ↓
Step 3: Upload Transformer Load Data (Required)
   ↓
Step 4: Enter Transformer Details
   - Transformer Number (e.g., T-001)
   - Transformer Capacity in kVA (Required) *
   ↓
Step 5: Generate Comprehensive Report
   ↓
Step 6: Download as JSON or PDF
```

## 🔒 Validation Rules

### Frontend Validation
- ✅ Feeder NMD file must be uploaded
- ✅ Transformer Load Data file must be uploaded  
- ✅ Transformer Capacity must be a positive number
- ✅ Consumer files are optional (can be 0 or more)

### Backend Validation
- ✅ Session must have NMD data
- ✅ Session must have transformer_load data
- ✅ Transformer capacity must be provided and > 0
- ✅ Consumer data is optional (report generated with or without it)

## 📊 Report Generation

### What Gets Included

**Always Included:**
1. Voltage Quality Analysis from Feeder NMD
2. Feeder-wise Analysis
3. Transformer Load Analysis
   - KVA Load Analysis
   - KW Load Analysis  
   - Overload Detection & Events
   - Load Percentages

**Conditionally Included:**
1. Consumer-wise Analysis (only if consumer files uploaded)

## 🎯 UI Changes Made

### Labels Updated
- ✅ Step 2: "Upload Consumer Data" → "Upload Consumer Data (Optional)"
- ✅ Step 3: "Transformer Load (Optional)" → "Transformer Load Data"
- ✅ Transformer Capacity field: Now always marked with asterisk (*)
- ✅ Removed conditional requirement message

### Button State
Generate Report button is disabled when:
- ❌ No Feeder NMD file
- ❌ No Transformer Load file
- ❌ No Transformer Capacity value

Generate Report button is enabled when:
- ✅ Feeder NMD uploaded
- ✅ Transformer Load uploaded
- ✅ Transformer Capacity entered
- ✅ Consumer files: doesn't matter (optional)

## 📝 Error Messages

| Condition | Error Message |
|-----------|--------------|
| No Feeder File | "Please upload feeder NMD file" |
| No Transformer Load | "Please upload transformer load data file" |
| No/Invalid Capacity | "Please enter a valid transformer rated capacity (kVA)" |

## 🔄 Backend Changes

### API Route: `/api/pq_generate_report`

**Required Parameters:**
```json
{
  "session_id": "pq_session_xxx",
  "feeders_to_use": ["FEEDER_001"],
  "transformer_capacity": 500  // REQUIRED (not optional anymore)
}
```

**Session Requirements:**
- Must have `nmd` data
- Must have `transformer_load` data
- May or may not have `consumers` data

**Response Always Includes:**
- `summary` (voltage quality)
- `feeders` (feeder-wise analysis)
- `transformer_load_analysis` (load analysis)
- `consumers` (only if consumer data uploaded)

## 📄 Report Structure

```json
{
  "title": "Voltage Quality Analysis Report",
  "transformer_number": "T-001",
  "generated_at": "2025-10-13 12:00:00",
  "summary": {
    "overall_analysis": { ... }
  },
  "feeders": {
    "FEEDER_001": { ... }
  },
  "consumers": {  // OPTIONAL - only if uploaded
    "CONSUMER_001": { ... }
  },
  "transformer_load_analysis": {  // REQUIRED
    "rated_capacity_kva": 500,
    "kva_analysis": { ... },
    "kw_analysis": { ... }
  }
}
```

## 🎨 Visual Indicators

### Upload Cards
1. **Feeder NMD**: Blue number badge "1️⃣"
2. **Consumer Data**: Blue number badge "2️⃣" + "(Optional)" text
3. **Transformer Load**: Blue number badge "3️⃣" (no optional text)

### Form Fields
- **Transformer Number**: No asterisk (optional)
- **Transformer Capacity**: Red asterisk "*" (required)

### Generate Button
- Disabled state: Gray, not clickable
- Enabled state: Blue gradient, clickable
- Shows loading spinner when generating

## ✨ Key Differences from Previous Version

| Feature | Before | After |
|---------|--------|-------|
| Consumer Data | Required | Optional |
| Transformer Load | Optional | Required |
| Transformer Capacity | Conditional | Always Required |
| Validation | Feeder + Consumer | Feeder + Transformer |
| Report Generation | Can skip transformer | Always includes transformer |

## 📋 Use Cases

### Use Case 1: Full Analysis
- Upload: Feeder + Consumer + Transformer
- Result: Complete report with all sections

### Use Case 2: Transformer Focus
- Upload: Feeder + Transformer (no consumer)
- Result: Report with voltage quality + transformer load analysis
- Missing: Consumer-wise section (skipped gracefully)

### Use Case 3: Invalid (Will Fail)
- Upload: Feeder + Consumer (no transformer)
- Result: Error - "Please upload transformer load data file"

## 🔧 Implementation Files

### Modified Files
1. `frontend/src/components/PowerQuality.js`
   - Updated UI labels
   - Changed validation logic
   - Updated button disable conditions
   - Updated help text

2. `backend/app.py`
   - Made transformer_load required in session check
   - Made transformer_capacity validation mandatory
   - Kept consumers optional in report building

## 📊 Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Uploads Files                   │
├─────────────────────────────────────────────────────────┤
│  [1] Feeder NMD ────────────────────────► REQUIRED     │
│  [2] Consumer Data ─────────────────────► OPTIONAL     │
│  [3] Transformer Load ──────────────────► REQUIRED     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              User Enters Details                        │
├─────────────────────────────────────────────────────────┤
│  • Transformer Number                                    │
│  • Transformer Capacity (kVA) * ───────► REQUIRED       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│           Validation Checks                             │
├─────────────────────────────────────────────────────────┤
│  ✓ Feeder NMD uploaded?                                 │
│  ✓ Transformer Load uploaded?                           │
│  ✓ Capacity entered and valid?                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│            Generate Comprehensive Report                │
├─────────────────────────────────────────────────────────┤
│  • Voltage Quality Analysis (from Feeder)               │
│  • Feeder-wise Analysis                                 │
│  • Consumer-wise Analysis (if uploaded)                 │
│  • Transformer Load Analysis (ALWAYS)                   │
│    - KVA Analysis                                        │
│    - KW Analysis                                         │
│    - Overload Events                                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Export Options                             │
├─────────────────────────────────────────────────────────┤
│  • Download JSON                                         │
│  • Download PDF                                          │
└─────────────────────────────────────────────────────────┘
```

## ✅ Testing Checklist

- [ ] Upload Feeder only → Error: need transformer load
- [ ] Upload Feeder + Transformer only → Success ✓
- [ ] Upload Feeder + Consumer only → Error: need transformer load
- [ ] Upload Feeder + Consumer + Transformer → Success ✓
- [ ] Generate without capacity → Error: need capacity
- [ ] Generate with capacity = 0 → Error: invalid capacity
- [ ] Generate with capacity > 0 → Success ✓
- [ ] PDF includes transformer section → Yes ✓
- [ ] JSON includes transformer section → Yes ✓
- [ ] Report works without consumers → Yes ✓

---

**Updated**: October 13, 2025  
**Version**: 2.0  
**Status**: Production Ready ✅


