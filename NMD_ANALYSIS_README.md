# NMD Analysis Feature

## Overview

The NMD Analysis feature allows users to upload NMD (Network Monitoring Device) feeder CSV files and customer CSV files to perform correlation analysis and automatically assign customers to the most appropriate feeders based on voltage profile similarity.

## Features

- **File Upload Interface**: Upload one NMD feeder CSV file and multiple customer CSV files
- **Automatic Data Processing**: Parse and clean CSV files, convert DATE + TIME columns to datetime format
- **Time Alignment**: Align customer and feeder readings using nearest timestamp within 15 minutes
- **Statistical Analysis**: Calculate Pearson correlation coefficient and Root Mean Square Error (RMSE) for each customer-feeder pair
- **Automatic Assignment**: Assign each customer to the feeder with the highest correlation and lowest RMSE
- **Results Visualization**: Display results in tables and interactive voltage curve comparisons
- **JSON API**: Structured results for easy integration with other systems

## File Formats

### NMD Feeder CSV Format
Expected columns:
- `DATE`: Date in DD/MM/YYYY format
- `TIME`: Time in HH:MM:SS format
- Voltage columns: `PHASE_A`, `PHASE_B`, `PHASE_C` (or similar naming)

### Customer CSV Format
Expected columns:
- `DATE`: Date in DD/MM/YYYY format
- `TIME`: Time in HH:MM:SS format
- Voltage columns: `PHASE_A`, `PHASE_B`, `PHASE_C` (or similar naming)

## API Endpoints

### Upload Feeder File
```
POST /nmd_analysis/upload_feeder
Content-Type: multipart/form-data

Parameters:
- file: CSV file
- session_id: Session identifier
```

### Upload Customer Files
```
POST /nmd_analysis/upload_customers
Content-Type: multipart/form-data

Parameters:
- files: Multiple CSV files
- session_id: Session identifier
```

### Run Analysis
```
POST /nmd_analysis/analyze
Content-Type: application/json

Body:
{
    "session_id": "session_id"
}
```

### Get Visualization Data
```
POST /nmd_analysis/visualization
Content-Type: application/json

Body:
{
    "session_id": "session_id",
    "customer_id": "customer_id",
    "feeder_id": "feeder_id"
}
```

## Response Format

### Analysis Results
```json
{
    "success": true,
    "results": {
        "assignments": [
            {
                "customer_id": "CUSTOMER_001",
                "assigned_feeder": "FEEDER_001",
                "correlation": 0.85,
                "rmse": 12.5,
                "aligned_points": 96,
                "customer_filename": "customer_001.csv"
            }
        ],
        "feeder_summary": {
            "FEEDER_001": [
                {
                    "customer_id": "CUSTOMER_001",
                    "assigned_feeder": "FEEDER_001",
                    "correlation": 0.85,
                    "rmse": 12.5,
                    "aligned_points": 96
                }
            ]
        },
        "analysis_metadata": {
            "total_customers": 1,
            "analysis_timestamp": "2025-01-15T10:30:00",
            "time_window_minutes": 15
        }
    }
}
```

## Algorithm Details

### Time Alignment
- Customer and feeder readings are aligned by finding the nearest timestamp within a 15-minute window
- Only aligned pairs with valid voltage readings are used for analysis

### Correlation Calculation
- Uses Pearson correlation coefficient to measure linear relationship between customer and feeder voltage profiles
- Values range from -1 to 1, where 1 indicates perfect positive correlation

### RMSE Calculation
- Root Mean Square Error measures the average magnitude of differences between customer and feeder voltages
- Lower RMSE values indicate better alignment

### Assignment Logic
- Each customer is assigned to the feeder with the highest combined score
- Score = correlation - (normalized_rmse × 0.3)
- This prioritizes correlation while considering RMSE as a secondary factor

## Usage Instructions

1. **Start the Application**
   ```bash
   python app.py
   ```

2. **Access the Feature**
   - Go to `http://localhost:5000/nmd_analysis`
   - Or click "NMD Correlation Analysis" from the main page

3. **Upload Files**
   - Step 1: Upload the NMD feeder CSV file
   - Step 2: Upload one or more customer CSV files
   - Click "Run Analysis" to process the data

4. **View Results**
   - Review the summary statistics
   - Check the customer assignments table
   - View feeder groupings
   - Use the visualization feature to compare voltage curves

## Testing

Run the test script to verify the installation:

```bash
python test_nmd_analysis.py
```

This will:
- Test all required dependencies
- Verify the NMD analysis module
- Check app integration
- Create sample data files for testing

## Dependencies

The following packages are required (automatically installed via requirements.txt):
- `pandas>=2.2.3`
- `numpy>=2.0.0`
- `scipy>=1.11.0`
- `scikit-learn>=1.3.0`
- `Flask>=2.3.3`
- `plotly>=5.17.0`

## Error Handling

The system handles various error conditions:
- Invalid CSV formats
- Missing required columns
- File upload errors
- Data processing failures
- Insufficient aligned data points

Error messages are returned in JSON format with descriptive error details.

## Performance Considerations

- Large CSV files are processed efficiently using pandas
- Time alignment is optimized for performance
- Results are cached in session data
- Memory usage is managed by processing files individually

## Future Enhancements

Potential improvements:
- Support for multiple feeders
- Advanced correlation algorithms
- Real-time data processing
- Export results to various formats
- Batch processing capabilities
- Custom time window configuration

