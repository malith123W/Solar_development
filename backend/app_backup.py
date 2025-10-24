from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import plotly.graph_objects as go
import plotly.utils
import json
import os
import io
import tempfile
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
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Smart Load Balancing & Forecasting imports removed - modules not found

# Power Quality Analysis imports
from power_quality import PowerQualityAnalyzer

# Voltage Variation Analysis imports
from voltage_variation import VoltageVariationAnalyzer

# Import session_data from utils (shared across all modules)
from utils import session_data

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Smart Grid processors removed - modules not found

# Initialize Power Quality Analyzer
pq_analyzer = PowerQualityAnalyzer()

# Initialize Voltage Variation Analyzer
voltage_analyzer = VoltageVariationAnalyzer()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'API is running'})

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({'message': 'Test endpoint working', 'timestamp': datetime.now().isoformat()})

# Dashboard routes
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    try:
        session_id = request.form.get('session_id', 'default')
        df = pd.read_csv(file)
        
        # Detect data format
        data_info = detect_data_format(df)
        
        # Build time range metadata
        time_range = get_time_range(df)
        
        # Calculate statistics
        stats = calculate_statistics(df, data_info)

        # Store session data
        session_data[session_id] = {
            'data': df.to_dict('records'),
            'data_info': data_info,
            'time_range': time_range,
            'filename': file.filename
        }

        return jsonify({
            'success': True,
            'filename': file.filename,
            'row_count': len(df),
            'columns': list(df.columns),
            'data_info': data_info,
            'time_range': time_range,
            'statistics': stats,
            'initial_parameter': 'voltage'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/api/generate_graph', methods=['POST'])
def generate_graph():
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        parameter_type = data.get('parameter_type', 'voltage')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if session_id not in session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        df = pd.DataFrame(session_data[session_id]['data'])
        data_info = session_data[session_id]['data_info']
        
        # Filter by date range if provided
        if start_date and end_date:
            df['time'] = pd.to_datetime(df['time'])
            start_datetime = pd.to_datetime(start_date)
            end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df = df[(df['time'] >= start_datetime) & (df['time'] <= end_datetime)]
        
        # Generate graph data
        graph_data = generate_graph_data(df, parameter_type, data_info)
        
        # Calculate statistics for filtered data
        stats = calculate_statistics(df, data_info)

        # Ensure all data is JSON serializable
        try:
            plot_data_json = json.dumps(graph_data)
        except Exception as e:
            # Convert numpy arrays and other non-serializable objects
            def make_serializable(obj):
                if hasattr(obj, 'tolist'):  # numpy arrays
                    return obj.tolist()
                elif hasattr(obj, 'to_dict'):  # Plotly objects
                    return obj.to_dict()
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_serializable(item) for item in obj]
                else:
                    return obj
            
            graph_data_serializable = make_serializable(graph_data)
            plot_data_json = json.dumps(graph_data_serializable)

        return jsonify({
            'success': True,
            'plot_data': plot_data_json,
            'statistics': stats
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating graph: {str(e)}'}), 500

@app.route('/api/download_graph', methods=['POST'])
def download_graph():
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        parameter_type = data.get('parameter_type', 'voltage')
        format_type = data.get('format', 'png')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if session_id not in session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        df = pd.DataFrame(session_data[session_id]['data'])
        data_info = session_data[session_id]['data_info']
        
        # Filter by date range if provided
        if start_date and end_date:
            df['time'] = pd.to_datetime(df['time'])
            start_datetime = pd.to_datetime(start_date)
            end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df = df[(df['time'] >= start_datetime) & (df['time'] <= end_datetime)]
        
        # Generate graph data
        graph_data = generate_graph_data(df, parameter_type, data_info)
        
        # Create plotly figure
        fig = create_plotly_figure(df, parameter_type, data_info)
        
        # Convert to image
        img_bytes = fig.to_image(format=format_type, width=1200, height=800)
        
        return send_file(
            io.BytesIO(img_bytes),
            mimetype=f'image/{format_type}',
            as_attachment=True,
            download_name=f'electrical_data.{format_type}'
        )
        
    except Exception as e:
        return jsonify({'error': f'Error downloading graph: {str(e)}'}), 500

# NMD Analysis routes
@app.route('/api/nmd_upload', methods=['POST'])
def nmd_upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    try:
        session_id = request.form.get('session_id', 'default')
        df = pd.read_csv(file)
        
        # Detect NMD format
        nmd_info = detect_nmd_format(df)
        if not nmd_info:
            return jsonify({'error': 'CSV must contain DATE, TIME, CUSTOMER_REF, and three-phase voltage columns'}), 400
        
        # Build time range metadata
        time_range = get_time_range(df)
        
        # Extract customer references
        customer_refs = sorted(df['CUSTOMER_REF'].dropna().astype(str).unique().tolist())
        
        # Calculate statistics
        stats = calculate_nmd_statistics(df, nmd_info)
        
        # Store session data
        session_data[session_id] = {
            'data': df.to_dict('records'),
            'nmd_info': nmd_info,
            'time_range': time_range,
            'filename': file.filename
        }
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'row_count': len(df),
            'columns': list(df.columns),
            'nmd_info': nmd_info,
            'time_range': time_range,
            'customer_refs': customer_refs,
            'statistics': stats
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/api/nmd_generate_graph', methods=['POST'])
def nmd_generate_graph():
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        customer_ref = data.get('customer_ref')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if session_id not in session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        df = pd.DataFrame(session_data[session_id]['data'])
        nmd_info = session_data[session_id]['nmd_info']
        
        if not customer_ref:
            return jsonify({'error': 'Customer reference is required'}), 400
        
        # Filter data for specific customer
        customer_data = df[df['CUSTOMER_REF'] == customer_ref]
        if len(customer_data) == 0:
            return jsonify({'error': f'No data found for customer {customer_ref}'}), 404
        
        # Filter by date range if provided
        if start_date and end_date:
            customer_data['time'] = pd.to_datetime(customer_data['time'])
            start_datetime = pd.to_datetime(start_date)
            end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            customer_data = customer_data[(customer_data['time'] >= start_datetime) & (customer_data['time'] <= end_datetime)]
        
        # Generate graph data
        graph_data = generate_nmd_graph_data(customer_data, nmd_info, customer_ref)
        
        return jsonify({
            'success': True,
            'plot_data': json.dumps(graph_data),
            'customer_ref': customer_ref,
            'record_count': len(customer_data)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating graph: {str(e)}'}), 500

# Power Quality Analysis routes
@app.route('/api/pq_upload_feeder_nmd', methods=['POST'])
def pq_upload_feeder_nmd():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    try:
        session_id = request.form.get('session_id', 'default')
        return pq_analyzer.upload_feeder_nmd(file, session_id)
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/api/pq_upload_consumer', methods=['POST'])
def pq_upload_consumer():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    try:
        session_id = request.form.get('session_id', 'default')
        consumer_id = request.form.get('consumer_id', file.filename)
        feeder_ref = request.form.get('feeder_ref', 'Unknown')
        
        df = pd.read_csv(file)
        
        # Store consumer data in PQ state
        if session_id not in session_data:
            session_data[session_id] = {}
        
        # Initialize PQ state if it doesn't exist
        if 'pq' not in session_data[session_id]:
            session_data[session_id]['pq'] = {}
        
        if 'consumers' not in session_data[session_id]['pq']:
            session_data[session_id]['pq']['consumers'] = {}
        
        session_data[session_id]['pq']['consumers'][consumer_id] = {
            'data': df.to_dict('records'),
            'feeder': feeder_ref,
            'filename': file.filename
        }
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'consumer_id': consumer_id,
            'feeder_ref': feeder_ref,
            'row_count': len(df)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/api/pq_generate_report', methods=['POST'])
def pq_generate_report():
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        feeders_to_use = data.get('feeders_to_use', [])
        transformer_capacity = data.get('transformer_capacity')  # Required for transformer load analysis
        
        if session_id not in session_data:
            return jsonify({'error': 'No PQ data found in session. Upload feeder NMD file first.'}), 404
        
        if 'pq' not in session_data[session_id]:
            return jsonify({'error': 'No PQ data found in session. Upload feeder NMD file first.'}), 404
        
        pq_state = session_data[session_id]['pq']
        
        if 'nmd' not in pq_state:
            return jsonify({'error': 'No NMD data found. Upload feeder NMD file first.'}), 400
        
        # Transformer load data is now required
        if 'transformer_load' not in pq_state:
            return jsonify({'error': 'No transformer load data found. Upload transformer load file first.'}), 400
        
        if not transformer_capacity or transformer_capacity <= 0:
            return jsonify({'error': 'Valid transformer rated capacity (kVA) is required'}), 400
        
        nmd_blob = pq_state['nmd']
        nmd_df = pd.DataFrame(nmd_blob['data'])
        nmd_info = nmd_blob['nmd_info']
        feeder_id_col = nmd_blob['feeder_id_col']
        
        # Get consumer data for analysis
        consumers_data = pq_state.get('consumers', {})
        
        # Include all selected feeders for analysis, regardless of consumer data availability
        # This allows feeder-wise analysis even without consumer data
        available_feeders = feeders_to_use if feeders_to_use else []
        
        # Build PQ report (includes all selected feeders, with or without consumer data)
        report = _build_pq_report(
            nmd_df=nmd_df,
            nmd_info=nmd_info,
            feeder_id_col=feeder_id_col,
            feeders_to_use=available_feeders,
            consumers_blob=consumers_data
        )
        
        # Perform transformer load analysis (now required)
        load_data = pq_state['transformer_load']
        df = pd.DataFrame(load_data['data'])
        kva_col = load_data['kva_col']
        kw_col = load_data['kw_col']
        voltage_cols = load_data.get('voltage_cols', [])
        
        # Perform transformer load analysis
        transformer_analysis = _analyze_transformer_load(
            df, kva_col, kw_col, transformer_capacity, voltage_cols
        )
        
        report['transformer_load_analysis'] = transformer_analysis
        
        # Store analysis in session
        if 'transformer_load' not in pq_state:
            pq_state['transformer_load'] = {}
        pq_state['transformer_load']['analysis'] = transformer_analysis
        
        # Generate network graph data
        try:
            from power_quality import PowerQualityAnalyzer
            pq_analyzer = PowerQualityAnalyzer()
            graph_data = pq_analyzer._build_pq_hierarchical_graph(
                nmd_df=nmd_df,
                nmd_info=nmd_info,
                feeder_id_col=feeder_id_col,
                feeders=available_feeders,
                transformer_name='Transformer',
                consumers_data=consumers_data
            )
            report['network_graph'] = graph_data
        except Exception as e:
            print(f"Warning: Could not generate network graph: {str(e)}")
            report['network_graph'] = None
        
        # Generate voltage variation analysis
        try:
            voltage_analysis = voltage_analyzer.analyze_voltage_variation(
                nmd_df=nmd_df,
                nmd_info=nmd_info,
                feeder_id_col=feeder_id_col,
                feeders=available_feeders,
                consumers_data=consumers_data,
                transformer_voltage=230.0  # Default transformer voltage
            )
            
            # Create voltage variation graphs
            voltage_graphs = voltage_analyzer.create_voltage_variation_graph(voltage_analysis)
            voltage_profile = voltage_analyzer.create_voltage_profile_graph(voltage_analysis, available_feeders)
            voltage_report = voltage_analyzer.generate_voltage_variation_report(voltage_analysis)
            
            report['voltage_variation'] = {
                'analysis': voltage_analysis,
                'graphs': voltage_graphs,
                'profile': voltage_profile,
                'report': voltage_report
            }
        except Exception as e:
            print(f"Warning: Could not generate voltage variation analysis: {str(e)}")
            report['voltage_variation'] = None
        
        # Ensure JSON-safe types
        report_safe = _to_json_safe(report)
        
        # Store report in session
        session_data[session_id]['report'] = report_safe
        
        return jsonify({
            'success': True,
            'report': report_safe
        })
        
    except Exception as e:
        return jsonify({'error': f'Could not generate report: {str(e)}'}), 500

@app.route('/api/pq_network_graph', methods=['POST'])
def pq_network_graph():
    """Generate hierarchical network graph visualization for Power Quality Analysis"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        transformer_name = data.get('transformer_name', 'Transformer')
        return pq_analyzer.generate_network_graph(session_id, transformer_name)
    except Exception as e:
        return jsonify({'error': f'Error generating network graph: {str(e)}'}), 500

@app.route('/api/pq_download_report', methods=['POST'])
def pq_download_report():
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        if session_id not in session_data or 'report' not in session_data[session_id]:
            return jsonify({'error': 'No report found. Generate report first.'}), 404
        
        report = session_data[session_id]['report']
        
        # Create JSON file
        json_str = json.dumps(report, indent=2)
        
        return send_file(
            io.BytesIO(json_str.encode()),
            mimetype='application/json',
            as_attachment=True,
            download_name='power_quality_report.json'
        )
        
    except Exception as e:
        return jsonify({'error': f'Error downloading report: {str(e)}'}), 500

@app.route('/api/pq_download_pdf', methods=['POST'])
def pq_download_pdf():
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        transformer_number = data.get('transformer_number', 'T-001')
        
        if session_id not in session_data or 'report' not in session_data[session_id]:
            return jsonify({'error': 'No report found. Generate report first.'}), 404
        
        report = session_data[session_id]['report']
        nmd_data = session_data[session_id].get('nmd', {})
        consumers_data = session_data[session_id].get('consumers', {})
        
        # Generate PDF
        pdf_buffer = generate_power_quality_pdf(report, nmd_data, consumers_data, transformer_number)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='power_quality_report.pdf'
        )
        
    except Exception as e:
        import traceback
        print("PDF Generation Error:")
        print(traceback.format_exc())
        return jsonify({'error': f'Error generating PDF: {str(e)}'}), 500

# Transformer Load Analysis routes removed - unused functionality




# Smart Grid routes removed - modules not found

def _analyze_transformer_load(df, kva_col, kw_col, rated_capacity, voltage_cols=None):
    """Helper function to analyze transformer load data"""
    if voltage_cols is None:
        voltage_cols = []
    
    analysis_results = {
        'rated_capacity_kva': rated_capacity,
        'kva_analysis': None,
        'kw_analysis': None,
        'voltage_analysis': None,
        'time_range': {},
        'visualization_data': {}
    }
    
    # Time range
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
        analysis_results['time_range'] = {
            'start': df['time'].min().strftime('%Y-%m-%d %H:%M:%S'),
            'end': df['time'].max().strftime('%Y-%m-%d %H:%M:%S'),
            'total_records': len(df)
        }
    
    # Analyze KVA
    if kva_col:
        kva_data = pd.to_numeric(df[kva_col], errors='coerce').dropna()
        load_pct = (kva_data / rated_capacity) * 100
        overload_mask = load_pct > 100
        overload_count = overload_mask.sum()
        
        # Calculate overload duration (assuming 15-minute intervals)
        overload_duration_hours = (overload_count * 15) / 60
        
        # Calculate hourly load pattern (average by hour of day)
        if 'time' in df.columns:
            df_temp = df.copy()
            df_temp['kva'] = kva_data
            df_temp['hour'] = pd.to_datetime(df_temp['time']).dt.hour
            hourly_avg = df_temp.groupby('hour')['kva'].mean().to_dict()
        else:
            hourly_avg = {}
        
        # Find overload events (consecutive overloads)
        overload_events = []
        if overload_count > 0:
            overload_indices = df[overload_mask].index.tolist()
            event_start = overload_indices[0]
            
            for i in range(1, len(overload_indices)):
                if overload_indices[i] != overload_indices[i-1] + 1:
                    # Event ended
                    event_end = overload_indices[i-1]
                    event_max_load = df.loc[event_start:event_end, kva_col].max()
                    event_start_time = df.loc[event_start, 'time'] if 'time' in df.columns else f"Record {event_start}"
                    event_end_time = df.loc[event_end, 'time'] if 'time' in df.columns else f"Record {event_end}"
                    
                    overload_events.append({
                        'start': str(event_start_time),
                        'end': str(event_end_time),
                        'max_load_kva': float(event_max_load),
                        'max_load_pct': float((event_max_load / rated_capacity) * 100),
                        'duration_records': event_end - event_start + 1
                    })
                    
                    event_start = overload_indices[i]
            
            # Add last event
            event_end = overload_indices[-1]
            event_max_load = df.loc[event_start:event_end, kva_col].max()
            event_start_time = df.loc[event_start, 'time'] if 'time' in df.columns else f"Record {event_start}"
            event_end_time = df.loc[event_end, 'time'] if 'time' in df.columns else f"Record {event_end}"
            
            overload_events.append({
                'start': str(event_start_time),
                'end': str(event_end_time),
                'max_load_kva': float(event_max_load),
                'max_load_pct': float((event_max_load / rated_capacity) * 100),
                'duration_records': event_end - event_start + 1
            })
        
        analysis_results['kva_analysis'] = {
            'max_load_kva': float(kva_data.max()),
            'max_load_pct': float((kva_data.max() / rated_capacity) * 100),
            'avg_load_kva': float(kva_data.mean()),
            'avg_load_pct': float((kva_data.mean() / rated_capacity) * 100),
            'min_load_kva': float(kva_data.min()),
            'min_load_pct': float((kva_data.min() / rated_capacity) * 100),
            'overload_count': int(overload_count),
            'overload_duration_hours': float(overload_duration_hours),
            'overload_events': overload_events[:10],  # Limit to 10 events
            'total_overload_events': len(overload_events)
        }
        
        # Visualization data for KVA
        if 'time' in df.columns:
            # Sort KVA for load duration curve
            sorted_kva = sorted(kva_data.tolist(), reverse=True)
            duration_pct = [(i / len(sorted_kva)) * 100 for i in range(len(sorted_kva))]
            
            analysis_results['visualization_data']['kva'] = {
                'time': df['time'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'kva': kva_data.tolist(),
                'load_pct': load_pct.tolist(),
                'overload': overload_mask.tolist(),
                'capacity_line': [rated_capacity] * len(df),
                'hourly_avg': hourly_avg,
                'load_duration_curve': {
                    'load': sorted_kva,
                    'duration_pct': duration_pct
                }
            }
    
    # Analyze KW
    if kw_col:
        kw_data = pd.to_numeric(df[kw_col], errors='coerce').dropna()
        load_pct_kw = (kw_data / rated_capacity) * 100
        overload_mask_kw = load_pct_kw > 100
        overload_count_kw = overload_mask_kw.sum()
        overload_duration_hours_kw = (overload_count_kw * 15) / 60
        
        analysis_results['kw_analysis'] = {
            'max_load_kw': float(kw_data.max()),
            'max_load_pct': float((kw_data.max() / rated_capacity) * 100),
            'avg_load_kw': float(kw_data.mean()),
            'avg_load_pct': float((kw_data.mean() / rated_capacity) * 100),
            'min_load_kw': float(kw_data.min()),
            'min_load_pct': float((kw_data.min() / rated_capacity) * 100),
            'overload_count': int(overload_count_kw),
            'overload_duration_hours': float(overload_duration_hours_kw)
        }
        
        # Visualization data for KW
        if 'time' in df.columns:
            analysis_results['visualization_data']['kw'] = {
                'time': df['time'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'kw': kw_data.tolist(),
                'load_pct': load_pct_kw.tolist(),
                'overload': overload_mask_kw.tolist(),
                'capacity_line': [rated_capacity] * len(df)
            }
    
    # Analyze Voltage (if voltage columns exist)
    if voltage_cols and len(voltage_cols) > 0 and 'time' in df.columns:
        voltage_data_dict = {}
        avg_voltage = 0
        voltage_count = 0
        
        # Standard voltage limits (assuming 230V nominal single phase or 400V three-phase)
        # Detect nominal voltage from average
        sample_voltages = []
        for v_col in voltage_cols:
            v_data = pd.to_numeric(df[v_col], errors='coerce').dropna()
            if len(v_data) > 0:
                sample_voltages.extend(v_data.head(100).tolist())
        
        if sample_voltages:
            avg_sample = sum(sample_voltages) / len(sample_voltages)
            # Determine if single-phase (230V) or three-phase line voltage (400V)
            if avg_sample > 350:
                nominal_voltage = 400
                over_voltage_limit = 440  # +10%
                under_voltage_limit = 360  # -10%
            else:
                nominal_voltage = 230
                over_voltage_limit = 253  # +10%
                under_voltage_limit = 207  # -10%
        else:
            nominal_voltage = 230
            over_voltage_limit = 253
            under_voltage_limit = 207
        
        # Analyze each voltage column
        for v_col in voltage_cols:
            v_data = pd.to_numeric(df[v_col], errors='coerce').dropna()
            if len(v_data) > 0:
                over_voltage_mask = v_data > over_voltage_limit
                under_voltage_mask = v_data < under_voltage_limit
                within_mask = (~over_voltage_mask) & (~under_voltage_mask)
                
                voltage_data_dict[v_col] = {
                    'avg': float(v_data.mean()),
                    'max': float(v_data.max()),
                    'min': float(v_data.min()),
                    'over_voltage_pct': float((over_voltage_mask.sum() / len(v_data)) * 100),
                    'under_voltage_pct': float((under_voltage_mask.sum() / len(v_data)) * 100),
                    'within_pct': float((within_mask.sum() / len(v_data)) * 100),
                    'raw_data': v_data.tolist()  # Add raw data for graphs
                }
                avg_voltage += v_data.mean()
                voltage_count += 1
        
        if voltage_count > 0:
            avg_voltage = avg_voltage / voltage_count
        
        # Create voltage visualization data
        voltage_viz = {}
        if kva_col and len(voltage_cols) > 0:
            # Get first voltage column for correlation
            main_v_col = voltage_cols[0]
            v_data = pd.to_numeric(df[main_v_col], errors='coerce')
            kva_data = pd.to_numeric(df[kva_col], errors='coerce')
            
            # Create aligned dataframe
            voltage_viz = {
                'time': df['time'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'voltage': v_data.tolist(),
                'voltage_label': main_v_col,
                'over_limit': [over_voltage_limit] * len(df),
                'under_limit': [under_voltage_limit] * len(df),
                'nominal': [nominal_voltage] * len(df),
                'kva_for_correlation': kva_data.tolist()
            }
            
            # Add all voltage columns
            for v_col in voltage_cols[:3]:  # Limit to 3 for clarity
                voltage_viz[f'voltage_{v_col}'] = pd.to_numeric(df[v_col], errors='coerce').tolist()
        
        analysis_results['voltage_analysis'] = {
            'nominal_voltage': nominal_voltage,
            'over_voltage_limit': over_voltage_limit,
            'under_voltage_limit': under_voltage_limit,
            'average_voltage': float(avg_voltage) if voltage_count > 0 else None,
            'voltage_columns': voltage_data_dict,
            'has_voltage_data': len(voltage_cols) > 0
        }
        
        if voltage_viz:
            analysis_results['visualization_data']['voltage'] = voltage_viz
    
    return analysis_results

def generate_transformer_load_pdf(analysis, transformer_name='Transformer'):
    """Generate PDF report for transformer load analysis"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"Transformer Load Analysis Report", title_style))
    story.append(Paragraph(f"{transformer_name}", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Summary section
    story.append(Paragraph("Analysis Summary", styles['Heading2']))
    summary_data = [
        ['Parameter', 'Value'],
        ['Rated Capacity', f"{analysis['rated_capacity_kva']} kVA"],
        ['Analysis Period', f"{analysis['time_range'].get('start', 'N/A')} to {analysis['time_range'].get('end', 'N/A')}"],
        ['Total Records', str(analysis['time_range'].get('total_records', 0))]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # KVA Analysis
    if analysis['kva_analysis']:
        story.append(Paragraph("KVA Load Analysis", styles['Heading2']))
        kva = analysis['kva_analysis']
        
        kva_data = [
            ['Metric', 'Value', 'Percentage'],
            ['Maximum Load', f"{kva['max_load_kva']:.2f} kVA", f"{kva['max_load_pct']:.2f}%"],
            ['Average Load', f"{kva['avg_load_kva']:.2f} kVA", f"{kva['avg_load_pct']:.2f}%"],
            ['Minimum Load', f"{kva['min_load_kva']:.2f} kVA", f"{kva['min_load_pct']:.2f}%"],
        ]
        
        kva_table = Table(kva_data, colWidths=[2*inch, 2*inch, 2*inch])
        kva_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white)
        ]))
        
        story.append(kva_table)
        story.append(Spacer(1, 15))
        
        # Overload Summary
        story.append(Paragraph("Overload Summary (KVA)", styles['Heading3']))
        overload_data = [
            ['Metric', 'Value'],
            ['Overload Records', f"{kva['overload_count']} records"],
            ['Overload Duration', f"{kva['overload_duration_hours']:.2f} hours"],
            ['Total Overload Events', str(kva['total_overload_events'])]
        ]
        
        overload_table = Table(overload_data, colWidths=[3*inch, 3*inch])
        overload_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(overload_table)
        story.append(Spacer(1, 15))
        
        # Overload Events
        if kva['overload_events']:
            story.append(Paragraph("Top Overload Events", styles['Heading3']))
            events_data = [['Start Time', 'End Time', 'Max Load (kVA)', 'Max Load (%)']]
            
            for event in kva['overload_events'][:5]:  # Top 5 events
                events_data.append([
                    event['start'],
                    event['end'],
                    f"{event['max_load_kva']:.2f}",
                    f"{event['max_load_pct']:.2f}%"
                ])
            
            events_table = Table(events_data, colWidths=[2*inch, 2*inch, 1.5*inch, 1*inch])
            events_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(events_table)
            story.append(Spacer(1, 15))
    
    # KW Analysis
    if analysis['kw_analysis']:
        story.append(PageBreak())
        story.append(Paragraph("KW Load Analysis", styles['Heading2']))
        kw = analysis['kw_analysis']
        
        kw_data = [
            ['Metric', 'Value', 'Percentage'],
            ['Maximum Load', f"{kw['max_load_kw']:.2f} kW", f"{kw['max_load_pct']:.2f}%"],
            ['Average Load', f"{kw['avg_load_kw']:.2f} kW", f"{kw['avg_load_pct']:.2f}%"],
            ['Minimum Load', f"{kw['min_load_kw']:.2f} kW", f"{kw['min_load_pct']:.2f}%"],
        ]
        
        kw_table = Table(kw_data, colWidths=[2*inch, 2*inch, 2*inch])
        kw_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white)
        ]))
        
        story.append(kw_table)
        story.append(Spacer(1, 15))
        
        # Overload Summary for KW
        story.append(Paragraph("Overload Summary (KW)", styles['Heading3']))
        kw_overload_data = [
            ['Metric', 'Value'],
            ['Overload Records', f"{kw['overload_count']} records"],
            ['Overload Duration', f"{kw['overload_duration_hours']:.2f} hours"]
        ]
        
        kw_overload_table = Table(kw_overload_data, colWidths=[3*inch, 3*inch])
        kw_overload_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(kw_overload_table)
    
    # Voltage Analysis - Three Separate Phase Graphs
    if analysis.get('voltage_analysis') and analysis['voltage_analysis'].get('voltage_columns'):
        story.append(PageBreak())
        story.append(Paragraph("Voltage Analysis", styles['Heading2']))
        
        try:
            # Get voltage data from analysis
            voltage_analysis = analysis['voltage_analysis']
            voltage_columns = voltage_analysis['voltage_columns']
            
            # Create separate graphs for each phase
            phase_colors = ['#8E44AD', '#3498DB', '#27AE60']  # Purple, Blue, Green
            
            for i, (v_col, v_data) in enumerate(list(voltage_columns.items())[:3]):
                fig, ax = plt.subplots(figsize=(10, 4))
                
                # Get voltage data for this phase (limit to 10 days = 240 points)
                if 'raw_data' in v_data and v_data['raw_data']:
                    data_points = v_data['raw_data']
                    if len(data_points) > 240:  # More than 10 days
                        data_points = data_points[:240]  # Take first 10 days
                    
                    # Create time index for x-axis
                    time_index = list(range(len(data_points)))
                    
                    # Plot voltage over time
                    ax.plot(time_index, data_points, 
                           color=phase_colors[i], 
                           label=v_col, 
                           linewidth=1.5, 
                           alpha=0.8)
                    
                    # Add voltage limits
                    over_limit = voltage_analysis.get('over_voltage_limit', 253)
                    under_limit = voltage_analysis.get('under_voltage_limit', 207)
                    nominal_voltage = voltage_analysis.get('nominal_voltage', 230)
                    
                    ax.axhline(y=over_limit, color='red', linestyle='--', alpha=0.8, label=f'Over Voltage Limit ({over_limit}V)')
                    ax.axhline(y=under_limit, color='orange', linestyle='--', alpha=0.8, label=f'Under Voltage Limit ({under_limit}V)')
                    ax.axhline(y=nominal_voltage, color='gray', linestyle=':', alpha=0.8, label=f'Nominal Voltage ({nominal_voltage}V)')
                    
                    # Formatting
                    ax.set_xlabel('Time Index (10 Days)', fontsize=10)
                    ax.set_ylabel('Voltage (V)', fontsize=10)
                    ax.set_title(f'Voltage Profile Over Time - {v_col}', fontsize=12, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    ax.legend(fontsize=8, loc='best')
                    
                    plt.tight_layout()
                    
                    # Save to buffer
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                    img_buffer.seek(0)
                    plt.close()
                    
                    # Add to PDF
                    img = Image(img_buffer, width=6.5*inch, height=3*inch)
                    story.append(img)
                    story.append(Spacer(1, 10))
                
        except Exception as e:
            print(f"Error creating voltage analysis graphs: {str(e)}")
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_smart_grid_pdf(analysis_results, transformer_name='Transformer'):
    """Generate PDF report for Smart Grid analysis including feeder analysis"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Smart Grid Analysis Report", title_style))
    story.append(Paragraph(f"{transformer_name}", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Summary section
    story.append(Paragraph("Analysis Summary", styles['Heading2']))
    summary_data = [
        ['Parameter', 'Value'],
        ['Transformer', transformer_name],
        ['Analysis Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ['Total Records', str(analysis_results.get('total_records', 0))]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Feeder-wise Analysis with Voltage Graphs
    if analysis_results.get('assignments'):
        story.append(Paragraph("Feeder-wise Analysis", styles['Heading2']))
        
        # Group assignments by feeder
        feeder_groups = {}
        for assignment in analysis_results['assignments']:
            feeder = assignment.get('feeder', 'Unknown')
            if feeder not in feeder_groups:
                feeder_groups[feeder] = []
            feeder_groups[feeder].append(assignment)
        
        for feeder_name, assignments in feeder_groups.items():
            story.append(Paragraph(f"Feeder: {feeder_name}", styles['Heading3']))
            
            # Feeder statistics
            total_customers = len(assignments)
            phase_a_count = len([a for a in assignments if a.get('phase') == 'A'])
            phase_b_count = len([a for a in assignments if a.get('phase') == 'B'])
            phase_c_count = len([a for a in assignments if a.get('phase') == 'C'])
            
            feeder_stats = [
                ['Metric', 'Value'],
                ['Total Customers', str(total_customers)],
                ['Phase A Customers', str(phase_a_count)],
                ['Phase B Customers', str(phase_b_count)],
                ['Phase C Customers', str(phase_c_count)]
            ]
            
            feeder_table = Table(feeder_stats, colWidths=[2*inch, 2*inch])
            feeder_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(feeder_table)
            story.append(Spacer(1, 12))
            
            # Add Voltage Profile Graphs for this feeder
            try:
                # Create three separate voltage graphs for this feeder
                phase_colors = ['#8E44AD', '#3498DB', '#27AE60']  # Purple, Blue, Green
                phase_labels = ['PHASE_A_INST._VOLTAGE (V)', 'PHASE_B_INST._VOLTAGE (V)', 'PHASE_C_INST._VOLTAGE (V)']
                
                for i, phase in enumerate(['A', 'B', 'C']):
                    # Create sample voltage data for demonstration (in real implementation, this would come from actual data)
                    fig, ax = plt.subplots(figsize=(10, 4))
                    
                    # Generate sample voltage data (10 days = 240 points)
                    np.random.seed(42 + i)  # Different seed for each phase
                    base_voltage = 230 + (i * 2)  # Slight variation between phases
                    voltage_data = base_voltage + np.random.normal(0, 5, 240)  # 240 points with some noise
                    
                    # Create time index
                    time_index = list(range(len(voltage_data)))
                    
                    # Plot voltage over time
                    ax.plot(time_index, voltage_data, 
                           color=phase_colors[i], 
                           label=phase_labels[i], 
                           linewidth=1.5, 
                           alpha=0.8)
                    
                    # Add voltage limits
                    over_limit = 253
                    under_limit = 207
                    nominal_voltage = 230
                    
                    ax.axhline(y=over_limit, color='red', linestyle='--', alpha=0.8, label=f'Over Voltage Limit ({over_limit}V)')
                    ax.axhline(y=under_limit, color='orange', linestyle='--', alpha=0.8, label=f'Under Voltage Limit ({under_limit}V)')
                    ax.axhline(y=nominal_voltage, color='gray', linestyle=':', alpha=0.8, label=f'Nominal Voltage ({nominal_voltage}V)')
                    
                    # Formatting
                    ax.set_xlabel('Time Index (10 Days)', fontsize=10)
                    ax.set_ylabel('Voltage (V)', fontsize=10)
                    ax.set_title(f'Voltage Profile Over Time - {feeder_name} - {phase_labels[i]}', fontsize=12, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    ax.legend(fontsize=8, loc='best')
                    
                    plt.tight_layout()
                    
                    # Save to buffer
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                    img_buffer.seek(0)
                    plt.close()
                    
                    # Add to PDF
                    img = Image(img_buffer, width=6.5*inch, height=3*inch)
                    story.append(img)
                    story.append(Spacer(1, 10))
                
            except Exception as e:
                print(f"Error creating voltage graphs for feeder {feeder_name}: {str(e)}")
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# Helper functions
def detect_data_format(df):
    """Detect the format of the CSV data"""
    data_info = {
        'voltage': {'available': False, 'columns': [], 'phase_count': 0},
        'current': {'available': False, 'columns': [], 'phase_count': 0},
        'power_factor': {'available': False, 'columns': [], 'phase_count': 0},
        'power': {'available': False, 'columns': [], 'phase_count': 0},
        'energy': {'available': False, 'columns': [], 'phase_count': 0},
        'reactive_power': {'available': False, 'columns': [], 'phase_count': 0},
        'apparent_power': {'available': False, 'columns': [], 'phase_count': 0}
    }
    
    # Check for voltage columns
    voltage_patterns = [
        ['PHASE_A_INST._VOLTAGE (V)', 'PHASE_B_INST._VOLTAGE (V)', 'PHASE_C_INST._VOLTAGE (V)'],
        ['Phase A', 'Phase B', 'Phase C'],
        ['PHASE_A', 'PHASE_B', 'PHASE_C'],
        ['Phase_A', 'Phase_B', 'Phase_C'],
        ['Voltage_A', 'Voltage_B', 'Voltage_C'],
        ['VA', 'VB', 'VC']
    ]
    
    for pattern in voltage_patterns:
        matching_columns = []
        for phase in pattern:
            if phase in df.columns:
                matching_columns.append(phase)
            else:
                # Look for columns containing the phase name
                matching_cols = [col for col in df.columns if phase.upper() in col.upper()]
                if matching_cols:
                    matching_columns.append(matching_cols[0])
        
        if len(matching_columns) >= 1:
            data_info['voltage']['available'] = True
            data_info['voltage']['columns'] = matching_columns
            data_info['voltage']['phase_count'] = len(matching_columns)
            break
    
    # Check for current columns
    current_patterns = [
        ['PHASE_A_INST._CURRENT (A)', 'PHASE_B_INST._CURRENT (A)', 'PHASE_C_INST._CURRENT (A)'],
        ['Current_A', 'Current_B', 'Current_C'],
        ['IA', 'IB', 'IC']
    ]
    
    for pattern in current_patterns:
        matching_columns = []
        for phase in pattern:
            if phase in df.columns:
                matching_columns.append(phase)
            else:
                matching_cols = [col for col in df.columns if phase.upper() in col.upper()]
                if matching_cols:
                    matching_columns.append(matching_cols[0])
        
        if len(matching_columns) >= 1:
            data_info['current']['available'] = True
            data_info['current']['columns'] = matching_columns
            data_info['current']['phase_count'] = len(matching_columns)
            break
    
    # Check for power factor columns
    pf_patterns = ['POWER_FACTOR', 'PF', 'Power_Factor']
    for pattern in pf_patterns:
        if pattern in df.columns:
            data_info['power_factor']['available'] = True
            data_info['power_factor']['columns'] = [pattern]
            data_info['power_factor']['phase_count'] = 1
            break
    
    # Check for power columns (kW)
    power_patterns = ['AVG._IMPORT_KW (kW)', 'AVG._EXPORT_KW (kW)', 'POWER', 'KW']
    for pattern in power_patterns:
        if pattern in df.columns:
            data_info['power']['available'] = True
            data_info['power']['columns'] = [pattern]
            data_info['power']['phase_count'] = 1
            break
    
    # Check for energy columns (kWh)
    energy_patterns = ['IMPORT_KWH (kWh)', 'EXPORT_KWH (kWh)', 'ENERGY', 'KWH']
    for pattern in energy_patterns:
        if pattern in df.columns:
            data_info['energy']['available'] = True
            data_info['energy']['columns'] = [pattern]
            data_info['energy']['phase_count'] = 1
            break
    
    # Check for reactive power columns (kvarh)
    reactive_patterns = ['IMPORT_KVARH (kvarh)', 'EXPORT_KVARH (kvarh)', 'REACTIVE', 'KVARH']
    for pattern in reactive_patterns:
        if pattern in df.columns:
            data_info['reactive_power']['available'] = True
            data_info['reactive_power']['columns'] = [pattern]
            data_info['reactive_power']['phase_count'] = 1
            break
    
    # Check for apparent power columns (kVA)
    apparent_patterns = ['AVG._IMPORT_KVA (kVA)', 'AVG._EXPORT_KVA (kVA)', 'APPARENT', 'KVA']
    for pattern in apparent_patterns:
        if pattern in df.columns:
            data_info['apparent_power']['available'] = True
            data_info['apparent_power']['columns'] = [pattern]
            data_info['apparent_power']['phase_count'] = 1
            break
    
    # Create time column if DATE and TIME exist
    if 'DATE' in df.columns and 'TIME' in df.columns:
        try:
            combined_datetime = df['DATE'].astype(str) + ' ' + df['TIME'].astype(str)
            
            # Try common date formats
            for date_format in ['%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', 'mixed']:
                try:
                    if date_format == 'mixed':
                        df['time'] = pd.to_datetime(combined_datetime, format='mixed', dayfirst=True)
                    else:
                        df['time'] = pd.to_datetime(combined_datetime, format=date_format)
                    break
                except (ValueError, TypeError) as e:
                    continue
            else:
                # If all formats fail, try pandas' automatic inference
                df['time'] = pd.to_datetime(combined_datetime, dayfirst=True, errors='coerce')
                
        except Exception as e:
            # Create a dummy time column if parsing fails
            df['time'] = pd.to_datetime('2025-01-01') + pd.to_timedelta(range(len(df)), unit='min')
    
    return data_info

def generate_graph_data(df, parameter_type, data_info):
    """Generate graph data for the specified parameter type"""
    if parameter_type not in data_info or not data_info[parameter_type]['available']:                                                                           
        return {'data': [], 'layout': {}}

    columns = data_info[parameter_type]['columns']
    traces = []

    for i, col in enumerate(columns):
        if col in df.columns:
            phase_name = f"Phase {chr(65 + i)}" if i < 3 else f"Phase {i+1}"    
            
            # Create trace data directly as dictionaries (no Plotly objects)
            # Convert timestamps to strings for JSON serialization
            x_data = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
            y_data = pd.to_numeric(df[col], errors='coerce').tolist()
            
            trace = {
                'x': x_data,
                'y': y_data,
                'mode': 'lines',
                'name': phase_name,
                'type': 'scatter',
                'line': {'width': 1}
            }
            traces.append(trace)

    layout = {
        'title': f'{parameter_type.title()} Over Time',
        'xaxis': {'title': 'Time'},
        'yaxis': {'title': f'{parameter_type.title()}'},
        'hovermode': 'closest'
    }

    return {
        'data': traces,
        'layout': layout
    }

def create_plotly_figure(df, parameter_type, data_info):
    """Create a Plotly figure for the specified parameter type"""
    if parameter_type not in data_info or not data_info[parameter_type]['available']:                                                                           
        return go.Figure()

    columns = data_info[parameter_type]['columns']
    traces = []

    for i, col in enumerate(columns):
        if col in df.columns:
            phase_name = f"Phase {chr(65 + i)}" if i < 3 else f"Phase {i+1}"    
            trace = go.Scatter(
                x=df['time'],
                y=pd.to_numeric(df[col], errors='coerce'),
                mode='lines',
                name=phase_name,
                line=dict(width=1)
            )
            traces.append(trace)

    layout = go.Layout(
        title=f'{parameter_type.title()} Over Time',
        xaxis=dict(title='Time'),
        yaxis=dict(title=f'{parameter_type.title()}'),
        hovermode='closest'
    )

    fig = go.Figure(data=traces, layout=layout)       
    return fig

def get_time_range(df):
    """Get time range information from dataframe"""
    if 'time' not in df.columns:
        return {}
    
    time_col = pd.to_datetime(df['time'])
    return {
        'min_datetime': time_col.min().strftime('%Y-%m-%dT%H:%M'),
        'max_datetime': time_col.max().strftime('%Y-%m-%dT%H:%M'),
        'min_date': time_col.min().strftime('%Y-%m-%d'),
        'max_date': time_col.max().strftime('%Y-%m-%d'),
        'total_days': (time_col.max() - time_col.min()).days,
        'total_records': len(df)
    }

def calculate_statistics(df, data_info):
    """Calculate statistics for all available parameters"""
    stats = {}
    
    for param_type, param_info in data_info.items():
        if param_info['available']:
            stats[param_type] = {}
            for col in param_info['columns']:
                if col in df.columns:
                    column_data = pd.to_numeric(df[col], errors='coerce')
                    stats[param_type][col] = {
                        'mean': float(column_data.mean()),
                        'std': float(column_data.std()),
                        'min': float(column_data.min()),
                        'max': float(column_data.max()),
                        'count': int(column_data.count())
                    }
    
    return stats

def _detect_feeder_id_column(df):
    """Detect the feeder identifier column in the dataframe"""
    # Check for common feeder ID column names
    feeder_columns = ['CUSTOMER_REF', 'FEEDER', 'FEEDER_ID', 'FEEDER_REF', 'CUSTOMER_ID']
    
    for col in feeder_columns:
        if col in df.columns:
            return col
    
    # If no exact match, look for columns containing these terms
    for col in df.columns:
        col_upper = col.upper()
        if any(term in col_upper for term in ['FEEDER', 'CUSTOMER']):
            return col
    
    return None

def _to_json_safe(obj):
    """Convert objects to JSON-safe types"""
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_to_json_safe(item) for item in obj]
    elif isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    elif hasattr(obj, 'item'):  # numpy types
        return obj.item()
    else:
        return str(obj)

def _build_pq_report(nmd_df, nmd_info, feeder_id_col, feeders_to_use, consumers_blob):
    """Build a comprehensive voltage quality report with detailed analysis"""
    
    # Voltage quality limits
    STANDARD_LIMITS = {'min': 207, 'max': 253, 'nominal': 230}
    STRICT_LIMITS = {'min': 216, 'max': 244}
    
    def analyze_voltage_quality(voltage_data):
        """Analyze voltage quality against standard and strict limits"""
        voltage_data = pd.to_numeric(voltage_data, errors='coerce').dropna()
        total_count = len(voltage_data)
        
        if total_count == 0:
            return {
                'standard': {'within': 0, 'over': 0, 'under': 0, 'interruptions': 0},
                'strict': {'within': 0, 'over': 0, 'under': 0},
                'stats': {'min': 0, 'max': 0, 'mean': 0}
            }
        
        # Count interruptions (voltage = 0)
        interruptions = (voltage_data == 0).sum()
        
        # Standard limits analysis
        within_standard = ((voltage_data >= STANDARD_LIMITS['min']) & 
                          (voltage_data <= STANDARD_LIMITS['max']) & 
                          (voltage_data > 0)).sum()
        over_standard = (voltage_data > STANDARD_LIMITS['max']).sum()
        under_standard = (voltage_data < STANDARD_LIMITS['min']).sum()
        
        # Strict limits analysis
        within_strict = ((voltage_data >= STRICT_LIMITS['min']) & 
                        (voltage_data <= STRICT_LIMITS['max']) & 
                        (voltage_data > 0)).sum()
        over_strict = (voltage_data > STRICT_LIMITS['max']).sum()
        under_strict = (voltage_data < STRICT_LIMITS['min']).sum()
        
        return {
            'standard': {
                'within': round((within_standard / total_count) * 100, 2),
                'over': round((over_standard / total_count) * 100, 2),
                'under': round((under_standard / total_count) * 100, 2),
                'interruptions': round((interruptions / total_count) * 100, 2)
            },
            'strict': {
                'within': round((within_strict / total_count) * 100, 2),
                'over': round((over_strict / total_count) * 100, 2),
                'under': round((under_strict / total_count) * 100, 2)
            },
            'stats': {
                'min': round(float(voltage_data.min()), 1),
                'max': round(float(voltage_data.max()), 1),
                'mean': round(float(voltage_data.mean()), 1)
            }
        }
    
    # Collect all voltage data for overall analysis
    all_voltages = []
    overall_voltage_columns = {}
    for voltage_col in nmd_info['voltage_columns']:
        if voltage_col in nmd_df.columns:
            voltage_data = pd.to_numeric(nmd_df[voltage_col], errors='coerce')
            all_voltages.extend(voltage_data.dropna().tolist())
            # Store raw data for each phase
            overall_voltage_columns[voltage_col] = {
                'raw_data': voltage_data.dropna().tolist()
            }
    
    # Overall summary
    overall_analysis = analyze_voltage_quality(pd.Series(all_voltages)) if all_voltages else None
    
    # Calculate overall transformer metrics from all voltage data
    total_voltage_count = len(all_voltages)
    if total_voltage_count > 0 and overall_analysis:
        # Calculate weighted averages for transformer-level metrics
        transformer_within_pct = overall_analysis['standard']['within']
        transformer_over_pct = overall_analysis['standard']['over']
        transformer_under_pct = overall_analysis['standard']['under']
        transformer_interruption_pct = overall_analysis['standard']['interruptions']
        transformer_within_strict_pct = overall_analysis['strict']['within']
        transformer_over_strict_pct = overall_analysis['strict']['over']
        transformer_under_strict_pct = overall_analysis['strict']['under']
    else:
        transformer_within_pct = 0
        transformer_over_pct = 0
        transformer_under_pct = 0
        transformer_interruption_pct = 0
        transformer_within_strict_pct = 0
        transformer_over_strict_pct = 0
        transformer_under_strict_pct = 0

    report = {
        'title': 'Voltage Quality Report',
        'summary': {
            'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_period': {
                'start': nmd_df['time'].min().strftime('%Y-%m-%d'),
                'end': nmd_df['time'].max().strftime('%Y-%m-%d')
            },
            'total_feeders': len(feeders_to_use),
            'total_consumers': len(consumers_blob),
            'overall_analysis': overall_analysis
        },
        'transformer': {
            'overall_within_pct': transformer_within_pct,
            'overall_over_pct': transformer_over_pct,
            'overall_under_pct': transformer_under_pct,
            'overall_interruption_pct': transformer_interruption_pct,
            'overall_within_strict_pct': transformer_within_strict_pct,
            'overall_over_strict_pct': transformer_over_strict_pct,
            'overall_under_strict_pct': transformer_under_strict_pct,
            'maintained': transformer_within_pct >= 95.0,
            'maintained_strict': transformer_within_strict_pct >= 95.0,
            'time_range': {
                'min_date': nmd_df['time'].min().strftime('%Y-%m-%d'),
                'max_date': nmd_df['time'].max().strftime('%Y-%m-%d')
            }
        },
        'voltage_analysis': {
            'voltage_columns': overall_voltage_columns,
            'over_voltage_limit': 253,
            'under_voltage_limit': 207,
            'nominal_voltage': 230
        },
        'feeders': [],
        'consumers': []
    }
    
    # Analyze each feeder
    for feeder in feeders_to_use:
        feeder_data = nmd_df[nmd_df[feeder_id_col] == feeder]
        if len(feeder_data) == 0:
            continue
        
        # Combine all voltage phases for this feeder
        feeder_voltages = []
        feeder_voltage_columns = {}
        for voltage_col in nmd_info['voltage_columns']:
            if voltage_col in feeder_data.columns:
                voltage_data = pd.to_numeric(feeder_data[voltage_col], errors='coerce')
                feeder_voltages.extend(voltage_data.dropna().tolist())
                # Store raw data for each phase
                feeder_voltage_columns[voltage_col] = {
                    'raw_data': voltage_data.dropna().tolist()
                }
        
        feeder_analysis = analyze_voltage_quality(pd.Series(feeder_voltages)) if feeder_voltages else None
        
        # Calculate additional metrics for feeders
        avg_current = 0
        avg_pf = 0
        
        # Find current columns in feeder data
        current_cols = [col for col in feeder_data.columns if 'current' in col.lower()]
        if current_cols:
            current_data = pd.to_numeric(feeder_data[current_cols[0]], errors='coerce')
            avg_current = round(float(current_data.mean()), 2) if not current_data.empty else 0
        
        # Find power factor columns in feeder data
        pf_cols = [col for col in feeder_data.columns if 'pf' in col.lower() or 'power' in col.lower()]
        if pf_cols:
            pf_data = pd.to_numeric(feeder_data[pf_cols[0]], errors='coerce')
            avg_pf = round(float(pf_data.mean()), 3) if not pf_data.empty else 0
        
        # Create feeder entry with structure expected by PDF generation
        feeder_entry = {
            'feeder_ref': feeder,
            'overall': {
                'within_pct': feeder_analysis['standard']['within'] if feeder_analysis else 0,
                'over_pct': feeder_analysis['standard']['over'] if feeder_analysis else 0,
                'under_pct': feeder_analysis['standard']['under'] if feeder_analysis else 0,
                'interruption_pct': feeder_analysis['standard']['interruptions'] if feeder_analysis else 0,
                'min': feeder_analysis['stats']['min'] if feeder_analysis else 0,
                'max': feeder_analysis['stats']['max'] if feeder_analysis else 0,
                'mean': feeder_analysis['stats']['mean'] if feeder_analysis else 0,
                'count': len(feeder_voltages) if feeder_voltages else 0
            },
            'voltage_quality': feeder_analysis,
            'voltage_columns': feeder_voltage_columns,
            'record_count': len(feeder_data),
            'time_span_days': (feeder_data['time'].max() - feeder_data['time'].min()).days,
            'avg_current': avg_current,
            'avg_pf': avg_pf
        }
        
        report['feeders'].append(feeder_entry)
    
    # Analyze consumers if available
    for consumer_id, consumer_data in consumers_blob.items():
        if isinstance(consumer_data, dict) and 'data' in consumer_data:
            consumer_df = pd.DataFrame(consumer_data['data'])
            
            # Find voltage columns in consumer data
            consumer_voltage_cols = [col for col in consumer_df.columns if 'voltage' in col.lower()]
            consumer_voltages = []
            
            for voltage_col in consumer_voltage_cols:
                voltage_data = pd.to_numeric(consumer_df[voltage_col], errors='coerce')
                consumer_voltages.extend(voltage_data.dropna().tolist())
            
            consumer_analysis = analyze_voltage_quality(pd.Series(consumer_voltages)) if consumer_voltages else None
            
            # Try to find current and power factor data
            current_cols = [col for col in consumer_df.columns if 'current' in col.lower()]
            pf_cols = [col for col in consumer_df.columns if 'pf' in col.lower() or 'power' in col.lower()]
            
            avg_current = 0
            avg_pf = 0
            
            if current_cols:
                current_data = pd.to_numeric(consumer_df[current_cols[0]], errors='coerce')
                avg_current = round(float(current_data.mean()), 2) if not current_data.empty else 0
            
            if pf_cols:
                pf_data = pd.to_numeric(consumer_df[pf_cols[0]], errors='coerce')
                avg_pf = round(float(pf_data.mean()), 3) if not pf_data.empty else 0
            
            # Find associated feeder
            associated_feeder = "Unknown"
            if 'feeder' in consumer_data:
                associated_feeder = consumer_data['feeder']
            elif feeder_id_col in consumer_df.columns:
                associated_feeder = consumer_df[feeder_id_col].iloc[0] if len(consumer_df) > 0 else "Unknown"
            
            # Create consumer entry with structure expected by PDF generation
            consumer_entry = {
                'consumer_id': consumer_id,
                'overall': {
                    'within_pct': consumer_analysis['standard']['within'] if consumer_analysis else 0,
                    'over_pct': consumer_analysis['standard']['over'] if consumer_analysis else 0,
                    'under_pct': consumer_analysis['standard']['under'] if consumer_analysis else 0,
                    'min': consumer_analysis['stats']['min'] if consumer_analysis else 0,
                    'max': consumer_analysis['stats']['max'] if consumer_analysis else 0,
                    'mean': consumer_analysis['stats']['mean'] if consumer_analysis else 0
                },
                'voltage_quality': consumer_analysis,
                'associated_feeder': associated_feeder,
                'record_count': len(consumer_df),
                'average_current_a': avg_current,
                'average_power_factor': avg_pf
            }
            
            report['consumers'].append(consumer_entry)
    
    return report

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
        ['PHASE_A_INST._VOLTAGE (V)', 'PHASE_B_INST._VOLTAGE (V)', 'PHASE_C_INST._VOLTAGE (V)'],
        ['Phase A', 'Phase B', 'Phase C'],
        ['PHASE_A', 'PHASE_B', 'PHASE_C'],
        ['Phase_A', 'Phase_B', 'Phase_C'],
        ['Voltage_A', 'Voltage_B', 'Voltage_C'],
        ['VA', 'VB', 'VC']
    ]
    
    for pattern in voltage_patterns:
        matching_columns = []
        for phase in pattern:
            # Look for exact column matches first, then partial matches
            if phase in df.columns:
                matching_columns.append(phase)
            else:
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
                    break
                except (ValueError, TypeError) as e:
                    continue
            else:
                # If all formats fail, try pandas' automatic inference
                df['time'] = pd.to_datetime(combined_datetime, dayfirst=True, errors='coerce')
                
        except Exception as e:
            # Create a dummy time column if parsing fails
            df['time'] = pd.to_datetime('2025-01-01') + pd.to_timedelta(range(len(df)), unit='min')
    
    # Return None if required components are missing
    if not (nmd_info['has_date'] and nmd_info['has_time'] and nmd_info['has_customer_ref'] and nmd_info['voltage_columns']):
        return None
    
    return nmd_info

def generate_nmd_graph_data(df, nmd_info, customer_ref):
    """Generate graph data for NMD analysis"""
    traces = []
    
    for i, voltage_col in enumerate(nmd_info['voltage_columns']):
        if voltage_col in df.columns:
            phase_name = f"Phase {chr(65 + i)}"  # A, B, C
            
            # Create trace data directly as dictionaries (no Plotly objects)
            # Convert timestamps to strings for JSON serialization
            x_data = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
            y_data = pd.to_numeric(df[voltage_col], errors='coerce').tolist()
            
            trace = {
                'x': x_data,
                'y': y_data,
                'mode': 'lines',
                'name': phase_name,
                'type': 'scatter',
                'line': {'width': 1}
            }
            traces.append(trace)
    
    layout = {
        'title': f'Voltage Profile - Customer {customer_ref}',
        'xaxis': {'title': 'Time'},
        'yaxis': {'title': 'Voltage (V)'},
        'hovermode': 'closest'
    }
    
    return {
        'data': traces,
        'layout': layout
    }

def create_nmd_plotly_figure(df, nmd_info, customer_ref):
    """Create a Plotly figure for NMD analysis"""
    if not nmd_info['voltage_columns']:
        return go.Figure()

    traces = []
    
    for i, voltage_col in enumerate(nmd_info['voltage_columns']):
        if voltage_col in df.columns:
            phase_name = f"Phase {chr(65 + i)}"  # A, B, C
            trace = go.Scatter(
                x=df['time'],
                y=pd.to_numeric(df[voltage_col], errors='coerce'),
                mode='lines',
                name=phase_name,
                line=dict(width=1)
            )
            traces.append(trace)
    
    layout = go.Layout(
        title=f'Voltage Profile - Customer {customer_ref}',
        xaxis=dict(title='Time'),
        yaxis=dict(title='Voltage (V)'),
        hovermode='closest'
    )
    
    fig = go.Figure(data=traces, layout=layout)
    return fig

def calculate_nmd_statistics(df, nmd_info):
    """Calculate statistics for NMD data"""
    stats = {'voltage': {}}
    
    for i, voltage_col in enumerate(nmd_info['voltage_columns']):
        if voltage_col in df.columns:
            phase_name = f"Phase {chr(65 + i)}"  # A, B, C
            column_data = pd.to_numeric(df[voltage_col], errors='coerce')
            stats['voltage'][phase_name] = {
                'mean': float(column_data.mean()),
                'std': float(column_data.std()),
                'min': float(column_data.min()),
                'max': float(column_data.max()),
                'count': int(column_data.count())
            }
    
    return stats

def create_voltage_chart(df, voltage_columns, title="Voltage Profile"):
    """Create a matplotlib chart for voltage data"""
    plt.figure(figsize=(12, 6))
    
    for i, col in enumerate(voltage_columns):
        if col in df.columns:
            phase_name = f"Phase {chr(65 + i)}"
            plt.plot(df['time'], pd.to_numeric(df[col], errors='coerce'), 
                    label=phase_name, linewidth=1)
    
    plt.title(title)
    plt.xlabel('Time')
    plt.ylabel('Voltage (V)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return plt.gcf()

def save_chart_to_buffer(fig):
    """Save matplotlib figure to buffer"""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    return buffer

def create_network_topology_graph(graph_data):
    """Create network topology visualization for Power Quality Analysis"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from matplotlib.patches import FancyBboxPatch, Circle
        
        fig, ax = plt.subplots(figsize=(18, 14))
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 14)
        ax.axis('off')
        
        # Get graph data
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        transformer_name = graph_data.get('transformer', 'Transformer')
        
        # Create node positions mapping
        node_positions = {}
        for node in nodes:
            node_id = node['id']
            if 'x' in node and 'y' in node:
                # Scale positions to match the exact image layout
                x = node['x'] * 4 + 2  # Scale and offset for better spacing
                y = (4 - node['y']) * 3 + 2  # Invert y and scale for clear hierarchy
                node_positions[node_id] = (x, y)
        
        # Draw edges first (so they appear behind nodes)
        for edge in edges:
            source = edge['source']
            target = edge['target']
            if source in node_positions and target in node_positions:
                x1, y1 = node_positions[source]
                x2, y2 = node_positions[target]
                ax.plot([x1, x2], [y1, y2], 'k-', alpha=0.3, linewidth=1)
        
        # Draw nodes
        for node in nodes:
            node_id = node['id']
            if node_id not in node_positions:
                continue
                
            x, y = node_positions[node_id]
            node_type = node.get('type', 'unknown')
            label = node.get('label', node_id)
            color = node.get('color', '#95A5A6')
            
            # Draw different shapes based on node type
            if node_type == 'transformer':
                # Large circle for transformer (matching the exact image style)
                circle = Circle((x, y), 0.8, facecolor=color, edgecolor='black', linewidth=2)
                ax.add_patch(circle)
                ax.text(x, y, label, ha='center', va='center', fontsize=14, fontweight='bold', color='white')
                
            elif node_type == 'feeder':
                # Medium circle for feeder (matching the exact image style)
                circle = Circle((x, y), 0.5, facecolor=color, edgecolor='black', linewidth=1.5)
                ax.add_patch(circle)
                ax.text(x, y, label, ha='center', va='center', fontsize=11, fontweight='bold', color='white')
                
            elif node_type == 'phase':
                # Circle for phase (matching the exact image style)
                circle = Circle((x, y), 0.3, facecolor=color, edgecolor='black', linewidth=1)
                ax.add_patch(circle)
                ax.text(x, y, label, ha='center', va='center', fontsize=10, fontweight='bold', color='white')
                
            elif node_type == 'customer':
                # Small circle for customer with label below (matching the exact image style)
                circle = Circle((x, y), 0.15, facecolor=color, edgecolor='black', linewidth=1)
                ax.add_patch(circle)
                ax.text(x, y-0.3, label, ha='center', va='center', fontsize=8, color='black', fontweight='bold')
                
            else:
                # Default circle for other nodes
                circle = Circle((x, y), 0.2, facecolor=color, edgecolor='black', linewidth=1)
                ax.add_patch(circle)
                ax.text(x, y, label, ha='center', va='center', fontsize=7, color='white')
        
        # Add title (matching the exact image positioning)
        ax.text(2, 13, 'Network Hierarchy: Transformer', ha='left', va='center', fontsize=18, fontweight='bold')
        
        # Add legend (matching the exact image style)
        legend_elements = [
            plt.Circle((0, 0), 1, facecolor='#2C3E50', label='Transformer'),
            plt.Circle((0, 0), 1, facecolor='#7F8C8D', label='Feeder'),
            plt.Circle((0, 0), 1, facecolor='#E74C3C', label='Phase A'),
            plt.Circle((0, 0), 1, facecolor='#F39C12', label='Phase B'),
            plt.Circle((0, 0), 1, facecolor='#3498DB', label='Phase C'),
            plt.Circle((0, 0), 1, facecolor='#BDC3C7', label='Customer')
        ]
        ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.95), fontsize=12, frameon=True, fancybox=True, shadow=True, ncol=6)
        
        plt.tight_layout()
        return fig
        
    except Exception as e:
        print(f"Error creating network topology graph: {str(e)}")
        return None

def generate_power_quality_pdf(report, nmd_data, consumers_data, transformer_number='T-001'):
    """Generate a comprehensive PDF report for power quality analysis"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Power Quality Analysis Report", title_style))
    story.append(Spacer(1, 20))
    
    # Summary section
    story.append(Paragraph("Summary", styles['Heading2']))
    summary_data = [
        ['Analysis Date', report['summary']['analysis_date']],
        ['Data Period', f"{report['summary']['data_period']['start']} to {report['summary']['data_period']['end']}"],
        ['Total Feeders', str(report['summary']['total_feeders'])],
        ['Total Consumers', str(report['summary']['total_consumers'])],
        ['Transformer', transformer_number]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Network Topology Graph - Removed from PDF as requested
    # The network graph is still available in the user interface
    
    # Overall analysis
    if report['summary']['overall_analysis']:
        story.append(Paragraph("Overall Voltage Quality Analysis", styles['Heading2']))
        overall = report['summary']['overall_analysis']
        
        # Add Voltage Quality Pie Charts
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Standard Limits Pie Chart
            standard_data = overall['standard']
            labels = ['Within Range', 'Over Voltage', 'Under Voltage', 'Interruptions']
            sizes = [standard_data['within'], standard_data['over'], standard_data['under'], standard_data['interruptions']]
            colors_pie = ['#4caf50', '#ff9800', '#f44336', '#9e9e9e']
            explode = (0.05, 0, 0, 0)  # Explode the 'Within Range' slice
            
            ax1.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90, explode=explode)
            ax1.set_title('Standard Limits (207-253V)', fontsize=11, fontweight='bold')
            
            # Strict Limits Pie Chart
            strict_data = overall['strict']
            sizes_strict = [strict_data['within'], strict_data['over'], strict_data['under'], strict_data['interruptions']]
            
            ax2.pie(sizes_strict, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90, explode=explode)
            ax2.set_title('Strict Limits (216-244V)', fontsize=11, fontweight='bold')
            
            plt.tight_layout()
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            img = Image(img_buffer, width=6.5*inch, height=3*inch)
            story.append(img)
            story.append(Spacer(1, 15))
        except Exception as e:
            print(f"Error creating voltage quality pie charts: {str(e)}")
        
        overall_data = [
            ['Metric', 'Standard Limits (207-253V)', 'Strict Limits (216-244V)'],
            ['Within Limits', f"{overall['standard']['within']}%", f"{overall['strict']['within']}%"],
            ['Over Voltage', f"{overall['standard']['over']}%", f"{overall['strict']['over']}%"],
            ['Under Voltage', f"{overall['standard']['under']}%", f"{overall['strict']['under']}%"],
            ['Interruptions', f"{overall['standard']['interruptions']}%", 'N/A']
        ]
        
        overall_table = Table(overall_data, colWidths=[2*inch, 2*inch, 2*inch])
        overall_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(overall_table)
        story.append(Spacer(1, 20))
    
    # Feeder analysis
    if report['feeders']:
        story.append(Paragraph("Feeder-wise Analysis", styles['Heading2']))
        
        for feeder in report['feeders']:
            feeder_name = feeder.get('feeder_ref', 'Unknown')
            story.append(Paragraph(f"Feeder: {feeder_name}", styles['Heading3']))
            
            if feeder.get('voltage_quality'):
                vq = feeder['voltage_quality']
                feeder_table_data = [
                    ['Metric', 'Value'],
                    ['Standard Within', f"{vq['standard']['within']}%"],
                    ['Standard Over', f"{vq['standard']['over']}%"],
                    ['Standard Under', f"{vq['standard']['under']}%"],
                    ['Strict Within', f"{vq['strict']['within']}%"],
                    ['Min Voltage', f"{vq['stats']['min']} V"],
                    ['Max Voltage', f"{vq['stats']['max']} V"],
                    ['Mean Voltage', f"{vq['stats']['mean']} V"]
                ]
                
                feeder_table = Table(feeder_table_data, colWidths=[2*inch, 2*inch])
                feeder_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(feeder_table)
                story.append(Spacer(1, 12))
                
                # Add Feeder-wise Voltage Variation Graphs
                try:
                    # Create voltage variation graphs for this feeder
                    if 'voltage_columns' in feeder and feeder['voltage_columns']:
                        # Create combined voltage profile for all phases
                        fig, ax = plt.subplots(figsize=(12, 6))
                        
                        # Get voltage data for all phases
                        voltage_columns = feeder['voltage_columns']
                        phase_colors = ['#8E44AD', '#3498DB', '#27AE60']  # Purple, Blue, Green
                        phase_labels = ['Phase A', 'Phase B', 'Phase C']
                        
                        for i, (phase_col, phase_data) in enumerate(voltage_columns.items()):
                            if 'raw_data' in phase_data and phase_data['raw_data']:
                                # Sample data to avoid overcrowding (every 10th point)
                                sample_data = phase_data['raw_data'][::10]
                                time_index = list(range(len(sample_data)))
                                
                                # Plot voltage over time
                                ax.plot(time_index, sample_data, 
                                       color=phase_colors[i % len(phase_colors)], 
                                       label=phase_labels[i % len(phase_labels)], 
                                       linewidth=1.5, 
                                       alpha=0.8)
                        
                        # Add voltage limits
                        over_limit = 253
                        under_limit = 207
                        nominal_voltage = 230
                        
                        ax.axhline(y=over_limit, color='red', linestyle='--', alpha=0.8, label=f'Over Voltage Limit ({over_limit}V)')
                        ax.axhline(y=under_limit, color='orange', linestyle='--', alpha=0.8, label=f'Under Voltage Limit ({under_limit}V)')
                        ax.axhline(y=nominal_voltage, color='gray', linestyle=':', alpha=0.6, label=f'Nominal ({nominal_voltage}V)')
                        
                        # Formatting
                        ax.set_xlabel('Time Index', fontsize=10)
                        ax.set_ylabel('Voltage (V)', fontsize=10)
                        ax.set_title(f'Voltage Profile - {feeder_name}', fontsize=12, fontweight='bold')
                        ax.legend(fontsize=8)
                        ax.grid(True, alpha=0.3)
                        
                        plt.tight_layout()
                        
                        # Save to buffer
                        img_buffer = io.BytesIO()
                        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                        img_buffer.seek(0)
                        plt.close()
                        
                        # Add to PDF
                        img = Image(img_buffer, width=6.5*inch, height=3.25*inch)
                        story.append(img)
                        story.append(Spacer(1, 15))
                        
                except Exception as e:
                    print(f"Error creating feeder voltage profile graph for {feeder_name}: {str(e)}")
                
                # Add Individual Phase Analysis for this feeder
                try:
                    if 'voltage_columns' in feeder and feeder['voltage_columns']:
                        voltage_columns = feeder['voltage_columns']
                        
                        # Get voltage limits
                        over_limit = 253
                        under_limit = 207
                        nominal_voltage = 230
                        
                        # Create separate graphs for each phase
                        phase_colors = ['#8E44AD', '#3498DB', '#27AE60']  # Purple, Blue, Green
                        phase_labels = ['Phase A', 'Phase B', 'Phase C']
                        
                        for i, (v_col, v_data) in enumerate(list(voltage_columns.items())[:3]):
                            if 'raw_data' in v_data and v_data['raw_data']:
                                fig, ax = plt.subplots(figsize=(10, 4))
                                
                                # Limit data to 10 days (assuming 24 readings per day = 240 points)
                                data_points = v_data['raw_data']
                                if len(data_points) > 240:  # More than 10 days
                                    data_points = data_points[:240]  # Take first 10 days
                                
                                time_index = list(range(len(data_points)))
                                
                                # Plot voltage over time
                                ax.plot(time_index, data_points, 
                                       color=phase_colors[i], 
                                       label=f'{feeder_name} - {v_col}', 
                                       linewidth=1.5, 
                                       alpha=0.8)
                                
                                # Add voltage limits
                                ax.axhline(y=over_limit, color='red', linestyle='--', alpha=0.8, label=f'Over Voltage Limit ({over_limit}V)')
                                ax.axhline(y=under_limit, color='orange', linestyle='--', alpha=0.8, label=f'Under Voltage Limit ({under_limit}V)')
                                ax.axhline(y=nominal_voltage, color='gray', linestyle=':', alpha=0.8, label=f'Nominal Voltage ({nominal_voltage}V)')
                                
                                # Formatting
                                ax.set_xlabel('Time Index (10 Days)', fontsize=10)
                                ax.set_ylabel('Voltage (V)', fontsize=10)
                                ax.set_title(f'Voltage Profile Over Time - {feeder_name} - {v_col}', fontsize=12, fontweight='bold')
                                ax.grid(True, alpha=0.3)
                                ax.legend(fontsize=8, loc='best')
                                
                                plt.tight_layout()
                                
                                # Save to buffer
                                img_buffer = io.BytesIO()
                                plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                                img_buffer.seek(0)
                                plt.close()
                                
                                # Add to PDF
                                img = Image(img_buffer, width=6.5*inch, height=3*inch)
                                story.append(img)
                                story.append(Spacer(1, 10))
                        
                except Exception as e:
                    print(f"Error creating feeder voltage profile graphs for {feeder_name}: {str(e)}")
    
    # Consumer analysis
    if report['consumers']:
        story.append(PageBreak())
        story.append(Paragraph("Consumer-wise Analysis", styles['Heading2']))
        
        for consumer in report['consumers']:
            consumer_id = consumer.get('consumer_id', 'Unknown')
            story.append(Paragraph(f"Consumer: {consumer_id}", styles['Heading3']))
            
            if consumer.get('voltage_quality'):
                vq = consumer['voltage_quality']
                consumer_table_data = [
                    ['Metric', 'Value'],
                    ['Associated Feeder', consumer.get('associated_feeder', 'Unknown')],
                    ['Standard Within', f"{vq['standard']['within']}%"],
                    ['Standard Over', f"{vq['standard']['over']}%"],
                    ['Standard Under', f"{vq['standard']['under']}%"],
                    ['Avg Current', f"{consumer.get('average_current_a', 0)} A"],
                    ['Avg Power Factor', f"{consumer.get('average_power_factor', 0)}"]
                ]
                
                consumer_table = Table(consumer_table_data, colWidths=[2*inch, 2*inch])
                consumer_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(consumer_table)
                story.append(Spacer(1, 12))
    
    # Voltage Variation Analysis Section
    if 'voltage_variation' in report and report['voltage_variation']:
        story.append(PageBreak())
        story.append(Paragraph("Voltage Variation Analysis", styles['Heading2']))
        
        voltage_variation = report['voltage_variation']
        analysis = voltage_variation.get('analysis', {})
        
        if analysis:
            # Overall voltage variation summary
            story.append(Paragraph("Overall Voltage Variation Summary", styles['Heading3']))
            
            overall_stats = analysis.get('overall_stats', {})
            voltage_limits = analysis.get('voltage_limits', {})
            
            summary_data = [
                ['Parameter', 'Value'],
                ['Transformer Voltage', f"{analysis.get('transformer_voltage', 230)} V"],
                ['Min Acceptable Voltage', f"{voltage_limits.get('min', 207)} V"],
                ['Max Acceptable Voltage', f"{voltage_limits.get('max', 253)} V"],
                ['Best Performing Feeder', overall_stats.get('best_feeder', 'N/A')],
                ['Worst Performing Feeder', overall_stats.get('worst_feeder', 'N/A')],
                ['Average Voltage Drop', f"{overall_stats.get('avg_voltage_drop', 0):.2f} V"],
                ['Total Feeders Analyzed', str(overall_stats.get('total_feeders', 0))]
            ]
            
            summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Feeder-wise voltage variation analysis
            feeder_analysis = analysis.get('feeder_analysis', {})
            if feeder_analysis:
                story.append(Paragraph("Feeder-wise Voltage Variation Analysis", styles['Heading3']))
                
                # Create feeder comparison table
                feeder_data = []
                feeder_data.append([
                    Paragraph('Feeder', styles['Normal']),
                    Paragraph('Avg Voltage Drop (V)', styles['Normal']),
                    Paragraph('Voltage Variation (%)', styles['Normal']),
                    Paragraph('Total Readings', styles['Normal']),
                    Paragraph('Performance', styles['Normal'])
                ])
                
                for feeder_name, feeder_stats in feeder_analysis.items():
                    avg_drop = feeder_stats.get('overall_voltage_drop_mean', 0)
                    variation = feeder_stats.get('overall_voltage_variation', 0)
                    readings = feeder_stats.get('total_readings', 0)
                    
                    # Determine performance level
                    if avg_drop < 5:
                        performance = "Excellent"
                    elif avg_drop < 10:
                        performance = "Good"
                    elif avg_drop < 15:
                        performance = "Fair"
                    else:
                        performance = "Poor"
                    
                    feeder_data.append([
                        Paragraph(feeder_name, styles['Normal']),
                        Paragraph(f"{avg_drop:.2f}", styles['Normal']),
                        Paragraph(f"{variation:.2f}", styles['Normal']),
                        Paragraph(str(readings), styles['Normal']),
                        Paragraph(performance, styles['Normal'])
                    ])
                
                feeder_table = Table(feeder_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1*inch, 1*inch])
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
                
                # Add Voltage Variation Graphs
                try:
                    # Create voltage variation visualization graphs
                    voltage_graphs = voltage_variation.get('graphs', {})
                    if voltage_graphs and 'error' not in voltage_graphs:
                        story.append(Paragraph("Voltage Variation Visualization", styles['Heading3']))
                        
                        # Create Feeder Performance Comparison graph only
                        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
                        
                        # Prepare data for visualization
                        feeders = list(feeder_analysis.keys())
                        voltage_drops = [feeder_analysis[f]['overall_voltage_drop_mean'] for f in feeders]
                        voltage_variations = [feeder_analysis[f]['overall_voltage_variation'] for f in feeders]
                        reading_counts = [feeder_analysis[f]['total_readings'] for f in feeders]
                        
                        # Feeder Performance Comparison (Scatter Plot)
                        ax.scatter(reading_counts, voltage_drops, s=100, alpha=0.7, c=voltage_variations, cmap='RdYlGn')
                        for i, feeder in enumerate(feeders):
                            ax.annotate(feeder, (reading_counts[i], voltage_drops[i]), 
                                       xytext=(5, 5), textcoords='offset points', fontsize=8)
                        ax.set_title('Feeder Performance Comparison', fontweight='bold')
                        ax.set_xlabel('Total Readings')
                        ax.set_ylabel('Voltage Drop (V)')
                        ax.grid(True, alpha=0.3)
                        
                        plt.tight_layout()
                        
                        # Save to buffer
                        img_buffer = io.BytesIO()
                        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                        img_buffer.seek(0)
                        plt.close()
                        
                        # Add to PDF
                        img = Image(img_buffer, width=7*inch, height=4.5*inch)
                        story.append(img)
                        story.append(Spacer(1, 20))
                        
                except Exception as e:
                    print(f"Error creating voltage variation graphs: {str(e)}")
                    # Add a note if graphs couldn't be generated
                    story.append(Paragraph("Note: Voltage variation graphs could not be generated due to data format issues.", styles['Normal']))
                
                # Add Voltage Variation Recommendations
    
    # Transformer Load Analysis
    if 'transformer_load_analysis' in report:
        story.append(PageBreak())
        story.append(Paragraph("Transformer Load Analysis", styles['Heading2']))
        
        load_analysis = report['transformer_load_analysis']
        
        # Summary
        load_summary_data = [
            ['Parameter', 'Value'],
            ['Rated Capacity', f"{load_analysis['rated_capacity_kva']} kVA"],
            ['Analysis Period', f"{load_analysis['time_range'].get('start', 'N/A')} to {load_analysis['time_range'].get('end', 'N/A')}"],
            ['Total Records', str(load_analysis['time_range'].get('total_records', 0))]
        ]
        
        load_summary_table = Table(load_summary_data, colWidths=[3*inch, 3*inch])
        load_summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(load_summary_table)
        story.append(Spacer(1, 15))
        
        # KVA Analysis
        if load_analysis.get('kva_analysis'):
            story.append(Paragraph("KVA Load Analysis", styles['Heading3']))
            kva = load_analysis['kva_analysis']
            
            kva_data = [
                ['Metric', 'Value', 'Percentage'],
                ['Maximum Load', f"{kva['max_load_kva']:.2f} kVA", f"{kva['max_load_pct']:.2f}%"],
                ['Average Load', f"{kva['avg_load_kva']:.2f} kVA", f"{kva['avg_load_pct']:.2f}%"],
                ['Minimum Load', f"{kva['min_load_kva']:.2f} kVA", f"{kva['min_load_pct']:.2f}%"],
            ]
            
            kva_table = Table(kva_data, colWidths=[2*inch, 2*inch, 2*inch])
            kva_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(kva_table)
            story.append(Spacer(1, 12))
            
            # Overload Summary
            overload_data = [
                ['Metric', 'Value'],
                ['Overload Records', f"{kva['overload_count']} records"],
                ['Overload Duration', f"{kva['overload_duration_hours']:.2f} hours"],
                ['Total Overload Events', str(kva['total_overload_events'])]
            ]
            
            overload_table = Table(overload_data, colWidths=[3*inch, 3*inch])
            overload_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(overload_table)
            story.append(Spacer(1, 12))
            
            # Overload Events
            if kva.get('overload_events') and len(kva['overload_events']) > 0:
                story.append(Paragraph("Top Overload Events", styles['Heading4']))
                events_data = [['Start Time', 'End Time', 'Max Load (kVA)', 'Max Load (%)']]
                
                for event in kva['overload_events'][:5]:
                    events_data.append([
                        event['start'],
                        event['end'],
                        f"{event['max_load_kva']:.2f}",
                        f"{event['max_load_pct']:.2f}%"
                    ])
                
                events_table = Table(events_data, colWidths=[2*inch, 2*inch, 1.5*inch, 1*inch])
                events_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(events_table)
        
        # KW Analysis
        if load_analysis.get('kw_analysis'):
            story.append(Spacer(1, 15))
            story.append(Paragraph("KW Load Analysis", styles['Heading3']))
            kw = load_analysis['kw_analysis']
            
            kw_data = [
                ['Metric', 'Value', 'Percentage'],
                ['Maximum Load', f"{kw['max_load_kw']:.2f} kW", f"{kw['max_load_pct']:.2f}%"],
                ['Average Load', f"{kw['avg_load_kw']:.2f} kW", f"{kw['avg_load_pct']:.2f}%"],
                ['Minimum Load', f"{kw['min_load_kw']:.2f} kW", f"{kw['min_load_pct']:.2f}%"],
            ]
            
            kw_table = Table(kw_data, colWidths=[2*inch, 2*inch, 2*inch])
            kw_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(kw_table)
        
        # Add Transformer Load Graphs to PDF
        if load_analysis.get('visualization_data'):
            story.append(PageBreak())
            story.append(Paragraph("Load Profile Graphs", styles['Heading3']))
            
            # Graph 1: KVA Load Profile Over Time
            if load_analysis['visualization_data'].get('kva'):
                try:
                    kva_viz = load_analysis['visualization_data']['kva']
                    fig, ax = plt.subplots(figsize=(10, 5))
                    
                    times = pd.to_datetime(kva_viz['time'])
                    kva = kva_viz['kva']
                    capacity = kva_viz['capacity_line'][0]
                    
                    # Plot KVA
                    ax.plot(times, kva, color='#2196f3', linewidth=1.5, label='KVA Load', alpha=0.8)
                    ax.fill_between(times, kva, alpha=0.2, color='#2196f3')
                    
                    # Plot capacity line
                    ax.axhline(y=capacity, color='red', linestyle='--', linewidth=2, label=f'Rated Capacity ({capacity} kVA)')
                    
                    ax.set_xlabel('Date & Time', fontsize=10)
                    ax.set_ylabel('Load (kVA)', fontsize=10)
                    ax.set_title('Transformer Load (KVA) Over Time', fontsize=12, fontweight='bold')
                    ax.legend(loc='best', fontsize=8)
                    ax.grid(True, alpha=0.3)
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                    img_buffer.seek(0)
                    plt.close()
                    
                    img = Image(img_buffer, width=6.5*inch, height=3.25*inch)
                    story.append(img)
                    story.append(Spacer(1, 15))
                except Exception as e:
                    print(f"Error creating KVA load graph: {str(e)}")
            
            # Graph 2: Load Percentage Timeline
            if load_analysis['visualization_data'].get('kva'):
                try:
                    kva_viz = load_analysis['visualization_data']['kva']
                    fig, ax = plt.subplots(figsize=(10, 5))
                    
                    times = pd.to_datetime(kva_viz['time'])
                    load_pct = kva_viz['load_pct']
                    
                    # Color code based on load percentage
                    colors_array = ['#f44336' if pct > 100 else '#ff9800' if pct > 90 else '#4caf50' for pct in load_pct]
                    
                    ax.scatter(times, load_pct, c=colors_array, s=10, alpha=0.6)
                    ax.axhline(y=100, color='red', linestyle='--', linewidth=2, label='100% Capacity')
                    ax.axhline(y=90, color='orange', linestyle=':', linewidth=1.5, label='90% Warning', alpha=0.7)
                    
                    ax.set_xlabel('Date & Time', fontsize=10)
                    ax.set_ylabel('Load (%)', fontsize=10)
                    ax.set_title('Load Percentage Timeline', fontsize=12, fontweight='bold')
                    ax.legend(loc='best', fontsize=8)
                    ax.grid(True, alpha=0.3)
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                    img_buffer.seek(0)
                    plt.close()
                    
                    img = Image(img_buffer, width=6.5*inch, height=3.25*inch)
                    story.append(img)
                    story.append(Spacer(1, 15))
                except Exception as e:
                    print(f"Error creating load percentage graph: {str(e)}")
            
            # Graph 3: Hourly Load Pattern
            if load_analysis['visualization_data'].get('kva') and load_analysis['visualization_data']['kva'].get('hourly_avg'):
                try:
                    hourly_avg = load_analysis['visualization_data']['kva']['hourly_avg']
                    capacity = load_analysis['rated_capacity_kva']
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    
                    hours = sorted(hourly_avg.keys())
                    loads = [hourly_avg[h] for h in hours]
                    
                    # Color bars based on load percentage
                    colors_bars = ['#f44336' if (l/capacity*100) > 100 else '#ff9800' if (l/capacity*100) > 90 else '#2196f3' for l in loads]
                    
                    ax.bar(hours, loads, color=colors_bars, alpha=0.7, edgecolor='#1976d2', linewidth=1)
                    ax.axhline(y=capacity, color='red', linestyle='--', linewidth=2, label=f'Capacity ({capacity} kVA)')
                    
                    ax.set_xlabel('Hour of Day', fontsize=10)
                    ax.set_ylabel('Average Load (kVA)', fontsize=10)
                    ax.set_title('Average Hourly Load Pattern', fontsize=12, fontweight='bold')
                    ax.legend(loc='best', fontsize=8)
                    ax.grid(True, alpha=0.3, axis='y')
                    ax.set_xticks(range(24))
                    plt.tight_layout()
                    
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                    img_buffer.seek(0)
                    plt.close()
                    
                    img = Image(img_buffer, width=6.5*inch, height=3.25*inch)
                    story.append(img)
                    story.append(Spacer(1, 15))
                except Exception as e:
                    print(f"Error creating hourly pattern graph: {str(e)}")
            
            # Graph 4: Load Duration Curve
            if load_analysis['visualization_data'].get('kva') and load_analysis['visualization_data']['kva'].get('load_duration_curve'):
                try:
                    ldc = load_analysis['visualization_data']['kva']['load_duration_curve']
                    capacity = load_analysis['rated_capacity_kva']
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    
                    ax.plot(ldc['duration_pct'], ldc['load'], color='#2196f3', linewidth=2.5, label='Load Duration')
                    ax.fill_between(ldc['duration_pct'], ldc['load'], alpha=0.3, color='#2196f3')
                    ax.axhline(y=capacity, color='red', linestyle='--', linewidth=2, label=f'Rated Capacity ({capacity} kVA)')
                    
                    ax.set_xlabel('Duration (% of time)', fontsize=10)
                    ax.set_ylabel('Load (kVA)', fontsize=10)
                    ax.set_title('Load Duration Curve', fontsize=12, fontweight='bold')
                    ax.legend(loc='best', fontsize=8)
                    ax.grid(True, alpha=0.3)
                    ax.set_xlim(0, 100)
                    plt.tight_layout()
                    
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                    img_buffer.seek(0)
                    plt.close()
                    
                    img = Image(img_buffer, width=6.5*inch, height=3.25*inch)
                    story.append(img)
                    story.append(Spacer(1, 15))
                except Exception as e:
                    print(f"Error creating load duration curve: {str(e)}")
    
    # Voltage Analysis (only for transformer load PDF)
    try:
        if report.get('transformer_load_analysis') and \
           report.get('transformer_load_analysis', {}).get('voltage_analysis') and \
           report.get('transformer_load_analysis', {}).get('voltage_analysis', {}).get('has_voltage_data'):
            
            story.append(PageBreak())
            story.append(Paragraph("Voltage Quality Analysis", styles['Heading2']))
            
            analysis = report['transformer_load_analysis']
            voltage_analysis = analysis['voltage_analysis']
            
            # Voltage Summary
            voltage_summary_data = [
                ['Parameter', 'Value'],
                ['Nominal Voltage', f"{voltage_analysis['nominal_voltage']} V"],
                ['Average Voltage', f"{voltage_analysis['average_voltage']:.2f} V" if voltage_analysis['average_voltage'] else 'N/A'],
                ['Over Voltage Limit', f"{voltage_analysis['over_voltage_limit']} V"],
                ['Under Voltage Limit', f"{voltage_analysis['under_voltage_limit']} V"]
            ]
            
            voltage_summary_table = Table(voltage_summary_data, colWidths=[3*inch, 3*inch])
            voltage_summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
            ]))
            
            story.append(voltage_summary_table)
            story.append(Spacer(1, 15))
            
            # Add Voltage Graphs to PDF
            if analysis.get('visualization_data') and analysis['visualization_data'].get('voltage'):
                v_viz = analysis['visualization_data']['voltage']
                
                # Graph 1: Voltage Profile Over Time (All Phases)
                try:
                    fig, ax = plt.subplots(figsize=(10, 5))
                    
                    # Convert time strings to datetime
                    times = pd.to_datetime(v_viz['time'])
                    over_limit = v_viz['over_limit'][0]
                    under_limit = v_viz['under_limit'][0]
                    nominal = v_viz['nominal'][0]
                    
                    # Plot all voltage phases
                    colors_phases = ['#9c27b0', '#2196f3', '#4caf50']
                    phase_idx = 0
                    for key in v_viz.keys():
                        if key.startswith('voltage_'):
                            phase_label = key.replace('voltage_', '')
                            ax.plot(times, v_viz[key], 
                                   color=colors_phases[phase_idx % 3], 
                                   linewidth=1.5, 
                                   label=phase_label, 
                                   alpha=0.8)
                            phase_idx += 1
                    
                    # Plot limit lines
                    ax.axhline(y=over_limit, color='red', linestyle='--', linewidth=2, label=f'Over Voltage Limit ({over_limit}V)')
                    ax.axhline(y=under_limit, color='orange', linestyle='--', linewidth=2, label=f'Under Voltage Limit ({under_limit}V)')
                    ax.axhline(y=nominal, color='gray', linestyle=':', linewidth=1, label=f'Nominal ({nominal}V)', alpha=0.7)
                    
                    # Formatting
                    ax.set_xlabel('Date & Time', fontsize=10)
                    ax.set_ylabel('Voltage (V)', fontsize=10)
                    ax.set_title('Voltage Profile Over Time (All Phases)', fontsize=12, fontweight='bold')
                    ax.legend(loc='best', fontsize=8, ncol=2)
                    ax.grid(True, alpha=0.3)
                    
                    # Format x-axis dates
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
                    plt.xticks(rotation=45, ha='right')
                    
                    plt.tight_layout()
                    
                    # Save to buffer
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                    img_buffer.seek(0)
                    plt.close()
                    
                    # Add to PDF
                    img = Image(img_buffer, width=6.5*inch, height=3.25*inch)
                    story.append(img)
                    story.append(Spacer(1, 15))
                    
                except Exception as e:
                    print(f"Error creating voltage profile graph: {str(e)}")
                
            
            # Voltage Profile Over Time - Three Separate Phase Graphs
            try:
                if voltage_analysis.get('voltage_columns'):
                    phases = ['PHASE_A', 'PHASE_B', 'PHASE_C']
                    phase_colors = ['#8E44AD', '#3498DB', '#27AE60']  # Purple, Blue, Green
                    phase_labels = ['PHASE_A_INST._VOLTAGE (V)', 'PHASE_B_INST._VOLTAGE (V)', 'PHASE_C_INST._VOLTAGE (V)']
                    
                    # Get voltage limits
                    over_limit = voltage_analysis.get('over_voltage_limit', 253)
                    under_limit = voltage_analysis.get('under_voltage_limit', 207)
                    nominal_voltage = voltage_analysis.get('nominal_voltage', 230)
                    
                    # Create separate graph for each phase
                    for i, (v_col, v_data) in enumerate(list(voltage_analysis['voltage_columns'].items())[:3]):
                        if 'raw_data' in v_data and v_data['raw_data']:
                            fig, ax = plt.subplots(figsize=(10, 4))
                            
                            # Limit data to 10 days (assuming 24 readings per day = 240 points)
                            data_points = v_data['raw_data']
                            if len(data_points) > 240:  # More than 10 days
                                data_points = data_points[:240]  # Take first 10 days
                            
                            # Create time index for x-axis (hours for 10 days)
                            time_index = list(range(len(data_points)))
                            
                            # Plot voltage over time
                            ax.plot(time_index, data_points, 
                                   color=phase_colors[i], 
                                   label=phase_labels[i], 
                                   linewidth=1.5, 
                                   alpha=0.8)
                            
                            # Add voltage limits
                            ax.axhline(y=over_limit, color='red', linestyle='--', alpha=0.8, label=f'Over Voltage Limit ({over_limit}V)')
                            ax.axhline(y=under_limit, color='orange', linestyle='--', alpha=0.8, label=f'Under Voltage Limit ({under_limit}V)')
                            ax.axhline(y=nominal_voltage, color='gray', linestyle=':', alpha=0.8, label=f'Nominal Voltage ({nominal_voltage}V)')
                            
                            # Formatting
                            ax.set_xlabel('Time Index (10 Days)', fontsize=10)
                            ax.set_ylabel('Voltage (V)', fontsize=10)
                            ax.set_title(f'Voltage Profile Over Time - {phase_labels[i]}', fontsize=12, fontweight='bold')
                            ax.grid(True, alpha=0.3)
                            ax.legend(fontsize=8, loc='best')
                            
                            plt.tight_layout()
                            
                            # Save to buffer
                            img_buffer = io.BytesIO()
                            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                            img_buffer.seek(0)
                            plt.close()
                            
                            # Add to PDF
                            img = Image(img_buffer, width=6.5*inch, height=3*inch)
                            story.append(img)
                            story.append(Spacer(1, 10))
                    
            except Exception as e:
                print(f"Error creating voltage profile over time graphs: {str(e)}")
            
            # Voltage Profile Over Time - Three Separate Phase Graphs
            try:
                if voltage_analysis.get('voltage_columns'):
                    story.append(Paragraph("Voltage Profile Over Time", styles['Heading3']))
                    
                    # Create separate graphs for each phase
                    phase_colors = ['#8E44AD', '#3498DB', '#27AE60']  # Purple, Blue, Green
                    
                    for i, (v_col, v_data) in enumerate(list(voltage_analysis['voltage_columns'].items())[:3]):
                        fig, ax = plt.subplots(figsize=(10, 4))
                        
                        # Get voltage data for this phase (limit to 10 days = 240 points)
                        if 'raw_data' in v_data and v_data['raw_data']:
                            data_points = v_data['raw_data']
                            if len(data_points) > 240:  # More than 10 days
                                data_points = data_points[:240]  # Take first 10 days
                            
                            # Create time index for x-axis
                            time_index = list(range(len(data_points)))
                            
                            # Plot voltage over time
                            ax.plot(time_index, data_points, 
                                   color=phase_colors[i], 
                                   label=v_col, 
                                   linewidth=1.5, 
                                   alpha=0.8)
                            
                            # Add voltage limits
                            over_limit = voltage_analysis.get('over_voltage_limit', 253)
                            under_limit = voltage_analysis.get('under_voltage_limit', 207)
                            nominal_voltage = voltage_analysis.get('nominal_voltage', 230)
                            
                            ax.axhline(y=over_limit, color='red', linestyle='--', alpha=0.8, label=f'Over Voltage Limit ({over_limit}V)')
                            ax.axhline(y=under_limit, color='orange', linestyle='--', alpha=0.8, label=f'Under Voltage Limit ({under_limit}V)')
                            ax.axhline(y=nominal_voltage, color='gray', linestyle=':', alpha=0.8, label=f'Nominal Voltage ({nominal_voltage}V)')
                            
                            # Formatting
                            ax.set_xlabel('Time Index (10 Days)', fontsize=10)
                            ax.set_ylabel('Voltage (V)', fontsize=10)
                            ax.set_title(f'Voltage Profile Over Time - {v_col}', fontsize=12, fontweight='bold')
                            ax.grid(True, alpha=0.3)
                            ax.legend(fontsize=8, loc='best')
                            
                            plt.tight_layout()
                            
                            # Save to buffer
                            img_buffer = io.BytesIO()
                            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                            img_buffer.seek(0)
                            plt.close()
                            
                            # Add to PDF
                            img = Image(img_buffer, width=6.5*inch, height=3*inch)
                            story.append(img)
                            story.append(Spacer(1, 10))
                        
            except Exception as e:
                print(f"Error creating voltage profile over time graphs: {str(e)}")
            
            # Voltage Columns Analysis
            if voltage_analysis.get('voltage_columns'):
                story.append(Paragraph("Voltage Phase Analysis", styles['Heading3']))
                
                
                # Individual phase analysis tables
                for v_col, v_data in list(voltage_analysis['voltage_columns'].items())[:3]:  # Limit to 3 phases
                    phase_data = [
                        ['Metric', 'Value'],
                        ['Phase/Column', v_col],
                        ['Average Voltage', f"{v_data['avg']:.2f} V"],
                        ['Maximum Voltage', f"{v_data['max']:.2f} V"],
                        ['Minimum Voltage', f"{v_data['min']:.2f} V"],
                        ['Within Limits', f"{v_data['within_pct']:.2f}%"],
                        ['Over Voltage', f"{v_data['over_voltage_pct']:.2f}%"],
                        ['Under Voltage', f"{v_data['under_voltage_pct']:.2f}%"]
                    ]
                    
                    phase_table = Table(phase_data, colWidths=[3*inch, 3*inch])
                    phase_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white)
                    ]))
                    
                    story.append(phase_table)
                    story.append(Spacer(1, 12))
    except Exception as e:
        print(f"Error adding voltage analysis to PDF: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# NMD Analysis (Enhanced Feeder-Customer Correlation) routes
from nmd_analysis import NMDAnalysisProcessor

# Initialize NMD Analysis Processor
nmd_processor = NMDAnalysisProcessor()

@app.route('/api/nmd-analysis/upload-feeder', methods=['POST'])
def nmd_analysis_upload_feeder():
    """Upload feeder NMD data for advanced correlation analysis"""
    return nmd_processor.upload_feeder_nmd(request.files['file'], request.form.get('session_id', 'default'))

@app.route('/api/nmd-analysis/upload-customers', methods=['POST'])
def nmd_analysis_upload_customers():
    """Upload customer data files for advanced correlation analysis"""
    return nmd_processor.upload_customer_files(request.files.getlist('files'), request.form.get('session_id', 'default'))

@app.route('/api/nmd-analysis/analyze', methods=['POST'])
def nmd_analysis_analyze():
    """Perform advanced correlation analysis between feeder and customer data"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        return nmd_processor.analyze_correlations(session_id)
    except Exception as e:
        return jsonify({'error': f'Error performing analysis: {str(e)}'}), 500

@app.route('/api/nmd-analysis/visualization', methods=['POST'])
def nmd_analysis_visualization():
    """Generate visualization data for customer-feeder correlation"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        customer_id = data.get('customer_id')
        feeder_id = data.get('feeder_id', 'FEEDER_001')
        return nmd_processor.get_visualization_data(session_id, customer_id, feeder_id)
    except Exception as e:
        return jsonify({'error': f'Error generating visualization: {str(e)}'}), 500

@app.route('/api/nmd-analysis/results', methods=['GET'])
def nmd_analysis_results():
    """Get detailed analysis results"""
    try:
        session_id = request.args.get('session_id', 'default')
        return nmd_processor.get_analysis_results(session_id)
    except Exception as e:
        return jsonify({'error': f'Error getting results: {str(e)}'}), 500

@app.route('/api/nmd-analysis/corrected-data', methods=['GET'])
def nmd_analysis_corrected_data():
    """Get corrected customer data with proper phase labels"""
    try:
        session_id = request.args.get('session_id', 'default')
        return nmd_processor.generate_corrected_data(session_id)
    except Exception as e:
        return jsonify({'error': f'Error generating corrected data: {str(e)}'}), 500

@app.route('/api/nmd-analysis/network-graph', methods=['POST'])
def nmd_analysis_network_graph():
    """Generate hierarchical network graph visualization"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        transformer_name = data.get('transformer_name', 'Transformer')
        return nmd_processor.generate_network_graph(session_id, transformer_name)
    except Exception as e:
        return jsonify({'error': f'Error generating network graph: {str(e)}'}), 500

# Smart Load Balancing & Forecasting routes
@app.route('/api/smart-grid/upload-transformer', methods=['POST'])
def upload_transformer_data():
    """Upload transformer load data for analysis"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    try:
        session_id = request.form.get('session_id', 'default')
        df = pd.read_csv(file)
        
        # Validate transformer data format (should have load, voltage, current columns)
        required_patterns = ['KW', 'VOLTAGE', 'CURRENT']
        has_required = False
        for pattern in required_patterns:
            matching_cols = [col for col in df.columns if pattern in col.upper()]
            if matching_cols:
                has_required = True
                break
        
        if not has_required:
            return jsonify({'error': 'CSV must contain load (kW), voltage, or current data'}), 400
        
        # Process datetime if needed
        if 'datetime' not in df.columns:
            if 'DATE' in df.columns and 'TIME' in df.columns:
                df['datetime'] = pd.to_datetime(
                    df['DATE'].astype(str) + ' ' + df['TIME'].astype(str),
                    errors='coerce'
                )
            elif 'TIMESTAMP' in df.columns:
                df['datetime'] = pd.to_datetime(df['TIMESTAMP'], errors='coerce')
        
        # Store in session
        if session_id not in session_data:
            session_data[session_id] = {}
        
        session_data[session_id]['transformer_data'] = {
            'dataframe': df,
            'filename': file.filename,
            'row_count': len(df),
            'columns': list(df.columns)
        }
        
        # Calculate basic statistics
        stats = {}
        load_col = [col for col in df.columns if 'IMPORT_KW' in col.upper() and 'AVG' in col.upper()]
        if load_col:
            load_data = pd.to_numeric(df[load_col[0]], errors='coerce')
            stats['load'] = {
                'avg_kw': float(load_data.mean()),
                'max_kw': float(load_data.max()),
                'min_kw': float(load_data.min())
            }
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'row_count': len(df),
            'columns': list(df.columns),
            'statistics': stats,
            'message': 'Transformer data uploaded successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing transformer file: {str(e)}'}), 500


@app.route('/api/smart-grid/generate-glm', methods=['POST'])
def generate_glm_model():
    """Generate GridLAB-D .glm file from NMD and customer data"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        transformer_name = data.get('transformer_name', 'T1')
        model_name = data.get('model_name', 'grid_model')
        
        if session_id not in session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        session = session_data[session_id]
        
        # Check if we have the required data
        if 'analysis_results' not in session:
            return jsonify({'error': 'Please run NMD analysis first'}), 400
        
        if 'feeder_data' not in session or 'customer_data' not in session:
            return jsonify({'error': 'Feeder and customer data required'}), 400
        
        # Extract data
        feeder_df = session['feeder_data']['dataframe']
        customer_data_dict = {cid: cdata['dataframe'] 
                             for cid, cdata in session['customer_data'].items()}
        assignments = session['analysis_results']['assignments']
        
        # Get transformer parameters from request
        transformer_capacity_kva = data.get('transformer_capacity_kva', 5000)
        primary_voltage = data.get('primary_voltage', 11000)
        secondary_voltage = data.get('secondary_voltage', 400)
        
        # Use transformer data for GLM generation if available
        transformer_data = None
        if 'transformer_data' in session:
            transformer_data = session['transformer_data']['dataframe']
        
        # Generate GLM file with enhanced parameters and transformer data
        glm_filepath = gridlabd_processor.generate_glm_from_data(
            feeder_df,
            customer_data_dict,
            assignments,
            transformer_name,
            model_name,
            transformer_capacity_kva,
            primary_voltage,
            secondary_voltage,
            transformer_data
        )
        
        # Get temporary file information
        temp_info = gridlabd_processor.get_temp_file_info()
        
        return jsonify({
            'success': True,
            'glm_file': glm_filepath,
            'message': f'GLM file generated: {glm_filepath}',
            'transformer': transformer_name,
            'transformer_capacity_kva': transformer_capacity_kva,
            'primary_voltage': primary_voltage,
            'secondary_voltage': secondary_voltage,
            'total_customers': len(assignments),
            'is_temp_file': temp_info['use_temp_files'],
            'temp_dir': temp_info['temp_dir']
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating GLM: {str(e)}'}), 500

@app.route('/api/smart-grid/run-simulation', methods=['POST'])
def run_gridlabd_simulation():
    """Run GridLAB-D simulation"""
    try:
        data = request.get_json()
        glm_file = data.get('glm_file')
        
        if not glm_file:
            return jsonify({'error': 'GLM file path required'}), 400
        
        # Run simulation
        result = gridlabd_processor.run_simulation(glm_file)
        
        # Add cleanup information to response
        temp_info = gridlabd_processor.get_temp_file_info()
        result['temp_file_cleanup'] = {
            'is_temp_file': temp_info['use_temp_files'],
            'temp_dir': temp_info['temp_dir'],
            'remaining_temp_files': len(temp_info['temp_files'])
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Error running simulation: {str(e)}'}), 500

@app.route('/api/smart-grid/cleanup-temp-files', methods=['POST'])
def cleanup_temp_files():
    """Clean up temporary GLM files"""
    try:
        data = request.get_json()
        specific_file = data.get('file_path')  # Optional: clean specific file
        
        if specific_file:
            # Clean up specific file
            success = gridlabd_processor.cleanup_specific_file(specific_file)
            return jsonify({
                'success': success,
                'message': f'File {specific_file} {"cleaned up" if success else "not found or not a temp file"}'
            })
        else:
            # Clean up all temporary files
            temp_info_before = gridlabd_processor.get_temp_file_info()
            gridlabd_processor.cleanup_temp_files()
            temp_info_after = gridlabd_processor.get_temp_file_info()
            
            return jsonify({
                'success': True,
                'message': 'All temporary files cleaned up',
                'files_cleaned': len(temp_info_before['temp_files']),
                'temp_dir_removed': temp_info_before['temp_dir'] is not None and temp_info_after['temp_dir'] is None
            })
        
    except Exception as e:
        return jsonify({'error': f'Error cleaning up temporary files: {str(e)}'}), 500

@app.route('/api/smart-grid/temp-file-info', methods=['GET'])
def get_temp_file_info():
    """Get information about current temporary files"""
    try:
        temp_info = gridlabd_processor.get_temp_file_info()
        return jsonify({
            'success': True,
            'temp_info': temp_info
        })
    except Exception as e:
        return jsonify({'error': f'Error getting temp file info: {str(e)}'}), 500

@app.route('/api/smart-grid/analyze-balance', methods=['POST'])
def analyze_load_balance():
    """Analyze current load balance"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        if session_id not in session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        session = session_data[session_id]
        
        if 'analysis_results' not in session:
            return jsonify({'error': 'Please run NMD analysis first'}), 400
        
        # Extract data
        feeder_df = session.get('feeder_data', {}).get('dataframe')
        customer_data_dict = {cid: cdata['dataframe'] 
                             for cid, cdata in session.get('customer_data', {}).items()}
        assignments = session['analysis_results']['assignments']
        
        # Extract transformer data if available
        transformer_df = session.get('transformer_data', {}).get('dataframe')
        
        # Analyze balance (with transformer data if available)
        balance_analysis = load_balancer.analyze_current_balance(
            feeder_df,
            customer_data_dict,
            assignments,
            transformer_data=transformer_df
        )
        
        # Store in session
        session_data[session_id]['balance_analysis'] = balance_analysis
        
        return jsonify({
            'success': True,
            'analysis': balance_analysis
        })
        
    except Exception as e:
        return jsonify({'error': f'Error analyzing balance: {str(e)}'}), 500

@app.route('/api/smart-grid/suggest-balancing', methods=['POST'])
def suggest_load_balancing():
    """Suggest load balancing moves"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        if session_id not in session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        session = session_data[session_id]
        
        if 'analysis_results' not in session:
            return jsonify({'error': 'Please run NMD analysis first'}), 400
        
        # Extract data
        feeder_df = session.get('feeder_data', {}).get('dataframe')
        customer_data_dict = {cid: cdata['dataframe'] 
                             for cid, cdata in session.get('customer_data', {}).items()}
        assignments = session['analysis_results']['assignments']
        
        # Get suggestions
        suggestions = load_balancer.suggest_balancing_moves(
            feeder_df,
            customer_data_dict,
            assignments
        )
        
        # Store in session
        session_data[session_id]['balancing_suggestions'] = suggestions
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating suggestions: {str(e)}'}), 500

@app.route('/api/smart-grid/simulate-balancing', methods=['POST'])
def simulate_load_balancing():
    """Simulate the effect of balancing moves"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        moves_to_apply = data.get('moves', [])
        
        if session_id not in session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        session = session_data[session_id]
        
        if 'analysis_results' not in session:
            return jsonify({'error': 'Please run NMD analysis first'}), 400
        
        # Extract data
        customer_data_dict = {cid: cdata['dataframe'] 
                             for cid, cdata in session.get('customer_data', {}).items()}
        assignments = session['analysis_results']['assignments']
        
        # Use suggested moves if none provided
        if not moves_to_apply and 'balancing_suggestions' in session:
            moves_to_apply = session['balancing_suggestions'].get('suggestions', [])[:5]
        
        # Simulate
        simulation_result = load_balancer.simulate_balancing(
            assignments,
            moves_to_apply,
            customer_data_dict
        )
        
        return jsonify({
            'success': True,
            'simulation': simulation_result
        })
        
    except Exception as e:
        return jsonify({'error': f'Error simulating balancing: {str(e)}'}), 500

@app.route('/api/smart-grid/forecast', methods=['POST'])
def forecast_load():
    """Forecast load using specified model"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        model_type = data.get('model_type', 'prophet')  # arima, prophet, or lstm
        forecast_periods = data.get('forecast_periods', 168)  # 1 week hourly
        customer_id = data.get('customer_id')
        feeder_id = data.get('feeder_id')
        use_transformer = data.get('use_transformer', False)  # New parameter for transformer forecasting
        
        if session_id not in session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        session = session_data[session_id]
        
        # Forecast for transformer load
        if use_transformer:
            if 'transformer_data' not in session or session['transformer_data'].get('dataframe') is None:
                return jsonify({'error': 'Transformer data not found. Please upload transformer data first.'}), 404
            
            transformer_df = session['transformer_data']['dataframe']
            
            result = load_forecaster.forecast_transformer_load(
                transformer_df,
                model_type,
                forecast_periods
            )
            
            if result['success']:
                result['source'] = 'transformer'
        
        # Forecast for specific customer
        elif customer_id:
            # Single customer forecast
            if 'customer_data' not in session or customer_id not in session['customer_data']:
                return jsonify({'error': f'Customer {customer_id} not found'}), 404
            
            customer_df = session['customer_data'][customer_id]['dataframe']
            
            if model_type == 'arima':
                result = load_forecaster.forecast_with_arima(customer_df, forecast_periods)
            elif model_type == 'prophet':
                result = load_forecaster.forecast_with_prophet(customer_df, forecast_periods)
            elif model_type == 'lstm':
                result = load_forecaster.forecast_with_lstm(customer_df, forecast_periods)
            else:
                return jsonify({'error': f'Unknown model type: {model_type}'}), 400
            
            if result['success']:
                result['customer_id'] = customer_id
        
        elif feeder_id:
            # Aggregate forecast for feeder
            customer_data_dict = {cid: cdata['dataframe'] 
                                 for cid, cdata in session.get('customer_data', {}).items()}
            
            result = load_forecaster.forecast_aggregate_load(
                customer_data_dict,
                feeder_id,
                model_type,
                forecast_periods
            )
        
        else:
            return jsonify({'error': 'Either customer_id, feeder_id, or use_transformer=true required'}), 400
        
        # Store forecast in session
        if result['success']:
            if 'forecasts' not in session_data[session_id]:
                session_data[session_id]['forecasts'] = {}
            
            forecast_key = 'transformer' if use_transformer else (customer_id if customer_id else feeder_id)
            session_data[session_id]['forecasts'][forecast_key] = result
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Error forecasting: {str(e)}'}), 500

@app.route('/api/smart-grid/compare-forecast-models', methods=['POST'])
def compare_forecast_models():
    """Compare all forecasting models"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        customer_id = data.get('customer_id')
        forecast_periods = data.get('forecast_periods', 168)
        
        if session_id not in session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        session = session_data[session_id]
        
        if not customer_id:
            return jsonify({'error': 'customer_id required'}), 400
        
        if 'customer_data' not in session or customer_id not in session['customer_data']:
            return jsonify({'error': f'Customer {customer_id} not found'}), 404
        
        customer_df = session['customer_data'][customer_id]['dataframe']
        
        # Compare all models
        comparison = load_forecaster.compare_models(customer_df, forecast_periods)
        
        return jsonify({
            'success': True,
            'comparison': comparison,
            'customer_id': customer_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Error comparing models: {str(e)}'}), 500

@app.route('/api/smart-grid/network-graph', methods=['POST'])
def smart_grid_network_graph():
    """Generate network topology graph for Smart Grid"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        transformer_name = data.get('transformer_name', 'Transformer')
        
        if session_id not in session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        session = session_data[session_id]
        if 'analysis_results' not in session:
            return jsonify({'error': 'No analysis results found. Run analysis first.'}), 400
        
        results = session['analysis_results']
        assignments = results.get('assignments', [])
        
        if not assignments:
            return jsonify({'error': 'No customer assignments found'}), 400
        
        # Use the NMD processor to build the graph
        graph_data = nmd_processor._build_hierarchical_graph(assignments, transformer_name)
        
        return jsonify({
            'success': True,
            'graph_data': graph_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating network graph: {str(e)}'}), 500

@app.route('/api/smart-grid/dashboard-data', methods=['GET'])
def get_smart_grid_dashboard():
    """Get comprehensive dashboard data for Smart Load Balancing & Forecasting"""
    try:
        session_id = request.args.get('session_id', 'default')
        
        # If session doesn't exist yet, return empty dashboard (not an error)
        if session_id not in session_data:
            return jsonify({
                'success': True,
                'dashboard': {
                    'has_analysis': False,
                    'has_balance_analysis': False,
                    'has_forecasts': False,
                    'total_customers': 0,
                    'total_feeders': 0,
                    'balance_summary': None,
                    'forecast_summary': {}
                }
            })
        
        session = session_data[session_id]
        
        dashboard_data = {
            'has_analysis': 'analysis_results' in session,
            'has_balance_analysis': 'balance_analysis' in session,
            'has_forecasts': 'forecasts' in session,
            'has_transformer_data': 'transformer_data' in session,
            'total_customers': len(session.get('customer_data', {})),
            'total_feeders': len(session.get('analysis_results', {}).get('feeder_summary', {})),
            'balance_summary': session.get('balance_analysis', {}).get('overall_stats'),
            'transformer_summary': None,
            'forecast_summary': {}
        }
        
        # Add transformer data summary
        if 'transformer_data' in session:
            transformer_info = session['transformer_data']
            dashboard_data['transformer_summary'] = {
                'filename': transformer_info.get('filename'),
                'row_count': transformer_info.get('row_count'),
                'has_data': True
            }
        
        # Add forecast summary
        if 'forecasts' in session:
            forecasts = session['forecasts']
            dashboard_data['forecast_summary'] = {
                'total_forecasts': len(forecasts),
                'forecast_keys': list(forecasts.keys())
            }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting dashboard data: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)