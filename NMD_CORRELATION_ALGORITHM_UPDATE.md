# NMD Correlation Algorithm Update

## Date: October 13, 2025

## Summary
Updated the feeder and phase correlation analysis algorithm for voltage-only matching between NMD feeder data and customer CSV files. The modifications improve scoring accuracy by using normalized RMSE relative to nominal voltage and absolute correlation values.

## Modified Files
- `backend/nmd_analysis.py`

## Changes Made

### 1. Feeder Correlation Scoring (Lines 437-447)

#### Previous Implementation
```python
# Calculate combined score
normalized_rmse = min(rmse / 100, 1)
score = correlation - (normalized_rmse * 0.3)
```

#### New Implementation
```python
# Calculate combined score with new formula
# Normalize RMSE relative to nominal voltage (230V)
normalized_rmse = rmse / 230.0
# New scoring: Score = |r| - 0.5 × RMSE_norm
score = abs(correlation) - (0.5 * normalized_rmse)
```

#### Changes:
- **RMSE Normalization**: Changed from `min(rmse / 100, 1)` to `rmse / 230.0`
  - Now normalizes RMSE relative to nominal voltage (230V) for better scaling
  - Removes artificial cap at 1.0, allowing true error magnitude representation
  
- **Score Formula**: Changed from `correlation - (normalized_rmse * 0.3)` to `abs(correlation) - (0.5 * normalized_rmse)`
  - Uses absolute value of correlation: `|r|` instead of `r`
  - Increases RMSE weight from 0.3 to 0.5 for more penalty on voltage deviation
  - Higher scores indicate better matches

### 2. Phase Correlation Scoring (Lines 523-533)

Applied the same modifications to phase-level correlation analysis:

#### Previous Implementation
```python
# Calculate combined score
normalized_rmse = min(rmse / 100, 1)
score = correlation - (normalized_rmse * 0.3)
```

#### New Implementation
```python
# Calculate combined score with new formula
# Normalize RMSE relative to nominal voltage (230V)
normalized_rmse = rmse / 230.0
# New scoring: Score = |r| - 0.5 × RMSE_norm
score = abs(correlation) - (0.5 * normalized_rmse)
```

### 3. Score Selection Logic

#### Verified Existing Behavior (No Changes Needed)
The system already correctly selects **maximum** scores:

1. **Feeder Selection** (Line 452):
   ```python
   if score > best_score:
       best_score = score
       best_match = {...}
   ```

2. **Single-Phase Assignment** (Line 586):
   ```python
   best_match = max(phase_matches, key=lambda x: x['score'])
   ```

3. **Three-Phase Assignment** (Line 608):
   ```python
   best_match = max(matches, key=lambda x: x['score'])
   ```

## Algorithm Flow

### Step 1: Feeder Correlation (Voltage-Only Matching)
For each customer:
1. Compare customer voltage profile against each available feeder (F1, F2, F3, etc.)
2. For each feeder:
   - Calculate Pearson correlation coefficient (r) between customer and feeder voltage
   - Calculate RMSE between customer and feeder voltage
   - Normalize RMSE: `RMSE_norm = RMSE / 230`
   - Calculate Score: `Score = |r| - 0.5 × RMSE_norm`
3. Select feeder with **maximum Score**

### Step 2: Phase Correlation (Within Best Feeder)
Once best feeder is identified:
1. Compare each customer phase voltage (A, B, C...) against each feeder phase (A, B, C)
2. For each customer-feeder phase pair:
   - Calculate correlation (r) and RMSE
   - Normalize RMSE: `RMSE_norm = RMSE / 230`
   - Calculate Score: `Score = |r| - 0.5 × RMSE_norm`
3. Assign customer phase to feeder phase with **highest Score**
4. Produce mapping: `Customer Phase X → Feeder Phase Y`

## Mathematical Formulas

### Normalized RMSE
```
RMSE_norm = RMSE / 230
```
Where:
- RMSE is the root mean square error between voltage profiles
- 230V is the nominal voltage for normalization

### Combined Score
```
Score = |r| - 0.5 × RMSE_norm
```
Where:
- r is the Pearson correlation coefficient
- |r| is the absolute value of correlation
- RMSE_norm is the normalized RMSE
- 0.5 is the weight factor for RMSE penalty

### Interpretation
- **Higher scores = Better matches**
- Score range: approximately [-∞, 1]
  - Perfect match: r = 1, RMSE = 0 → Score = 1.0
  - Good match: r = 0.9, RMSE = 23V → Score ≈ 0.85
  - Poor match: r = 0.5, RMSE = 46V → Score ≈ 0.40

## Benefits of New Algorithm

1. **Better Scaling**: RMSE normalized to nominal voltage (230V) provides consistent scaling across different voltage ranges

2. **Absolute Correlation**: Using |r| treats positive and negative correlations equally by magnitude

3. **Appropriate Error Penalty**: 0.5 weight factor for RMSE gives proper importance to voltage deviation errors

4. **Voltage-Only Matching**: Algorithm focuses exclusively on voltage profiles for correlation, suitable for feeder-customer assignment

5. **Physical Meaning**: Normalized RMSE has physical meaning (error relative to nominal voltage)

## Testing & Validation

✅ Python syntax validation passed  
✅ No linter errors  
✅ Score selection logic verified (maximum scores)  
✅ Both feeder-level and phase-level scoring updated consistently  

## Usage Notes

- The algorithm is used through the `/api/nmd-analysis/analyze` endpoint
- Results include:
  - `correlation`: Pearson correlation coefficient (r)
  - `rmse`: Root mean square error in volts
  - `score`: Combined score using new formula
  - `phase_assignments`: Mapping of customer phases to feeder phases
  
- Higher scores indicate better matches
- Minimum aligned data points: 10 (configurable via `time_window_minutes`)

## Future Enhancements

Consider:
1. Making nominal voltage (230V) configurable for different regions
2. Making RMSE weight (0.5) configurable for different use cases
3. Adding additional metrics like phase angle or frequency analysis
4. Implementing confidence intervals for correlation values

## References

- File: `backend/nmd_analysis.py`
- Class: `NMDAnalysisProcessor`
- Methods modified:
  - `_find_best_feeder_match_multi()` - Lines 437-447
  - `_analyze_phase_correlation()` - Lines 523-533

