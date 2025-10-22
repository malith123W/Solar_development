# Voltage Variation Analysis Feature

## Overview

The Voltage Variation Analysis feature provides comprehensive visualization and analysis of voltage drops and variations across the electrical grid, from transformer to NMD readings through feeder networks. This feature helps identify voltage quality issues, load imbalances, and provides actionable recommendations for grid optimization.

## Features

### 1. Voltage Drop Analysis
- **Transformer to NMD Analysis**: Calculates voltage drop from transformer (230V nominal) to NMD readings
- **Feeder-wise Breakdown**: Individual analysis for each feeder showing voltage drop patterns
- **Phase Analysis**: Separate analysis for each phase (R, Y, B) with detailed statistics

### 2. Interactive Visualizations

#### Overview Dashboard
- **Voltage Drop by Feeder**: Bar chart showing average voltage drop for each feeder
- **Voltage Variation by Feeder**: Bar chart showing voltage variation (standard deviation) for each feeder
- **Voltage Distribution**: Histogram showing distribution of voltage drops across all readings
- **Feeder Performance Comparison**: Scatter plot comparing voltage drop vs variation with bubble size indicating reading count

#### Voltage Profile Graph
- **Grid Position Visualization**: Shows voltage profile from Transformer → Feeder Start → Feeder End
- **Voltage Limits Overlay**: Displays standard (207-253V) and strict (216-244V) voltage limits
- **Multi-feeder Comparison**: Overlay multiple feeder profiles for comparison

### 3. Comprehensive Reporting

#### Summary Metrics
- Total feeders analyzed
- Average voltage drop across all feeders
- Maximum voltage drop detected
- Overall voltage variation
- Worst and best performing feeders

#### Feeder Analysis Table
- Individual feeder statistics
- Voltage drop and variation metrics
- Reading counts and consumer counts
- Color-coded performance indicators

#### Recommendations Engine
- Automatic identification of voltage quality issues
- Specific recommendations for problematic feeders
- Priority-based action items

## Technical Implementation

### Backend Components

#### VoltageVariationAnalyzer Class (`backend/voltage_variation.py`)
```python
class VoltageVariationAnalyzer:
    def analyze_voltage_variation(self, nmd_df, nmd_info, feeder_id_col, feeders, consumers_data, transformer_voltage=230.0)
    def create_voltage_variation_graph(self, analysis_data)
    def create_voltage_profile_graph(self, analysis_data, selected_feeders=None)
    def generate_voltage_variation_report(self, analysis_data)
```

#### Key Methods:
- **`analyze_voltage_variation()`**: Core analysis engine calculating voltage drops and variations
- **`create_voltage_variation_graph()`**: Generates 4-panel overview dashboard
- **`create_voltage_profile_graph()`**: Creates voltage profile visualization
- **`generate_voltage_variation_report()`**: Generates comprehensive report with recommendations

### Frontend Components

#### VoltageVariation Component (`frontend/src/components/VoltageVariation.js`)
- Interactive Plotly.js visualizations
- Tabbed interface for different graph types
- Summary cards with key metrics
- Detailed feeder analysis table
- Recommendations display
- Voltage limits reference

### Integration Points

#### Power Quality Analysis Integration
- Automatically triggered during power quality report generation
- Integrated after network topology visualization
- Uses existing NMD data and feeder information
- Leverages consumer data for comprehensive analysis

## Data Flow

1. **Data Input**: NMD readings, feeder information, consumer data
2. **Analysis**: Voltage drop calculation from transformer to NMD readings
3. **Visualization**: Interactive graphs and charts
4. **Reporting**: Comprehensive analysis with recommendations
5. **Integration**: Seamless integration with power quality analysis

## Voltage Limits Reference

### Standard Limits (IEC 60038)
- **Nominal Voltage**: 230V
- **Minimum Standard**: 207V (-10%)
- **Maximum Standard**: 253V (+10%)

### Strict Limits (Enhanced Quality)
- **Minimum Strict**: 216V (-6%)
- **Maximum Strict**: 244V (+6%)

## Usage Instructions

### 1. Data Requirements
- NMD readings with voltage columns (R, Y, B phases)
- Feeder identification column
- Consumer data for each feeder
- Transformer load data (optional but recommended)

### 2. Analysis Workflow
1. Upload NMD feeder data
2. Upload consumer data for each feeder
3. Generate power quality report
4. View voltage variation analysis automatically included

### 3. Interpretation Guidelines

#### Voltage Drop Analysis
- **< 5V**: Excellent performance
- **5-10V**: Good performance, monitor
- **10-15V**: Acceptable, investigate if persistent
- **> 15V**: Poor performance, requires attention

#### Voltage Variation Analysis
- **< 2V**: Excellent stability
- **2-5V**: Good stability, monitor
- **5-10V**: Moderate variation, investigate
- **> 10V**: High variation, requires immediate attention

## Key Benefits

### 1. Grid Optimization
- Identify voltage quality issues early
- Prioritize maintenance and upgrades
- Optimize load distribution

### 2. Customer Service
- Proactive voltage quality monitoring
- Reduced customer complaints
- Improved service reliability

### 3. Planning and Investment
- Data-driven investment decisions
- Feeder reinforcement prioritization
- Load balancing optimization

## Technical Specifications

### Performance
- Handles large datasets efficiently
- Real-time visualization updates
- Optimized for typical grid sizes (10-100 feeders)

### Compatibility
- Works with existing NMD data formats
- Compatible with all feeder types
- Supports three-phase analysis

### Scalability
- Modular design for easy extension
- Configurable voltage limits
- Customizable analysis parameters

## Future Enhancements

### Planned Features
1. **Historical Trend Analysis**: Track voltage quality over time
2. **Predictive Analytics**: Forecast voltage issues
3. **Load Flow Integration**: Combine with load flow analysis
4. **Real-time Monitoring**: Live voltage quality dashboard
5. **Mobile Optimization**: Responsive design for mobile devices

### Advanced Analytics
1. **Machine Learning**: Predictive voltage quality models
2. **Anomaly Detection**: Automatic identification of unusual patterns
3. **Correlation Analysis**: Identify relationships between load and voltage
4. **Optimization Algorithms**: Automated grid optimization suggestions

## Troubleshooting

### Common Issues
1. **No voltage data**: Ensure NMD data contains voltage columns
2. **Missing feeder data**: Verify feeder identification column
3. **Empty analysis**: Check data quality and completeness

### Performance Optimization
1. **Large datasets**: Consider data sampling for initial analysis
2. **Memory usage**: Monitor for very large datasets
3. **Visualization**: Adjust graph complexity for better performance

## Support and Maintenance

### Regular Updates
- Voltage limit updates based on standards
- Algorithm improvements
- Performance optimizations

### User Training
- Comprehensive documentation
- Video tutorials
- Best practices guide

---

*This feature enhances the power quality analysis capabilities by providing detailed voltage variation insights, helping utilities maintain optimal grid performance and customer satisfaction.*
