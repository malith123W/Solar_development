# Voltage-Only Phase Correlation Analysis Update

## Date: October 13, 2025

## Summary
Modified the phase correlation analysis to use **ONLY voltage data** from both customer CSV files and feeder data. All non-voltage parameters (KVA, KW, CURRENT, POWER, etc.) are now explicitly excluded from the correlation analysis.

## Modified Files
- `backend/nmd_analysis.py`

## Changes Made

### 1. Enhanced Voltage Column Detection - Feeder Format (Lines 254-286)

#### Previous Implementation
```python
# Look for voltage columns ONLY - focus on voltage for correlation analysis
voltage_patterns = [
    'PHASE_A_INST._VOLTAGE (V)', 'PHASE_B_INST._VOLTAGE (V)', 'PHASE_C_INST._VOLTAGE (V)',
    'VOLTAGE', 'Voltage', 'voltage',
    'PHASE_A', 'PHASE_B', 'PHASE_C',
    'Phase A', 'Phase B', 'Phase C',
    'VA', 'VB', 'VC'
]

for col in df.columns:
    for pattern in voltage_patterns:
        if pattern.upper() in col.upper():
            info['voltage_columns'].append(col)
            break
```

**Problem**: Patterns like 'VA', 'VB', 'VC' could match 'KVA'. Patterns like 'PHASE_A' could match 'PHASE_A_INST._CURRENT (A)'.

#### New Implementation
```python
# Look for voltage columns ONLY - explicitly exclude non-voltage parameters
# Columns to EXCLUDE (non-voltage parameters)
exclude_keywords = ['CURRENT', 'KVA', 'KW', 'KVARH', 'KWH', 'POWER', 'ENERGY', 
                   'APPARENT', 'REACTIVE', 'ACTIVE', 'FACTOR', 'PF', 'FREQUENCY', 'HZ']

# Voltage-specific patterns (must contain one of these)
voltage_keywords = ['VOLTAGE', 'VOLT']

for col in df.columns:
    col_upper = col.upper()
    
    # Skip if column contains any exclude keyword
    if any(exclude_word in col_upper for exclude_word in exclude_keywords):
        continue
    
    # Include if column contains voltage keyword
    if any(voltage_word in col_upper for voltage_word in voltage_keywords):
        info['voltage_columns'].append(col)
        print(f"    Found voltage column: {col}")
```

**Benefits**:
- Explicitly excludes all non-voltage parameters
- Only matches columns containing 'VOLTAGE' or 'VOLT'
- Prevents false matches with KVA, CURRENT, POWER, etc.
- Logs detected voltage columns for transparency

### 2. Enhanced Voltage Column Detection - Customer Format (Lines 311-342)

Applied the same filtering logic to customer data detection:

```python
# Look for voltage columns ONLY - explicitly exclude non-voltage parameters
exclude_keywords = ['CURRENT', 'KVA', 'KW', 'KVARH', 'KWH', 'POWER', 'ENERGY', 
                   'APPARENT', 'REACTIVE', 'ACTIVE', 'FACTOR', 'PF', 'FREQUENCY', 'HZ']

voltage_keywords = ['VOLTAGE', 'VOLT']

for col in df.columns:
    col_upper = col.upper()
    
    # Skip if column contains any exclude keyword
    if any(exclude_word in col_upper for exclude_word in exclude_keywords):
        continue
    
    # Include if column contains voltage keyword
    if any(voltage_word in col_upper for voltage_word in voltage_keywords):
        info['voltage_columns'].append(col)
        print(f"    Found voltage column: {col}")
```

### 3. Improved Phase Assignment Logging (Lines 590-632)

Added detailed logging to show phase assignments clearly:

#### For Single-Phase Customers:
```python
if num_customer_phases == 1:
    best_match = max(phase_matches, key=lambda x: x['score'])
    # ... assignment logic ...
    print(f"      ✅ {best_match['customer_phase']} → Feeder {best_match['feeder_phase']} (Score: {best_match['score']:.3f})")
```

#### For Multi-Phase Customers (2, 3, or more phases):
```python
else:
    # Group by customer phase
    customer_phases = {}
    for match in phase_matches:
        customer_phase = match['customer_phase']
        if customer_phase not in customer_phases:
            customer_phases[customer_phase] = []
        customer_phases[customer_phase].append(match)
    
    # For each customer phase, find the best feeder phase match
    for customer_phase, matches in sorted(customer_phases.items()):
        best_match = max(matches, key=lambda x: x['score'])
        # ... assignment logic ...
        print(f"      ✅ {customer_phase} → Feeder {best_match['feeder_phase']} (Score: {best_match['score']:.3f})")
```

## Expected Debug Output Format

### Example: Three-Phase Customer Analysis

```
Processing customer 0700082108 with 3 voltage columns (VOLTAGE-ONLY correlation)
  Step 1: Testing 1 feeders for VOLTAGE-ONLY correlation: ['0700082108']
    Testing feeder 0700082108 with 12345 data points
    Found voltage column: PHASE_A_INST._VOLTAGE (V)
    Found voltage column: PHASE_B_INST._VOLTAGE (V)
    Found voltage column: PHASE_C_INST._VOLTAGE (V)
    ✅ Feeder 0700082108 - Correlation: 0.892, RMSE: 8.45V, Score: 0.874
  🎯 Best feeder match: 0700082108 (score: 0.874)
  
  Step 2: Performing VOLTAGE-ONLY phase analysis with best feeder 0700082108
    VOLTAGE-ONLY Phase Analysis: 3 customer voltage phases vs 3 feeder voltage phases
      Testing customer Phase A (PHASE_A_INST._VOLTAGE (V))
        ✅ Phase A: r=0.677, RMSE=9.12V, Score=0.642
        ✅ Phase B: r=0.412, RMSE=12.23V, Score=0.384
        ✅ Phase C: r=0.255, RMSE=11.91V, Score=0.227
      Testing customer Phase B (PHASE_B_INST._VOLTAGE (V))
        ✅ Phase A: r=0.389, RMSE=13.45V, Score=0.360
        ✅ Phase B: r=0.821, RMSE=7.89V, Score=0.804
        ✅ Phase C: r=0.298, RMSE=14.21V, Score=0.267
      Testing customer Phase C (PHASE_C_INST._VOLTAGE (V))
        ✅ Phase A: r=0.234, RMSE=15.67V, Score=0.200
        ✅ Phase B: r=0.345, RMSE=13.89V, Score=0.315
        ✅ Phase C: r=0.756, RMSE=8.92V, Score=0.737
      ✅ Phase A → Feeder Phase A (Score: 0.642)
      ✅ Phase B → Feeder Phase B (Score: 0.804)
      ✅ Phase C → Feeder Phase C (Score: 0.737)
    ✅ Phase analysis completed successfully
✅ Customer 0700082108 assigned to 0700082108 (correlation: 0.892)
```

### Example: Single-Phase Customer Analysis

```
Processing customer 0701114909 with 1 voltage columns (VOLTAGE-ONLY correlation)
  Step 1: Testing 1 feeders for VOLTAGE-ONLY correlation: ['0701114909']
    Testing feeder 0701114909 with 8765 data points
    Found voltage column: PHASE_A_INST._VOLTAGE (V)
    ✅ Feeder 0701114909 - Correlation: 0.845, RMSE: 10.34V, Score: 0.822
  🎯 Best feeder match: 0701114909 (score: 0.822)
  
  Step 2: Performing VOLTAGE-ONLY phase analysis with best feeder 0701114909
    VOLTAGE-ONLY Phase Analysis: 1 customer voltage phases vs 3 feeder voltage phases
      Testing customer Phase A (PHASE_A_INST._VOLTAGE (V))
        ✅ Phase A: r=0.845, RMSE=10.34V, Score=0.822
        ✅ Phase B: r=0.567, RMSE=12.89V, Score=0.539
        ✅ Phase C: r=0.423, RMSE=14.56V, Score=0.391
      ✅ Phase A → Feeder Phase A (Score: 0.822)
    ✅ Phase analysis completed successfully
✅ Customer 0701114909 assigned to 0701114909 (correlation: 0.845)
```

## Excluded Parameters

The following parameters are **explicitly excluded** from phase correlation analysis:

### Power Parameters
- `AVG._IMPORT_KW (kW)`
- `AVG._EXPORT_KW (kW)`
- `POWER`
- `KW`

### Apparent Power Parameters
- `AVG._IMPORT_KVA (kVA)`
- `AVG._EXPORT_KVA (kVA)`
- `APPARENT`
- `KVA`

### Current Parameters
- `PHASE_A_INST._CURRENT (A)`
- `PHASE_B_INST._CURRENT (A)`
- `PHASE_C_INST._CURRENT (A)`
- `CURRENT`

### Energy Parameters
- `IMPORT_KWH (kWh)`
- `EXPORT_KWH (kWh)`
- `IMPORT_KVARH (kvarh)`
- `EXPORT_KVARH (kvarh)`
- `ENERGY`
- `KWH`
- `KVARH`

### Reactive Power Parameters
- `REACTIVE`
- `ACTIVE`

### Other Parameters
- `POWER_FACTOR`
- `PF`
- `FACTOR`
- `FREQUENCY`
- `HZ`

## Included Parameters

The following parameters are **included** in phase correlation analysis:

### Voltage Parameters (MUST contain 'VOLTAGE' or 'VOLT')
- `PHASE_A_INST._VOLTAGE (V)`
- `PHASE_B_INST._VOLTAGE (V)`
- `PHASE_C_INST._VOLTAGE (V)`
- Any column containing 'VOLTAGE' or 'VOLT' that doesn't contain excluded keywords

## Algorithm Behavior

### Step 1: Column Detection
1. Scan all columns in customer and feeder CSV files
2. Check if column name contains any exclude keyword (CURRENT, KVA, KW, etc.)
   - If yes: **Skip this column**
   - If no: Continue to next check
3. Check if column name contains voltage keyword (VOLTAGE, VOLT)
   - If yes: **Include this column**
   - If no: Skip this column
4. Log all detected voltage columns for transparency

### Step 2: Feeder Correlation
1. Use detected voltage columns only
2. Calculate correlation and RMSE between customer and feeder voltages
3. Apply scoring formula: `Score = |r| - 0.5 × (RMSE/230)`
4. Select feeder with maximum score

### Step 3: Phase Correlation
1. Within best feeder, compare each customer voltage phase to each feeder voltage phase
2. Use only voltage columns (no current, power, or other parameters)
3. Calculate correlation, RMSE, and score for each phase pair
4. Assign customer phase to feeder phase with highest score
5. Log assignments clearly

## Multi-Phase Support

The algorithm now properly handles:
- **Single-phase customers**: 1 voltage column
- **Two-phase customers**: 2 voltage columns
- **Three-phase customers**: 3 voltage columns
- **N-phase customers**: N voltage columns (flexible)

## Validation Results

✅ Python syntax check passed  
✅ No linter errors detected  
✅ Voltage column detection verified (excludes non-voltage parameters)  
✅ Phase correlation uses only voltage data  
✅ Debug logging improved for clarity  

## Key Improvements

1. **Explicit Exclusion**: Non-voltage parameters are explicitly excluded by keyword matching
2. **Specific Inclusion**: Only columns containing 'VOLTAGE' or 'VOLT' are included
3. **Better Logging**: Debug output clearly shows which voltage columns are being compared
4. **Multi-Phase Support**: Handles 1, 2, 3, or more phase customers
5. **Transparency**: Logs detected voltage columns during file upload

## Benefits

1. **No False Matches**: Prevents accidental matching of KVA, CURRENT, or POWER columns
2. **Voltage-Only Analysis**: Ensures correlation is based purely on voltage profiles
3. **Clear Documentation**: Debug logs clearly show voltage column names and scores
4. **Flexible**: Automatically adapts to different CSV column naming conventions
5. **Robust**: Handles edge cases with different numbers of voltage phases

## Usage

The voltage-only filtering is applied automatically when:
1. Uploading feeder NMD files via `/api/nmd-analysis/upload-feeder`
2. Uploading customer CSV files via `/api/nmd-analysis/upload-customers`
3. Running correlation analysis via `/api/nmd-analysis/analyze`

No configuration changes required - the filtering is built into the column detection logic.

## Testing Recommendations

To verify voltage-only filtering:
1. Check console logs for "Found voltage column:" messages
2. Verify no CURRENT, KVA, or KW columns appear in the logs
3. Review phase correlation output to confirm only voltage comparisons
4. Test with CSV files containing mixed parameters (voltage, current, power)

## Future Enhancements

Consider:
1. Making exclude/include keywords configurable
2. Adding voltage column name validation
3. Supporting alternative voltage units (mV, kV)
4. Adding column name mapping for non-standard formats
5. Implementing column type auto-detection based on data ranges

## References

- File: `backend/nmd_analysis.py`
- Class: `NMDAnalysisProcessor`
- Methods modified:
  - `_detect_feeder_format()` - Lines 254-286
  - `_detect_customer_format()` - Lines 311-342
  - `_determine_phase_assignments()` - Lines 590-632

