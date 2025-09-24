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
import numpy as np
# PDF generation imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_agg import FigureCanvasAgg
import tempfile

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

        # Ensure JSON-safe types
        report_safe = _to_json_safe(report)

        # Persist report for download
        pq_state['report'] = report_safe
        session_data[session_id]['pq'] = pq_state

        return jsonify({'success': True, 'report': report_safe})
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
        report_safe = _to_json_safe(report)
        buf = io.BytesIO(json.dumps(report_safe, indent=2).encode('utf-8'))
        buf.seek(0)
        return send_file(buf, mimetype='application/json', as_attachment=True, download_name=filename)
    except Exception as e:
        print(f"Error preparing PQ report download: {str(e)}")
        return jsonify({'error': f'Could not download report: {str(e)}'}), 500

@app.route('/pq_download_pdf', methods=['POST'])
def pq_download_pdf():
    data = request.json or {}
    session_id = data.get('session_id', 'default')
    transformer_number = data.get('transformer_number', 'T-001')

    if session_id not in session_data or 'pq' not in session_data[session_id] or 'report' not in session_data[session_id]['pq']:
        return jsonify({'error': 'No report available. Generate the report first.'}), 400

    try:
        report = session_data[session_id]['pq']['report']
        nmd_data = session_data[session_id]['pq']['nmd']
        consumers_data = session_data[session_id]['pq'].get('consumers', {})
        
        # Generate PDF
        pdf_buffer = generate_power_quality_pdf(report, nmd_data, consumers_data, transformer_number)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Power_Quality_Analysis_Report_{transformer_number}.pdf'
        )
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return jsonify({'error': f'Could not generate PDF: {str(e)}'}), 500

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


def _evaluate_voltage_series(series: pd.Series, v_min: float, v_max: float, v_min_strict: float = None, v_max_strict: float = None) -> Dict[str, float]:
    s = pd.to_numeric(series, errors='coerce').dropna()
    total = len(s)
    if total == 0:
        return {'count': 0, 'within_pct': 0.0, 'over_pct': 0.0, 'under_pct': 0.0, 'interruption_pct': 0.0, 'min': None, 'max': None, 'mean': None, 'within_strict_pct': 0.0, 'over_strict_pct': 0.0, 'under_strict_pct': 0.0}
    
    # Separate zero voltage values (interruptions) from non-zero values
    zero_voltage = (s == 0).sum()
    non_zero_voltage = s[s != 0]
    
    # Calculate interruption percentage
    interruption_pct = round(zero_voltage * 100.0 / total, 2)
    
    # Only calculate voltage quality metrics for non-zero values
    if len(non_zero_voltage) == 0:
        # All values are zero (complete interruption)
        return {
            'count': int(total),
            'within_pct': 0.0,
            'over_pct': 0.0,
            'under_pct': 0.0,
            'interruption_pct': interruption_pct,
            'min': 0.0,
            'max': 0.0,
            'mean': 0.0,
            'within_strict_pct': 0.0,
            'over_strict_pct': 0.0,
            'under_strict_pct': 0.0
        }
    
    # Calculate voltage quality metrics for standard limits (207-253V)
    within = ((non_zero_voltage >= v_min) & (non_zero_voltage <= v_max)).sum()
    over = (non_zero_voltage > v_max).sum()
    under = (non_zero_voltage < v_min).sum()
    
    # Calculate percentages based on non-zero voltage readings only
    non_zero_total = len(non_zero_voltage)
    within_pct = round(within * 100.0 / non_zero_total, 2) if non_zero_total > 0 else 0.0
    over_pct = round(over * 100.0 / non_zero_total, 2) if non_zero_total > 0 else 0.0
    under_pct = round(under * 100.0 / non_zero_total, 2) if non_zero_total > 0 else 0.0
    
    # Calculate strict limits (216-244V) if provided
    within_strict_pct = 0.0
    over_strict_pct = 0.0
    under_strict_pct = 0.0
    
    if v_min_strict is not None and v_max_strict is not None:
        within_strict = ((non_zero_voltage >= v_min_strict) & (non_zero_voltage <= v_max_strict)).sum()
        over_strict = (non_zero_voltage > v_max_strict).sum()
        under_strict = (non_zero_voltage < v_min_strict).sum()
        
        within_strict_pct = round(within_strict * 100.0 / non_zero_total, 2) if non_zero_total > 0 else 0.0
        over_strict_pct = round(over_strict * 100.0 / non_zero_total, 2) if non_zero_total > 0 else 0.0
        under_strict_pct = round(under_strict * 100.0 / non_zero_total, 2) if non_zero_total > 0 else 0.0
    
    return {
        'count': int(total),
        'within_pct': within_pct,
        'over_pct': over_pct,
        'under_pct': under_pct,
        'interruption_pct': interruption_pct,
        'min': float(non_zero_voltage.min()) if len(non_zero_voltage) > 0 else 0.0,
        'max': float(non_zero_voltage.max()) if len(non_zero_voltage) > 0 else 0.0,
        'mean': float(non_zero_voltage.mean()) if len(non_zero_voltage) > 0 else 0.0,
        'within_strict_pct': within_strict_pct,
        'over_strict_pct': over_strict_pct,
        'under_strict_pct': under_strict_pct
    }


def _compute_feeder_metrics(nmd_df: pd.DataFrame, nmd_info: Dict, feeder_id_col: str, feeders: List[str], v_min: float, v_max: float, v_min_strict: float = None, v_max_strict: float = None) -> List[Dict]:
    voltage_cols = [c for c in nmd_info.get('voltage_columns', []) if c in nmd_df.columns]
    results = []
    for feeder in feeders:
        grp = nmd_df[nmd_df[feeder_id_col].astype(str) == str(feeder)]
        phase_metrics: Dict[str, Dict] = {}
        stacked_values = []
        for idx, col in enumerate(voltage_cols):
            phase_name = f"Phase {chr(65 + idx)}"
            m = _evaluate_voltage_series(grp[col] if col in grp.columns else pd.Series([], dtype=float), v_min, v_max, v_min_strict, v_max_strict)
            phase_metrics[phase_name] = m
            if 'count' in m and m['count'] > 0 and col in grp.columns:
                stacked_values.append(pd.to_numeric(grp[col], errors='coerce'))
        if stacked_values:
            stacked = pd.concat(stacked_values).dropna()
            overall = _evaluate_voltage_series(stacked, v_min, v_max, v_min_strict, v_max_strict)
        else:
            overall = {'count': 0, 'within_pct': 0.0, 'over_pct': 0.0, 'under_pct': 0.0, 'min': None, 'max': None, 'mean': None, 'within_strict_pct': 0.0, 'over_strict_pct': 0.0, 'under_strict_pct': 0.0}

        results.append({
            'feeder_ref': str(feeder),
            'phase_metrics': phase_metrics,
            'overall': overall
        })
    return results


def _compute_consumer_metrics(consumers_blob: Dict[str, Dict], v_min: float, v_max: float, v_min_strict: float = None, v_max_strict: float = None) -> List[Dict]:
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
                m = _evaluate_voltage_series(df[col], v_min, v_max, v_min_strict, v_max_strict)
                phase_metrics[phase_name] = m
                stacked_values.append(pd.to_numeric(df[col], errors='coerce'))

        if stacked_values:
            stacked = pd.concat(stacked_values).dropna()
            overall = _evaluate_voltage_series(stacked, v_min, v_max, v_min_strict, v_max_strict)
        else:
            overall = {'count': 0, 'within_pct': 0.0, 'over_pct': 0.0, 'under_pct': 0.0, 'min': None, 'max': None, 'mean': None, 'within_strict_pct': 0.0, 'over_strict_pct': 0.0, 'under_strict_pct': 0.0}

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
        interruption = f['overall'].get('interruption_pct', 0.0)
        fmax = f['overall'].get('max')
        fmin = f['overall'].get('min')
        if interruption >= 1.0:
            suggestions.append(f"Feeder {name}: Power interruptions detected ({interruption:.1f}%). Investigate protective device operations, fault conditions, and supply reliability issues.")
        if ov >= 5.0 or (fmax is not None and fmax > v_max):
            suggestions.append(f"Feeder {name}: Frequent over-voltage. Consider AVR/tap adjustment, feeder load balancing, and reviewing capacitor banks for over-compensation.")
        if uv >= 5.0 or (fmin is not None and fmin < v_min):
            suggestions.append(f"Feeder {name}: Recurrent under-voltage. Check transformer loading, voltage drop along the feeder (conductor sizing, joints), and consider network reconfiguration or capacity reinforcement.")

    for c in consumers:
        cid = c.get('consumer_id')
        feeder = c.get('feeder_ref')
        ov = c['overall'].get('over_pct', 0.0)
        uv = c['overall'].get('under_pct', 0.0)
        interruption = c['overall'].get('interruption_pct', 0.0)
        avg_pf = c.get('average_power_factor')
        if interruption >= 1.0:
            suggestions.append(f"Consumer {cid} (Feeder {feeder}): Power interruptions detected ({interruption:.1f}%). Check service connections, protective devices, and upstream supply reliability.")
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
    # Limits - Standard (207-253V) and Strict (216-244V)
    limits = {
        'nominal': 230.0, 
        'min': 207.0, 
        'max': 253.0, 
        'min_strict': 216.0, 
        'max_strict': 244.0,
        'accept_threshold_pct': 95.0
    }

    # Compute feeder metrics with both limit ranges
    feeder_results = _compute_feeder_metrics(
        nmd_df=nmd_df,
        nmd_info=nmd_info,
        feeder_id_col=feeder_id_col,
        feeders=feeders_to_use,
        v_min=limits['min'],
        v_max=limits['max'],
        v_min_strict=limits['min_strict'],
        v_max_strict=limits['max_strict']
    )

    # Overall transformer metrics (weighted by sample counts) for standard limits
    total_counts = sum([f['overall'].get('count', 0) for f in feeder_results]) or 1
    weighted_within = sum([(f['overall'].get('within_pct', 0.0) * f['overall'].get('count', 0)) for f in feeder_results]) / total_counts
    weighted_over = sum([(f['overall'].get('over_pct', 0.0) * f['overall'].get('count', 0)) for f in feeder_results]) / total_counts
    weighted_under = sum([(f['overall'].get('under_pct', 0.0) * f['overall'].get('count', 0)) for f in feeder_results]) / total_counts
    weighted_interruption = sum([(f['overall'].get('interruption_pct', 0.0) * f['overall'].get('count', 0)) for f in feeder_results]) / total_counts
    
    # Overall transformer metrics for strict limits
    weighted_within_strict = sum([(f['overall'].get('within_strict_pct', 0.0) * f['overall'].get('count', 0)) for f in feeder_results]) / total_counts
    weighted_over_strict = sum([(f['overall'].get('over_strict_pct', 0.0) * f['overall'].get('count', 0)) for f in feeder_results]) / total_counts
    weighted_under_strict = sum([(f['overall'].get('under_strict_pct', 0.0) * f['overall'].get('count', 0)) for f in feeder_results]) / total_counts
    
    maintained = weighted_within >= limits['accept_threshold_pct']
    maintained_strict = weighted_within_strict >= limits['accept_threshold_pct']

    # Consumers with both limit ranges
    consumer_results = _compute_consumer_metrics(
        consumers_blob=consumers_blob, 
        v_min=limits['min'], 
        v_max=limits['max'],
        v_min_strict=limits['min_strict'],
        v_max_strict=limits['max_strict']
    )

    # Time range from NMD data
    time_range = get_time_range(nmd_df)

    # Suggestions (Grok AI-like heuristics)
    suggestions = _generate_pq_suggestions(feeder_results, consumer_results, limits)

    return {
        'transformer': {
            'overall_within_pct': round(weighted_within, 2),
            'overall_over_pct': round(weighted_over, 2),
            'overall_under_pct': round(weighted_under, 2),
            'overall_interruption_pct': round(weighted_interruption, 2),
            'overall_within_strict_pct': round(weighted_within_strict, 2),
            'overall_over_strict_pct': round(weighted_over_strict, 2),
            'overall_under_strict_pct': round(weighted_under_strict, 2),
            'maintained': bool(maintained),
            'maintained_strict': bool(maintained_strict),
            'time_range': time_range,
            'num_feeders': len(feeder_results),
            'num_consumers': len(consumer_results)
        },
        'feeders': feeder_results,
        'consumers': consumer_results,
        'limits': limits,
        'suggestions': suggestions
    }


def _to_json_safe(obj):
    """Recursively convert numpy/pandas types into JSON-serializable Python types."""
    # Primitives and None
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # Numpy scalars
    if isinstance(obj, np.generic):
        return obj.item()

    # Pandas Timestamp
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    # Dict
    if isinstance(obj, dict):
        return {str(_to_json_safe(k)): _to_json_safe(v) for k, v in obj.items()}

    # List or Tuple
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(v) for v in obj]

    # Pandas Series/DataFrame
    if isinstance(obj, pd.Series):
        return [_to_json_safe(v) for v in obj.tolist()]
    if isinstance(obj, pd.DataFrame):
        return [_to_json_safe(rec) for rec in obj.to_dict(orient='records')]

    # Fallback to string
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)

# -----------------------------
# PDF Generation Functions
# -----------------------------

def create_voltage_chart(df, voltage_columns, title="Voltage Profile"):
    """Create a voltage profile chart using matplotlib"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Convert time column to datetime if it exists
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
        x_data = df['time']
    else:
        x_data = range(len(df))
    
    # Use different line styles instead of colors for black and white
    line_styles = ['-', '--', '-.', ':']
    
    for i, col in enumerate(voltage_columns):
        if col in df.columns:
            phase_name = f"Phase {chr(65 + i)}" if len(voltage_columns) > 1 else "Voltage"
            ax.plot(x_data, df[col], label=phase_name, linestyle=line_styles[i % len(line_styles)], linewidth=1.5, color='black')
    
    # Add voltage limits
    ax.axhline(y=207, color='black', linestyle='--', alpha=0.7, label='Min Limit (207V)')
    ax.axhline(y=253, color='black', linestyle='--', alpha=0.7, label='Max Limit (253V)')
    ax.axhline(y=230, color='black', linestyle='-', alpha=0.5, label='Nominal (230V)')
    
    ax.set_title(title, fontsize=14, fontweight='bold', color='black')
    ax.set_xlabel('Time', color='black')
    ax.set_ylabel('Voltage (V)', color='black')
    ax.legend()
    ax.grid(True, alpha=0.3, color='black')
    ax.tick_params(colors='black')
    
    # Format x-axis for time series
    if 'time' in df.columns:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    return fig

def create_current_chart(df, current_columns, title="Current Profile"):
    """Create a current profile chart using matplotlib"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Convert time column to datetime if it exists
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
        x_data = df['time']
    else:
        x_data = range(len(df))
    
    # Use different line styles instead of colors for black and white
    line_styles = ['-', '--', '-.', ':']
    
    for i, col in enumerate(current_columns):
        if col in df.columns:
            phase_name = f"Phase {chr(65 + i)}" if len(current_columns) > 1 else "Current"
            ax.plot(x_data, df[col], label=phase_name, linestyle=line_styles[i % len(line_styles)], linewidth=1.5, color='black')
    
    ax.set_title(title, fontsize=14, fontweight='bold', color='black')
    ax.set_xlabel('Time', color='black')
    ax.set_ylabel('Current (A)', color='black')
    ax.legend()
    ax.grid(True, alpha=0.3, color='black')
    ax.tick_params(colors='black')
    
    # Format x-axis for time series
    if 'time' in df.columns:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    return fig

def create_power_factor_chart(df, pf_columns, title="Power Factor Profile"):
    """Create a power factor profile chart using matplotlib"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Convert time column to datetime if it exists
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
        x_data = df['time']
    else:
        x_data = range(len(df))
    
    for col in pf_columns:
        if col in df.columns:
            ax.plot(x_data, df[col], label='Power Factor', color='black', linewidth=1.5)
    
    # Add power factor limits
    ax.axhline(y=0.9, color='black', linestyle='--', alpha=0.7, label='Min Acceptable (0.9)')
    ax.axhline(y=1.0, color='black', linestyle='-', alpha=0.5, label='Ideal (1.0)')
    
    ax.set_title(title, fontsize=14, fontweight='bold', color='black')
    ax.set_xlabel('Time', color='black')
    ax.set_ylabel('Power Factor', color='black')
    ax.legend()
    ax.grid(True, alpha=0.3, color='black')
    ax.set_ylim(0, 1.1)
    ax.tick_params(colors='black')
    
    # Format x-axis for time series
    if 'time' in df.columns:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    return fig

def create_voltage_quality_pie_chart(within_pct, over_pct, under_pct, interruption_pct):
    """Create a pie chart showing voltage quality distribution"""
    fig, ax = plt.subplots(figsize=(8, 8))
    
    labels = ['Within Limits', 'Over Voltage', 'Under Voltage', 'Interruptions']
    sizes = [within_pct, over_pct, under_pct, interruption_pct]
    colors = ['#28a745', '#dc3545', '#ffc107', '#6c757d']
    
    # Only show non-zero values
    filtered_labels = []
    filtered_sizes = []
    filtered_colors = []
    
    for i, size in enumerate(sizes):
        if size > 0:
            filtered_labels.append(f'{labels[i]} ({size:.1f}%)')
            filtered_sizes.append(size)
            filtered_colors.append(colors[i])
    
    if filtered_sizes:
        ax.pie(filtered_sizes, labels=filtered_labels, colors=filtered_colors, autopct='%1.1f%%', startangle=90)
        ax.set_title('Voltage Quality Distribution', fontsize=14, fontweight='bold')
    else:
        ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_title('Voltage Quality Distribution', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    return fig

def save_chart_to_buffer(fig):
    """Save matplotlib figure to BytesIO buffer"""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    plt.close(fig)
    return buffer

def generate_power_quality_pdf(report, nmd_data, consumers_data, transformer_number='T-001'):
    """Generate a comprehensive 2-page Power Quality Analysis PDF report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles (black and white only)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.black
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.black
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=8,
        textColor=colors.black
    )
    
    # Create list item style
    list_style = ParagraphStyle(
        'CustomList',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6,
        leftIndent=20,
        bulletIndent=10
    )
    
    # Build the story (content)
    story = []
    
    # Page 1: Header and Overview
    story.append(Paragraph("Power Quality Analysis Report", title_style))
    
    # Header information in list format
    transformer_info = report.get('transformer', {})
    time_range = transformer_info.get('time_range', {})
    
    # Get feeder names from the data (one per line)
    feeders = report.get('feeders', [])
    feeder_names = [f.get('feeder_ref', '') for f in feeders[:4]] if feeders else ['N/A']
    
    # Get customer numbers from consumers (one per line)
    consumers = report.get('consumers', [])
    customer_numbers = [c.get('consumer_id', '') for c in consumers[:4]] if consumers else ['Multiple']
    
    # Get status information
    status = "Maintained" if transformer_info.get('maintained', False) else "Not Maintained"
    
    # Create header list with tab spacing for better page utilization
    story.append(Paragraph(f"<b>Transformer Number:</b> {transformer_number}", list_style))
    
    # Customer numbers in vertical list format
    story.append(Paragraph("<b>Customer Numbers:</b>", list_style))
    for customer in customer_numbers:
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{customer}", list_style))
    
    # Feeder names in vertical list format
    story.append(Paragraph("<b>Feeder Names:</b>", list_style))
    for feeder in feeder_names:
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{feeder}", list_style))
    
    story.append(Paragraph(f"<b>Analysis Period:</b> {time_range.get('min_date', 'N/A')} to {time_range.get('max_date', 'N/A')}", list_style))
    story.append(Paragraph(f"<b>Status:</b> {status}", list_style))
    
    story.append(Spacer(1, 20))
    
    # Overall System Performance
    story.append(Paragraph("Overall System Performance", heading_style))
    
    # KPI Table (simplified - no status column, no total rows)
    kpi_data = [
        [Paragraph('Parameter', styles['Normal']), 
         Paragraph('Standard Limits (207-253V)', styles['Normal']), 
         Paragraph('Strict Limits (216-244V)', styles['Normal'])],
        [Paragraph('Within Limits', styles['Normal']), 
         Paragraph(f"{transformer_info.get('overall_within_pct', 0):.2f}%", styles['Normal']), 
         Paragraph(f"{transformer_info.get('overall_within_strict_pct', 0):.2f}%", styles['Normal'])],
        [Paragraph('Over Voltage', styles['Normal']), 
         Paragraph(f"{transformer_info.get('overall_over_pct', 0):.2f}%", styles['Normal']), 
         Paragraph(f"{transformer_info.get('overall_over_strict_pct', 0):.2f}%", styles['Normal'])],
        [Paragraph('Under Voltage', styles['Normal']), 
         Paragraph(f"{transformer_info.get('overall_under_pct', 0):.2f}%", styles['Normal']), 
         Paragraph(f"{transformer_info.get('overall_under_strict_pct', 0):.2f}%", styles['Normal'])],
        [Paragraph('Interruptions', styles['Normal']), 
         Paragraph(f"{transformer_info.get('overall_interruption_pct', 0):.2f}%", styles['Normal']), 
         Paragraph('', styles['Normal'])]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    kpi_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(kpi_table)
    story.append(Spacer(1, 20))
    
    # Feeder Analysis Table (moved to Page 1)
    story.append(Paragraph("Feeder-wise Analysis", subheading_style))
    
    feeders = report.get('feeders', [])
    if feeders:
        # Create header row with Paragraph objects for better text wrapping
        feeder_data = [[Paragraph('Feeder', styles['Normal']), 
                       Paragraph('Within %', styles['Normal']), 
                       Paragraph('Over %', styles['Normal']), 
                       Paragraph('Under %', styles['Normal']), 
                       Paragraph('Interruptions %', styles['Normal']), 
                       Paragraph('Min V', styles['Normal']), 
                       Paragraph('Max V', styles['Normal']), 
                       Paragraph('Mean V', styles['Normal'])]]
        
        for feeder in feeders[:4]:  # Limit to 4 feeders for space
            overall = feeder.get('overall', {})
            feeder_data.append([
                Paragraph(feeder.get('feeder_ref', 'N/A'), styles['Normal']),
                Paragraph(f"{overall.get('within_pct', 0):.2f}", styles['Normal']),
                Paragraph(f"{overall.get('over_pct', 0):.2f}", styles['Normal']),
                Paragraph(f"{overall.get('under_pct', 0):.2f}", styles['Normal']),
                Paragraph(f"{overall.get('interruption_pct', 0):.2f}", styles['Normal']),
                Paragraph(f"{overall.get('min', 0):.1f}" if overall.get('min') else 'N/A', styles['Normal']),
                Paragraph(f"{overall.get('max', 0):.1f}" if overall.get('max') else 'N/A', styles['Normal']),
                Paragraph(f"{overall.get('mean', 0):.1f}" if overall.get('mean') else 'N/A', styles['Normal'])
            ])
        
        feeder_table = Table(feeder_data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        feeder_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(feeder_table)
        story.append(Spacer(1, 20))
    
    # Consumer Analysis Table (moved to be right after Feeder-wise Analysis)
    story.append(Paragraph("Consumer-wise Analysis", subheading_style))
    
    consumers = report.get('consumers', [])
    if consumers:
        # Create header row with Paragraph objects for better text wrapping
        consumer_data = [[Paragraph('Consumer', styles['Normal']), 
                         Paragraph('Within %', styles['Normal']), 
                         Paragraph('Over %', styles['Normal']), 
                         Paragraph('Under %', styles['Normal']), 
                         Paragraph('Min V', styles['Normal']), 
                         Paragraph('Max V', styles['Normal']), 
                         Paragraph('Avg Current (A)', styles['Normal']), 
                         Paragraph('Avg PF', styles['Normal'])]]
        
        for consumer in consumers[:4]:  # Limit to 4 consumers for space
            overall = consumer.get('overall', {})
            consumer_data.append([
                Paragraph(consumer.get('consumer_id', 'N/A'), styles['Normal']),
                Paragraph(f"{overall.get('within_pct', 0):.2f}", styles['Normal']),
                Paragraph(f"{overall.get('over_pct', 0):.2f}", styles['Normal']),
                Paragraph(f"{overall.get('under_pct', 0):.2f}", styles['Normal']),
                Paragraph(f"{overall.get('min', 0):.1f}" if overall.get('min') else 'N/A', styles['Normal']),
                Paragraph(f"{overall.get('max', 0):.1f}" if overall.get('max') else 'N/A', styles['Normal']),
                Paragraph(f"{consumer.get('average_current_a', 0):.2f}" if consumer.get('average_current_a') else 'N/A', styles['Normal']),
                Paragraph(f"{consumer.get('average_power_factor', 0):.3f}" if consumer.get('average_power_factor') else 'N/A', styles['Normal'])
            ])
        
        consumer_table = Table(consumer_data, colWidths=[1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch, 0.8*inch])
        consumer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(consumer_table)
        story.append(Spacer(1, 20))
    
    # Voltage Profile Analysis section (moved to be the last section)
    story.append(Paragraph("Voltage Profile Analysis", subheading_style))
    
    # Generate voltage chart if we have data
    try:
        # Try to create voltage chart from NMD data
        nmd_df = pd.DataFrame(nmd_data['data'])
        nmd_info = nmd_data.get('nmd_info', {})
        voltage_columns = nmd_info.get('voltage_columns', [])
        
        if voltage_columns and len(nmd_df) > 0:
            # Sample data for chart (take every 20th point to avoid overcrowding and fit on page)
            sample_df = nmd_df.iloc[::20].copy()
            
            # Create time column if not exists
            if 'time' not in sample_df.columns and 'DATE' in sample_df.columns and 'TIME' in sample_df.columns:
                sample_df['time'] = pd.to_datetime(sample_df['DATE'] + ' ' + sample_df['TIME'], dayfirst=True)
            
            # Create voltage chart
            voltage_fig = create_voltage_chart(sample_df, voltage_columns, "Voltage Profile Over Time")
            voltage_buffer = save_chart_to_buffer(voltage_fig)
            voltage_img = Image(voltage_buffer, width=7*inch, height=4*inch)
            story.append(voltage_img)
        else:
            # Add a note if no voltage data available
            story.append(Paragraph("Note: No voltage profile data available for analysis.", styles['Normal']))
    
    except Exception as e:
        print(f"Error creating voltage chart: {str(e)}")
        # Add a note if charts couldn't be generated
        story.append(Paragraph("Note: Voltage profile chart could not be generated due to data format issues.", styles['Normal']))
    
    # Generate additional charts if we have data
    try:
        # Try to create current chart if available
        nmd_df = pd.DataFrame(nmd_data['data'])
        current_columns = []
        for col in nmd_df.columns:
            if 'CURRENT' in col.upper() and '(A)' in col:
                current_columns.append(col)
        
        if current_columns and len(nmd_df) > 0:
            sample_df = nmd_df.iloc[::20].copy()
            if 'time' not in sample_df.columns and 'DATE' in sample_df.columns and 'TIME' in sample_df.columns:
                sample_df['time'] = pd.to_datetime(sample_df['DATE'] + ' ' + sample_df['TIME'], dayfirst=True)
            
            story.append(Paragraph("Current Profile Analysis", subheading_style))
            
            # Create current chart
            current_fig = create_current_chart(sample_df, current_columns, "Current Profile Over Time")
            current_buffer = save_chart_to_buffer(current_fig)
            current_img = Image(current_buffer, width=6*inch, height=3*inch)
            story.append(current_img)
            story.append(Spacer(1, 10))
        
        # Try to create power factor chart if available
        pf_columns = []
        for col in nmd_df.columns:
            if 'POWER_FACTOR' in col.upper():
                pf_columns.append(col)
        
        if pf_columns and len(nmd_df) > 0:
            sample_df = nmd_df.iloc[::20].copy()
            if 'time' not in sample_df.columns and 'DATE' in sample_df.columns and 'TIME' in sample_df.columns:
                sample_df['time'] = pd.to_datetime(sample_df['DATE'] + ' ' + sample_df['TIME'], dayfirst=True)
            
            story.append(Paragraph("Power Factor Analysis", subheading_style))
            
            # Create power factor chart
            pf_fig = create_power_factor_chart(sample_df, pf_columns, "Power Factor Over Time")
            pf_buffer = save_chart_to_buffer(pf_fig)
            pf_img = Image(pf_buffer, width=6*inch, height=3*inch)
            story.append(pf_img)
    
    except Exception as e:
        print(f"Error creating charts: {str(e)}")
        # Add a note if charts couldn't be generated
        story.append(Paragraph("Note: Additional charts could not be generated due to data format issues.", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


