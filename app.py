from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import plotly.graph_objects as go
import plotly.utils
import json
import os
import io
from werkzeug.utils import secure_filename
import base64
from datetime import datetime
from typing import Dict, List, Optional, Tuple

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size for large files
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'your-secret-key-here'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Store session data (in production, use Redis or database)
session_data = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/nmd')
def nmd_analysis():
    return render_template('nmd_analysis.html')

@app.route('/power_quality')
def power_quality_page():
    return render_template('power_quality.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    try:
        # Read CSV file
        print(f"Processing file: {file.filename}")
        df = pd.read_csv(file)
        print(f"CSV loaded with {len(df)} rows and columns: {list(df.columns)}")
        
        # Detect data format and available parameters
        data_info = detect_data_format(df)
        
        if not data_info:
            return jsonify({'error': 'CSV must contain voltage, current, or power factor columns'}), 400
        
        # Store data in session
        session_id = request.form.get('session_id', 'default')
        session_data[session_id] = {
            'data': df.to_dict('records'),
            'columns': df.columns.tolist(),
            'filename': file.filename,
            'data_info': data_info,
            'row_count': len(df)
        }
        
        # Generate initial graph with voltage data
        initial_parameter = 'voltage' if data_info['voltage']['available'] else 'current' if data_info['current']['available'] else 'power_factor'
        graph_data = generate_graph_data(df, initial_parameter, data_info)
        
        # Calculate basic statistics
        stats = calculate_statistics(df, data_info)
        
        # Extract time range information
        time_range = get_time_range(df)
        
        return jsonify({
            'success': True,
            'graph_data': graph_data,
            'statistics': stats,
            'data_info': data_info,
            'time_range': time_range,
            'columns': df.columns.tolist(),
            'filename': file.filename,
            'row_count': len(df),
            'initial_parameter': initial_parameter
        })
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/generate_graph', methods=['POST'])
def generate_graph():
    data = request.json
    session_id = data.get('session_id', 'default')
    parameter_type = data.get('parameter_type', 'voltage')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if session_id not in session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    # Convert stored data back to DataFrame
    df = pd.DataFrame(session_data[session_id]['data'])
    df['time'] = pd.to_datetime(df['time'])
    data_info = session_data[session_id]['data_info']
    
    # Apply time filtering if dates are provided
    if start_date and end_date:
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['time'] >= start_dt) & (df['time'] <= end_dt)]
            
            if len(df) == 0:
                return jsonify({'error': 'No data found in the selected date range'}), 400
                
        except Exception as e:
            return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    
    # Generate graph with selected parameter
    graph_data = generate_graph_data(df, parameter_type, data_info)

    # Calculate statistics for the filtered range and selected parameter
    stats_all = calculate_statistics(df, data_info)
    selected_stats = stats_all.get(parameter_type, {})
    
    return jsonify({
        'success': True,
        'graph_data': graph_data,
        'filtered_rows': len(df),
        'statistics': selected_stats
    })

@app.route('/download_graph', methods=['POST'])
def download_graph():
    data = request.json
    session_id = data.get('session_id', 'default')
    parameter_type = data.get('parameter_type', 'voltage')
    format_type = data.get('format', 'png')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if session_id not in session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    # Convert stored data back to DataFrame
    df = pd.DataFrame(session_data[session_id]['data'])
    df['time'] = pd.to_datetime(df['time'])
    data_info = session_data[session_id]['data_info']
    
    # Apply time filtering if dates are provided
    if start_date and end_date:
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['time'] >= start_dt) & (df['time'] <= end_dt)]
            
            if len(df) == 0:
                return jsonify({'error': 'No data found in the selected date range'}), 400
                
        except Exception as e:
            return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    
    # Generate graph
    fig = create_plotly_figure(df, parameter_type, data_info)
    
    # Convert to image
    if format_type == 'png':
        img_bytes = fig.to_image(format="png")
    else:
        img_bytes = fig.to_image(format="jpeg")
    
    # Create file-like object
    img_io = io.BytesIO(img_bytes)
    img_io.seek(0)
    
    # Create filename with date range if filtered
    if start_date and end_date:
        filename = f"{parameter_type}_data_{start_date}_to_{end_date}.{format_type}"
    else:
        filename = f"{parameter_type}_data_{session_id}.{format_type}"
    
    return send_file(
        img_io,
        mimetype=f'image/{format_type}',
        as_attachment=True,
        download_name=filename
    )

@app.route('/nmd_upload', methods=['POST'])
def nmd_upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    try:
        # Read CSV file
        print(f"Processing NMD file: {file.filename}")
        df = pd.read_csv(file)
        print(f"NMD CSV loaded with {len(df)} rows and columns: {list(df.columns)}")
        
        # Detect NMD data format
        nmd_info = detect_nmd_format(df)
        
        if not nmd_info:
            return jsonify({'error': 'CSV must contain Date, Time, CUSTOMER_REF, and three-phase voltage columns'}), 400
        
        # Store data in session
        session_id = request.form.get('session_id', 'default')
        session_data[session_id] = {
            'data': df.to_dict('records'),
            'columns': df.columns.tolist(),
            'filename': file.filename,
            'nmd_info': nmd_info,
            'row_count': len(df)
        }
        
        # Extract unique customer references
        customer_refs = sorted(df['CUSTOMER_REF'].unique().tolist())
        
        # Calculate basic statistics
        stats = calculate_nmd_statistics(df, nmd_info)
        
        # Extract time range information
        time_range = get_time_range(df)
        
        return jsonify({
            'success': True,
            'customer_refs': customer_refs,
            'statistics': stats,
            'nmd_info': nmd_info,
            'time_range': time_range,
            'columns': df.columns.tolist(),
            'filename': file.filename,
            'row_count': len(df)
        })
        
    except Exception as e:
        print(f"Error processing NMD file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/nmd_generate_graph', methods=['POST'])
def nmd_generate_graph():
    data = request.json
    session_id = data.get('session_id', 'default')
    customer_ref = data.get('customer_ref')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if session_id not in session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    if not customer_ref:
        return jsonify({'error': 'Customer reference is required'}), 400
    
    # Convert stored data back to DataFrame
    df = pd.DataFrame(session_data[session_id]['data'])
    df['time'] = pd.to_datetime(df['time'])
    nmd_info = session_data[session_id]['nmd_info']
    
    # Filter data for selected customer
    df = df[df['CUSTOMER_REF'] == customer_ref]
    
    if len(df) == 0:
        return jsonify({'error': f'No data found for customer {customer_ref}'}), 400
    
    # Apply time filtering if dates are provided
    if start_date and end_date:
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['time'] >= start_dt) & (df['time'] <= end_dt)]
            
            if len(df) == 0:
                return jsonify({'error': 'No data found in the selected date range'}), 400
                
        except Exception as e:
            return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    
    # Generate graph with three-phase voltage data
    graph_data = generate_nmd_graph_data(df, nmd_info, customer_ref)
    
    return jsonify({
        'success': True,
        'graph_data': graph_data,
        'filtered_rows': len(df),
        'customer_ref': customer_ref
    })

# -----------------------------
# Power Quality (PQ) Endpoints
# -----------------------------

@app.route('/pq_upload_feeder_nmd', methods=['POST'])
def pq_upload_feeder_nmd():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400

    try:
        session_id = request.form.get('session_id', 'default')
        df = pd.read_csv(file)

        nmd_info = detect_nmd_format(df)
        if not nmd_info:
            return jsonify({'error': 'CSV must contain DATE, TIME, CUSTOMER_REF, and three-phase voltage columns'}), 400

        feeder_id_col = _detect_feeder_id_column(df)
        if not feeder_id_col:
            return jsonify({'error': 'Could not detect feeder identifier column (expected CUSTOMER_REF or FEEDER/FEEDER_ID).'}), 400

        # Build time range metadata
        time_range = get_time_range(df)

        # Extract feeders (treat CUSTOMER_REF/FEEDER as feeder IDs)
        feeders = sorted(pd.Series(df[feeder_id_col].dropna().astype(str).unique()).tolist())

        if session_id not in session_data:
            session_data[session_id] = {}

        # Initialize PQ storage
        pq_state = session_data[session_id].get('pq', {})
        pq_state['nmd'] = {
            'data': df.to_dict('records'),
            'columns': df.columns.tolist(),
            'nmd_info': nmd_info,
            'row_count': len(df),
            'feeder_id_col': feeder_id_col
        }
        pq_state['feeders'] = feeders
        pq_state.setdefault('consumers', {})
        session_data[session_id]['pq'] = pq_state

        return jsonify({
            'success': True,
            'feeders': feeders,
            'feeder_id_col': feeder_id_col,
            'time_range': time_range,
            'row_count': len(df)
        })
    except Exception as e:
        print(f"Error processing PQ NMD file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


@app.route('/pq_upload_consumer', methods=['POST'])
def pq_upload_consumer():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400

    session_id = request.form.get('session_id', 'default')
    consumer_id = (request.form.get('consumer_id') or '').strip() or None
    explicit_feeder_ref = (request.form.get('feeder_ref') or '').strip() or None

    if session_id not in session_data or 'pq' not in session_data[session_id] or 'nmd' not in session_data[session_id]['pq']:
        return jsonify({'error': 'Upload feeder NMD CSV first.'}), 400

    try:
        df = pd.read_csv(file)
        data_info = detect_data_format(df)
        if not data_info or not data_info['voltage']['available']:
            return jsonify({'error': 'Consumer CSV must contain time and voltage data.'}), 400

        # Attempt to detect feeder reference from CSV if not explicitly provided
        feeder_id_col = session_data[session_id]['pq']['nmd'].get('feeder_id_col')
        known_feeders = set(session_data[session_id]['pq'].get('feeders', []))
        inferred_feeder_ref = None

        for candidate in ['CUSTOMER_REF', 'FEEDER_ID', 'FEEDER', 'Feeder', 'feeder']:
            if candidate in df.columns:
                # Take the most frequent non-null value as feeder ref
                values = df[candidate].dropna().astype(str)
                if len(values) > 0:
                    inferred = values.value_counts().idxmax()
                    if str(inferred) in known_feeders or not known_feeders:
                        inferred_feeder_ref = str(inferred)
                        break

        feeder_ref = explicit_feeder_ref or inferred_feeder_ref
        if not feeder_ref:
            return jsonify({'error': 'Feeder reference not provided and could not be inferred from CSV. Please supply feeder_ref.'}), 400

        # Determine consumer_id if not provided
        if not consumer_id:
            consumer_id = (request.form.get('label') or os.path.splitext(secure_filename(file.filename))[0])

        # Persist consumer data in session
        pq_state = session_data[session_id].get('pq', {})
        consumers = pq_state.get('consumers', {})
        consumers[consumer_id] = {
            'data': df.to_dict('records'),
            'columns': df.columns.tolist(),
            'data_info': data_info,
            'row_count': len(df),
            'feeder_ref': feeder_ref
        }
        pq_state['consumers'] = consumers
        session_data[session_id]['pq'] = pq_state

        return jsonify({
            'success': True,
            'consumer_id': consumer_id,
            'feeder_ref': feeder_ref,
            'row_count': len(df),
            'total_consumers': len(consumers)
        })
    except Exception as e:
        print(f"Error processing PQ consumer file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


@app.route('/pq_generate_report', methods=['POST'])
def pq_generate_report():
    data = request.json or {}
    session_id = data.get('session_id', 'default')
    selected_feeders = data.get('selected_feeders')  # Optional list

    if session_id not in session_data or 'pq' not in session_data[session_id] or 'nmd' not in session_data[session_id]['pq']:
        return jsonify({'error': 'No PQ data found in session. Upload NMD and consumer files first.'}), 400

    try:
        pq_state = session_data[session_id]['pq']
        nmd_blob = pq_state['nmd']
        feeders_all = pq_state.get('feeders', [])
        if not feeders_all:
            return jsonify({'error': 'No feeders detected from NMD data.'}), 400

        feeders_to_use = selected_feeders or feeders_all[:4]

        # Build DataFrame and compute metrics
        nmd_df = pd.DataFrame(nmd_blob['data'])
        nmd_info = nmd_blob['nmd_info']
        feeder_id_col = nmd_blob['feeder_id_col']

        report = _build_pq_report(
            nmd_df=nmd_df,
            nmd_info=nmd_info,
            feeder_id_col=feeder_id_col,
            feeders_to_use=feeders_to_use,
            consumers_blob=pq_state.get('consumers', {})
        )

        # Persist report for download
        pq_state['report'] = report
        session_data[session_id]['pq'] = pq_state

        return jsonify({'success': True, 'report': report})
    except Exception as e:
        print(f"Error generating PQ report: {str(e)}")
        return jsonify({'error': f'Could not generate report: {str(e)}'}), 500


@app.route('/pq_download_report', methods=['POST'])
def pq_download_report():
    data = request.json or {}
    session_id = data.get('session_id', 'default')
    filename = data.get('filename') or f'power_quality_report_{session_id}.json'

    if session_id not in session_data or 'pq' not in session_data[session_id] or 'report' not in session_data[session_id]['pq']:
        return jsonify({'error': 'No report available. Generate the report first.'}), 400

    try:
        report = session_data[session_id]['pq']['report']
        buf = io.BytesIO(json.dumps(report, indent=2).encode('utf-8'))
        buf.seek(0)
        return send_file(buf, mimetype='application/json', as_attachment=True, download_name=filename)
    except Exception as e:
        print(f"Error preparing PQ report download: {str(e)}")
        return jsonify({'error': f'Could not download report: {str(e)}'}), 500

def detect_data_format(df):
    """Detect the format of the CSV data and available parameters"""
    data_info = {
        'voltage': {'available': False, 'columns': [], 'phase_count': 0},
        'current': {'available': False, 'columns': [], 'phase_count': 0},
        'power_factor': {'available': False, 'columns': [], 'phase_count': 0}
    }
    
    # Check for voltage columns (handle different naming conventions)
    voltage_columns = []
    
    # Look for 3-phase voltage columns
    three_phase_voltage_patterns = [
        ['PHASE_A_INST._VOLTAGE (V)', 'PHASE_B_INST._VOLTAGE (V)', 'PHASE_C_INST._VOLTAGE (V)'],
        # Add pattern for columns like 'AVG._VOLTAGE (V)' which might be system-wide
    ]
    
    for pattern in three_phase_voltage_patterns:
        if all(col in df.columns for col in pattern):
            voltage_columns = pattern
            data_info['voltage']['available'] = True
            data_info['voltage']['columns'] = voltage_columns
            data_info['voltage']['phase_count'] = 3
            break
    
    # If no 3-phase found, look for single-phase voltage columns
    if not data_info['voltage']['available']:
        single_phase_voltage_patterns = [
            'PHASE_A_INST._VOLTAGE (V)',
            'AVG._VOLTAGE (V)',  # New pattern from the CSV files
        ]
        
        for pattern in single_phase_voltage_patterns:
            if pattern in df.columns:
                voltage_columns = [pattern]
                data_info['voltage']['available'] = True
                data_info['voltage']['columns'] = voltage_columns
                data_info['voltage']['phase_count'] = 1
                break
    
    # Check for current columns (handle different naming conventions)
    current_columns = []
    
    # Look for 3-phase current columns
    three_phase_current_patterns = [
        ['PHASE_A_INST._CURRENT (A)', 'PHASE_B_INST._CURRENT (A)', 'PHASE_C_INST._CURRENT (A)'],
    ]
    
    for pattern in three_phase_current_patterns:
        if all(col in df.columns for col in pattern):
            current_columns = pattern
            data_info['current']['available'] = True
            data_info['current']['columns'] = current_columns
            data_info['current']['phase_count'] = 3
            break
    
    # If no 3-phase found, look for single-phase current columns
    if not data_info['current']['available']:
        single_phase_current_patterns = [
            'PHASE_A_INST._CURRENT (A)',
            'AVG._CURRENT (V)',  # Note: This seems to be mislabeled as (V) in the CSV but is actually current
        ]
        
        for pattern in single_phase_current_patterns:
            if pattern in df.columns:
                current_columns = [pattern]
                data_info['current']['available'] = True
                data_info['current']['columns'] = current_columns
                data_info['current']['phase_count'] = 1
                break
    
    # Check for power factor column (multiple possible names)
    power_factor_columns = [col for col in df.columns if 'POWER_FACTOR' in col.upper() or 'INST._POWER_FACTOR' in col.upper()]
    if power_factor_columns:
        data_info['power_factor']['available'] = True
        data_info['power_factor']['columns'] = power_factor_columns[:1]  # Take the first match
        data_info['power_factor']['phase_count'] = 1  # Power factor is typically system-wide
    
    # Check if DATE and TIME columns exist for time series
    if 'DATE' in df.columns and 'TIME' in df.columns:
        try:
            # Try multiple date formats to handle different CSV formats
            combined_datetime = df['DATE'] + ' ' + df['TIME']
            
            # Try common date formats
            for date_format in ['%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', 'mixed']:
                try:
                    if date_format == 'mixed':
                        df['time'] = pd.to_datetime(combined_datetime, format='mixed', dayfirst=True)
                    else:
                        df['time'] = pd.to_datetime(combined_datetime, format=date_format)
                    print(f"Successfully parsed dates using format: {date_format}")
                    break
                except (ValueError, TypeError) as e:
                    continue
            else:
                # If all formats fail, try pandas' automatic inference with dayfirst=True
                df['time'] = pd.to_datetime(combined_datetime, dayfirst=True, errors='coerce')
                print("Used pandas automatic date inference with dayfirst=True")
                
        except Exception as e:
            print(f"Error parsing dates: {str(e)}")
            # Create a dummy time column if parsing fails
            df['time'] = pd.to_datetime('2025-01-01') + pd.to_timedelta(range(len(df)), unit='min')
            
    elif 'time' in df.columns:
        try:
            df['time'] = pd.to_datetime(df['time'], dayfirst=True)
        except:
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
    else:
        # Create a dummy time column if none exists
        df['time'] = pd.to_datetime('2025-01-01') + pd.to_timedelta(range(len(df)), unit='min')
    
    # Return None if no valid parameters found
    if not any([data_info['voltage']['available'], data_info['current']['available'], data_info['power_factor']['available']]):
        return None
    
    return data_info

def generate_graph_data(df, parameter_type, data_info):
    """Generate graph data for Plotly based on parameter type"""
    try:
        if not data_info[parameter_type]['available']:
            return {
                "data": [{"x": [], "y": [], "type": "scatter", "name": f"No {parameter_type} data available"}],
                "layout": {"title": f"Error: No {parameter_type} data available", "height": 600}
            }
        
        fig = create_plotly_figure(df, parameter_type, data_info)
        return json.loads(fig.to_json())
    except Exception as e:
        print(f"Error generating graph data: {str(e)}")
        return {
            "data": [{"x": [], "y": [], "type": "scatter", "name": "Error"}],
            "layout": {"title": "Error: Could not generate graph data", "height": 600}
        }

def create_plotly_figure(df, parameter_type, data_info):
    """Create Plotly figure for the specified parameter type"""
    try:
        fig = go.Figure()
        
        # Define colors for phases
        colors = {
            'PHASE_A_INST._VOLTAGE (V)': '#1f77b4', 'PHASE_B_INST._VOLTAGE (V)': '#ff7f0e', 'PHASE_C_INST._VOLTAGE (V)': '#2ca02c',
            'PHASE_A_INST._CURRENT (A)': '#1f77b4', 'PHASE_B_INST._CURRENT (A)': '#ff7f0e', 'PHASE_C_INST._CURRENT (A)': '#2ca02c',
            'POWER_FACTOR': '#d62728'
        }
        
        # Get columns for the selected parameter
        columns = data_info[parameter_type]['columns']
        phase_count = data_info[parameter_type]['phase_count']
        
        # Add traces for each phase/column
        for column in columns:
            if column in df.columns:
                # Clean up the column name for display
                display_name = column.replace('PHASE_A_INST._', 'Phase A ').replace('PHASE_B_INST._', 'Phase B ').replace('PHASE_C_INST._', 'Phase C ')
                display_name = display_name.replace(' (V)', '').replace(' (A)', '')
                
                if parameter_type == 'power_factor':
                    display_name = 'Power Factor'
                
                fig.add_trace(go.Scatter(
                    x=df['time'],
                    y=df[column],
                    mode='lines',
                    name=display_name,
                    line=dict(color=colors.get(column, '#000000')),
                    hovertemplate=f'<b>Time:</b> %{{x}}<br><b>{parameter_type.title()}:</b> %{{y:.3f}}<extra></extra>'
                ))
        
        # Set appropriate titles and labels
        if parameter_type == 'voltage':
            title = f'{"3-Phase" if phase_count == 3 else "Single-Phase"} Voltage vs Time'
            yaxis_title = 'Voltage (V)'
        elif parameter_type == 'current':
            title = f'{"3-Phase" if phase_count == 3 else "Single-Phase"} Current vs Time'
            yaxis_title = 'Current (A)'
        else:  # power_factor
            title = 'Power Factor vs Time'
            yaxis_title = 'Power Factor'
        
        fig.update_layout(
            title=title,
            xaxis_title='Time',
            yaxis_title=yaxis_title,
            hovermode='x unified',
            template='plotly_white',
            height=600
        )
        
        return fig
    except Exception as e:
        print(f"Error creating Plotly figure: {str(e)}")
        # Return a simple error figure
        error_fig = go.Figure()
        error_fig.add_trace(go.Scatter(x=[], y=[], mode='lines', name='Error'))
        error_fig.update_layout(title='Error: Could not create graph', height=600)
        return error_fig

def get_time_range(df):
    """Extract time range information from the DataFrame"""
    if 'time' not in df.columns:
        return None
    
    time_series = pd.to_datetime(df['time'])
    min_time = time_series.min()
    max_time = time_series.max()
    
    return {
        'min_date': min_time.strftime('%Y-%m-%d'),
        'max_date': max_time.strftime('%Y-%m-%d'),
        'min_datetime': min_time.strftime('%Y-%m-%dT%H:%M'),
        'max_datetime': max_time.strftime('%Y-%m-%dT%H:%M'),
        'total_days': (max_time - min_time).days + 1,
        'total_records': len(df)
    }

def calculate_statistics(df, data_info):
    """Calculate basic statistics for each available parameter"""
    stats = {}
    
    for parameter_type in ['voltage', 'current', 'power_factor']:
        if data_info[parameter_type]['available']:
            stats[parameter_type] = {}
            for column in data_info[parameter_type]['columns']:
                if column in df.columns:
                    column_data = df[column].dropna()
                    if len(column_data) > 0:
                        stats[parameter_type][column] = {
                            'min': float(column_data.min()),
                            'max': float(column_data.max()),
                            'mean': float(column_data.mean()),
                            'std': float(column_data.std())
                        }
    
    return stats

def detect_nmd_format(df):
    """Detect the format of NMD CSV data"""
    nmd_info = {
        'has_date': False,
        'has_time': False,
        'has_customer_ref': False,
        'voltage_columns': [],
        'phase_count': 0
    }
    
    # Check for required columns
    if 'DATE' in df.columns:
        nmd_info['has_date'] = True
    if 'TIME' in df.columns:
        nmd_info['has_time'] = True
    if 'CUSTOMER_REF' in df.columns:
        nmd_info['has_customer_ref'] = True
    
    # Check for three-phase voltage columns
    voltage_patterns = [
        ['Phase A', 'Phase B', 'Phase C'],
        ['PHASE_A', 'PHASE_B', 'PHASE_C'],
        ['Phase_A', 'Phase_B', 'Phase_C'],
        ['Voltage_A', 'Voltage_B', 'Voltage_C'],
        ['VA', 'VB', 'VC']
    ]
    
    for pattern in voltage_patterns:
        matching_columns = []
        for phase in pattern:
            # Look for columns containing the phase name
            matching_cols = [col for col in df.columns if phase.upper() in col.upper()]
            if matching_cols:
                matching_columns.append(matching_cols[0])
        
        if len(matching_columns) == 3:
            nmd_info['voltage_columns'] = matching_columns
            nmd_info['phase_count'] = 3
            break
    
    # If no 3-phase pattern found, look for any voltage columns
    if not nmd_info['voltage_columns']:
        voltage_cols = [col for col in df.columns if 'voltage' in col.lower() or 'volt' in col.lower()]
        if voltage_cols:
            nmd_info['voltage_columns'] = voltage_cols[:3]  # Take up to 3 columns
            nmd_info['phase_count'] = len(voltage_cols)
    
    # Create time column if DATE and TIME exist
    if nmd_info['has_date'] and nmd_info['has_time']:
        try:
            combined_datetime = df['DATE'].astype(str) + ' ' + df['TIME'].astype(str)
            
            # Try common date formats
            for date_format in ['%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', 'mixed']:
                try:
                    if date_format == 'mixed':
                        df['time'] = pd.to_datetime(combined_datetime, format='mixed', dayfirst=True)
                    else:
                        df['time'] = pd.to_datetime(combined_datetime, format=date_format)
                    print(f"Successfully parsed NMD dates using format: {date_format}")
                    break
                except (ValueError, TypeError) as e:
                    continue
            else:
                # If all formats fail, try pandas' automatic inference
                df['time'] = pd.to_datetime(combined_datetime, dayfirst=True, errors='coerce')
                print("Used pandas automatic date inference for NMD data")
                
        except Exception as e:
            print(f"Error parsing NMD dates: {str(e)}")
            # Create a dummy time column if parsing fails
            df['time'] = pd.to_datetime('2025-01-01') + pd.to_timedelta(range(len(df)), unit='min')
    
    # Return None if required components are missing
    if not (nmd_info['has_date'] and nmd_info['has_time'] and nmd_info['has_customer_ref'] and nmd_info['voltage_columns']):
        return None
    
    return nmd_info

def generate_nmd_graph_data(df, nmd_info, customer_ref):
    """Generate graph data for NMD three-phase voltage analysis"""
    try:
        if not nmd_info['voltage_columns']:
            return {
                "data": [{"x": [], "y": [], "type": "scatter", "name": "No voltage data available"}],
                "layout": {"title": f"Error: No voltage data available for customer {customer_ref}", "height": 600}
            }
        
        fig = create_nmd_plotly_figure(df, nmd_info, customer_ref)
        return json.loads(fig.to_json())
    except Exception as e:
        print(f"Error generating NMD graph data: {str(e)}")
        return {
            "data": [{"x": [], "y": [], "type": "scatter", "name": "Error"}],
            "layout": {"title": "Error: Could not generate NMD graph data", "height": 600}
        }

def create_nmd_plotly_figure(df, nmd_info, customer_ref):
    """Create Plotly figure for NMD three-phase voltage analysis"""
    try:
        fig = go.Figure()
        
        # Define colors for phases
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Blue, Orange, Green
        
        # Add traces for each voltage phase
        for i, column in enumerate(nmd_info['voltage_columns']):
            if column in df.columns:
                # Clean up the column name for display
                display_name = f"Phase {chr(65 + i)}"  # A, B, C
                
                fig.add_trace(go.Scatter(
                    x=df['time'],
                    y=df[column],
                    mode='lines',
                    name=display_name,
                    line=dict(color=colors[i % len(colors)]),
                    hovertemplate=f'<b>Time:</b> %{{x}}<br><b>{display_name} Voltage:</b> %{{y:.3f}} V<extra></extra>'
                ))
        
        fig.update_layout(
            title=f'Three-Phase Voltage Analysis - Customer {customer_ref}',
            xaxis_title='Time',
            yaxis_title='Voltage (V)',
            hovermode='x unified',
            template='plotly_white',
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    except Exception as e:
        print(f"Error creating NMD Plotly figure: {str(e)}")
        # Return a simple error figure
        error_fig = go.Figure()
        error_fig.add_trace(go.Scatter(x=[], y=[], mode='lines', name='Error'))
        error_fig.update_layout(title='Error: Could not create NMD graph', height=600)
        return error_fig

def calculate_nmd_statistics(df, nmd_info):
    """Calculate basic statistics for NMD voltage data"""
    stats = {}
    
    if nmd_info['voltage_columns']:
        stats['voltage'] = {}
        for i, column in enumerate(nmd_info['voltage_columns']):
            if column in df.columns:
                column_data = df[column].dropna()
                if len(column_data) > 0:
                    phase_name = f"Phase {chr(65 + i)}"  # A, B, C
                    stats['voltage'][phase_name] = {
                        'min': float(column_data.min()),
                        'max': float(column_data.max()),
                        'mean': float(column_data.mean()),
                        'std': float(column_data.std())
                    }
    
    return stats

# -----------------------------
# PQ Helper Functions
# -----------------------------

def _detect_feeder_id_column(df: pd.DataFrame) -> Optional[str]:
    for col in ['CUSTOMER_REF', 'Feeder', 'FEEDER', 'FEEDER_ID', 'feeder', 'feeder_id']:
        if col in df.columns:
            return col
    # Try fuzzy match
    for col in df.columns:
        if 'feeder' in str(col).lower() or 'customer_ref' in str(col).lower():
            return col
    return None


def _evaluate_voltage_series(series: pd.Series, v_min: float, v_max: float) -> Dict[str, float]:
    s = pd.to_numeric(series, errors='coerce').dropna()
    total = len(s)
    if total == 0:
        return {'count': 0, 'within_pct': 0.0, 'over_pct': 0.0, 'under_pct': 0.0, 'min': None, 'max': None, 'mean': None}
    within = ((s >= v_min) & (s <= v_max)).sum()
    over = (s > v_max).sum()
    under = (s < v_min).sum()
    return {
        'count': int(total),
        'within_pct': round(within * 100.0 / total, 2),
        'over_pct': round(over * 100.0 / total, 2),
        'under_pct': round(under * 100.0 / total, 2),
        'min': float(s.min()),
        'max': float(s.max()),
        'mean': float(s.mean())
    }


def _compute_feeder_metrics(nmd_df: pd.DataFrame, nmd_info: Dict, feeder_id_col: str, feeders: List[str], v_min: float, v_max: float) -> List[Dict]:
    voltage_cols = [c for c in nmd_info.get('voltage_columns', []) if c in nmd_df.columns]
    results = []
    for feeder in feeders:
        grp = nmd_df[nmd_df[feeder_id_col].astype(str) == str(feeder)]
        phase_metrics: Dict[str, Dict] = {}
        stacked_values = []
        for idx, col in enumerate(voltage_cols):
            phase_name = f"Phase {chr(65 + idx)}"
            m = _evaluate_voltage_series(grp[col] if col in grp.columns else pd.Series([], dtype=float), v_min, v_max)
            phase_metrics[phase_name] = m
            if 'count' in m and m['count'] > 0 and col in grp.columns:
                stacked_values.append(pd.to_numeric(grp[col], errors='coerce'))
        if stacked_values:
            stacked = pd.concat(stacked_values).dropna()
            overall = _evaluate_voltage_series(stacked, v_min, v_max)
        else:
            overall = {'count': 0, 'within_pct': 0.0, 'over_pct': 0.0, 'under_pct': 0.0, 'min': None, 'max': None, 'mean': None}

        results.append({
            'feeder_ref': str(feeder),
            'phase_metrics': phase_metrics,
            'overall': overall
        })
    return results


def _compute_consumer_metrics(consumers_blob: Dict[str, Dict], v_min: float, v_max: float) -> List[Dict]:
    consumer_results = []
    for consumer_id, blob in consumers_blob.items():
        df = pd.DataFrame(blob['data'])
        di = blob.get('data_info', {})
        feeder_ref = blob.get('feeder_ref')
        voltage_cols = di.get('voltage', {}).get('columns', []) if di else []
        phase_metrics: Dict[str, Dict] = {}
        stacked_values = []
        for idx, col in enumerate(voltage_cols):
            if col in df.columns:
                phase_name = f"Phase {chr(65 + idx)}" if len(voltage_cols) > 1 else 'Voltage'
                m = _evaluate_voltage_series(df[col], v_min, v_max)
                phase_metrics[phase_name] = m
                stacked_values.append(pd.to_numeric(df[col], errors='coerce'))

        if stacked_values:
            stacked = pd.concat(stacked_values).dropna()
            overall = _evaluate_voltage_series(stacked, v_min, v_max)
        else:
            overall = {'count': 0, 'within_pct': 0.0, 'over_pct': 0.0, 'under_pct': 0.0, 'min': None, 'max': None, 'mean': None}

        # Current and Power Factor summaries if available
        current_cols = di.get('current', {}).get('columns', []) if di else []
        pf_cols = di.get('power_factor', {}).get('columns', []) if di else []
        avg_current = None
        avg_pf = None
        if current_cols:
            cols_present = [c for c in current_cols if c in df.columns]
            if cols_present:
                avg_current = float(pd.concat([pd.to_numeric(df[c], errors='coerce') for c in cols_present], axis=1).mean(axis=1).dropna().mean())
        if pf_cols:
            c = pf_cols[0]
            if c in df.columns:
                avg_pf = float(pd.to_numeric(df[c], errors='coerce').dropna().mean())

        consumer_results.append({
            'consumer_id': str(consumer_id),
            'feeder_ref': str(feeder_ref) if feeder_ref is not None else None,
            'phase_metrics': phase_metrics,
            'overall': overall,
            'average_current_a': avg_current,
            'average_power_factor': avg_pf
        })
    return consumer_results


def _generate_pq_suggestions(feeders: List[Dict], consumers: List[Dict], limits: Dict[str, float]) -> List[str]:
    suggestions: List[str] = []
    v_min = limits['min']
    v_max = limits['max']

    for f in feeders:
        name = f.get('feeder_ref')
        ov = f['overall'].get('over_pct', 0.0)
        uv = f['overall'].get('under_pct', 0.0)
        fmax = f['overall'].get('max')
        fmin = f['overall'].get('min')
        if ov >= 5.0 or (fmax is not None and fmax > v_max):
            suggestions.append(f"Feeder {name}: Frequent over-voltage. Consider AVR/tap adjustment, feeder load balancing, and reviewing capacitor banks for over-compensation.")
        if uv >= 5.0 or (fmin is not None and fmin < v_min):
            suggestions.append(f"Feeder {name}: Recurrent under-voltage. Check transformer loading, voltage drop along the feeder (conductor sizing, joints), and consider network reconfiguration or capacity reinforcement.")

    for c in consumers:
        cid = c.get('consumer_id')
        feeder = c.get('feeder_ref')
        ov = c['overall'].get('over_pct', 0.0)
        uv = c['overall'].get('under_pct', 0.0)
        avg_pf = c.get('average_power_factor')
        if avg_pf is not None and avg_pf < 0.9:
            suggestions.append(f"Consumer {cid} (Feeder {feeder}): Low PF ({avg_pf:.2f}). Install/optimize capacitor banks to improve PF and reduce voltage drops.")
        if uv >= 5.0:
            suggestions.append(f"Consumer {cid} (Feeder {feeder}): Frequent under-voltage. Investigate service drop voltage drop, redistribute loads, and verify connection integrity.")
        if ov >= 5.0 and (avg_pf or 1.0) > 0.95:
            suggestions.append(f"Consumer {cid} (Feeder {feeder}): Over-voltage events with good PF. Review upstream regulation settings and potential over-compensation.")

    if not suggestions:
        suggestions.append("System appears compliant. Continue periodic monitoring and maintain current settings.")
    return suggestions


def _build_pq_report(nmd_df: pd.DataFrame, nmd_info: Dict, feeder_id_col: str, feeders_to_use: List[str], consumers_blob: Dict[str, Dict]) -> Dict:
    # Limits
    limits = {'nominal': 230.0, 'min': 207.0, 'max': 253.0, 'accept_threshold_pct': 95.0}

    # Compute feeder metrics
    feeder_results = _compute_feeder_metrics(
        nmd_df=nmd_df,
        nmd_info=nmd_info,
        feeder_id_col=feeder_id_col,
        feeders=feeders_to_use,
        v_min=limits['min'],
        v_max=limits['max']
    )

    # Overall transformer metrics (weighted by sample counts)
    total_counts = sum([f['overall'].get('count', 0) for f in feeder_results]) or 1
    weighted_within = sum([(f['overall'].get('within_pct', 0.0) * f['overall'].get('count', 0)) for f in feeder_results]) / total_counts
    weighted_over = sum([(f['overall'].get('over_pct', 0.0) * f['overall'].get('count', 0)) for f in feeder_results]) / total_counts
    weighted_under = sum([(f['overall'].get('under_pct', 0.0) * f['overall'].get('count', 0)) for f in feeder_results]) / total_counts
    maintained = weighted_within >= limits['accept_threshold_pct']

    # Consumers
    consumer_results = _compute_consumer_metrics(consumers_blob=consumers_blob, v_min=limits['min'], v_max=limits['max'])

    # Time range from NMD data
    time_range = get_time_range(nmd_df)

    # Suggestions (Grok AI-like heuristics)
    suggestions = _generate_pq_suggestions(feeder_results, consumer_results, limits)

    return {
        'transformer': {
            'overall_within_pct': round(weighted_within, 2),
            'overall_over_pct': round(weighted_over, 2),
            'overall_under_pct': round(weighted_under, 2),
            'maintained': maintained,
            'time_range': time_range,
            'num_feeders': len(feeder_results),
            'num_consumers': len(consumer_results)
        },
        'feeders': feeder_results,
        'consumers': consumer_results,
        'limits': limits,
        'suggestions': suggestions
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


