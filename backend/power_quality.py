import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from flask import jsonify, send_file
import io
import json
from utils import session_data, get_time_range, _to_json_safe

class PowerQualityAnalyzer:
    """Handles Power Quality analysis and reporting"""
    
    def upload_feeder_nmd(self, file, session_id):
        """Upload and process feeder NMD data for PQ analysis"""
        df = pd.read_csv(file)
        
        nmd_info = self._detect_nmd_format(df)
        if not nmd_info:
            return jsonify({'error': 'CSV must contain DATE, TIME, CUSTOMER_REF, and three-phase voltage columns'}), 400

        feeder_id_col = self._detect_feeder_id_column(df)
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
    
    def upload_consumer(self, file, session_id, consumer_id, explicit_feeder_ref):
        """Upload and process consumer data for PQ analysis"""
        df = pd.read_csv(file)
        data_info = self._detect_data_format(df)
        if not data_info or not data_info['voltage']['available']:
            return jsonify({'error': 'Consumer CSV must contain time and voltage data.'}), 400

        if session_id not in session_data or 'pq' not in session_data[session_id] or 'nmd' not in session_data[session_id]['pq']:
            return jsonify({'error': 'Upload feeder NMD CSV first.'}), 400

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
            from werkzeug.utils import secure_filename
            import os
            consumer_id = os.path.splitext(secure_filename(file.filename))[0]

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
    
    def generate_report(self, session_id, selected_feeders):
        """Generate Power Quality analysis report"""
        if session_id not in session_data or 'pq' not in session_data[session_id] or 'nmd' not in session_data[session_id]['pq']:
            return jsonify({'error': 'No PQ data found in session. Upload NMD and consumer files first.'}), 400

        try:
            pq_state = session_data[session_id]['pq']
            nmd_blob = pq_state['nmd']
            feeders_all = pq_state.get('feeders', [])
            if not feeders_all:
                return jsonify({'error': 'No feeders detected from NMD data.'}), 400

            # Filter feeders to only include those with consumer data uploaded
            consumers_data = pq_state.get('consumers', {})
            feeders_with_consumers = set()
            if consumers_data:
                for consumer_id, consumer_info in consumers_data.items():
                    if isinstance(consumer_info, dict) and 'feeder' in consumer_info:
                        feeders_with_consumers.add(str(consumer_info['feeder']))
            
            # Only use feeders that have consumer data uploaded
            available_feeders = [feeder for feeder in feeders_all if feeder in feeders_with_consumers]
            feeders_to_use = selected_feeders or available_feeders

            # Build DataFrame and compute metrics
            nmd_df = pd.DataFrame(nmd_blob['data'])
            nmd_info = nmd_blob['nmd_info']
            feeder_id_col = nmd_blob['feeder_id_col']

            report = self._build_pq_report(
                nmd_df=nmd_df,
                nmd_info=nmd_info,
                feeder_id_col=feeder_id_col,
                feeders_to_use=feeders_to_use,
                consumers_blob=pq_state.get('consumers', {})
            )

            # Ensure JSON-safe types
            report_safe = _to_json_safe(report)

            # Generate network graph data
            try:
                graph_data = self._build_pq_hierarchical_graph(
                    nmd_df=nmd_df,
                    nmd_info=nmd_info,
                    feeder_id_col=feeder_id_col,
                    feeders=feeders_to_use,
                    transformer_name='Transformer',
                    consumers_data=pq_state.get('consumers', {})
                )
                report_safe['network_graph'] = graph_data
            except Exception as e:
                print(f"Warning: Could not generate network graph: {str(e)}")
                report_safe['network_graph'] = None

            # Persist report for download
            pq_state['report'] = report_safe
            session_data[session_id]['pq'] = pq_state

            return jsonify({'success': True, 'report': report_safe})
        except Exception as e:
            print(f"Error generating PQ report: {str(e)}")
            return jsonify({'error': f'Could not generate report: {str(e)}'}), 500
    
    def generate_network_graph(self, session_id: str, transformer_name: str = 'Transformer'):
        """Generate hierarchical network graph visualization for Power Quality Analysis"""
        try:
            if session_id not in session_data:
                return jsonify({'error': 'Session not found'}), 404
            
            session = session_data[session_id]
            if 'pq' not in session or 'nmd' not in session['pq']:
                return jsonify({'error': 'No PQ data found. Upload NMD file first.'}), 400
            
            pq_state = session['pq']
            nmd_blob = pq_state['nmd']
            nmd_df = pd.DataFrame(nmd_blob['data'])
            nmd_info = nmd_blob['nmd_info']
            feeder_id_col = nmd_blob['feeder_id_col']
            
            # Get feeders from the data
            feeders = sorted(pd.Series(nmd_df[feeder_id_col].dropna().astype(str).unique()).tolist())
            
            # Get consumer data if available
            consumers_data = pq_state.get('consumers', {})
            
            # Build hierarchical structure for Power Quality
            graph_data = self._build_pq_hierarchical_graph(nmd_df, nmd_info, feeder_id_col, feeders, transformer_name, consumers_data)
            
            return jsonify({
                'success': True,
                'graph_data': graph_data
            })
            
        except Exception as e:
            return jsonify({'error': f'Error generating network graph: {str(e)}'}), 500
    
    def _build_pq_hierarchical_graph(self, nmd_df: pd.DataFrame, nmd_info: Dict, feeder_id_col: str, feeders: List[str], transformer_name: str, consumers_data: Dict = None) -> Dict:
        """Build hierarchical graph structure for Power Quality visualization - showing only categories (feeders) under customers"""
        # Filter feeders to only include those with consumer data uploaded
        feeders_with_consumers = set()
        if consumers_data:
            for consumer_id, consumer_info in consumers_data.items():
                if isinstance(consumer_info, dict) and 'feeder' in consumer_info:
                    feeders_with_consumers.add(str(consumer_info['feeder']))
        
        # Only process feeders that have consumer data
        active_feeders = [feeder for feeder in feeders if feeder in feeders_with_consumers]
        
        if not active_feeders:
            # If no consumer data, return empty graph
            return {
                'nodes': [{
                    'id': 'transformer',
                    'label': transformer_name,
                    'type': 'transformer',
                    'level': 0,
                    'color': '#2C3E50'
                }],
                'edges': [],
                'transformer': transformer_name,
                'total_feeders': 0,
                'total_customers': 0
            }
        
        # Organize data by feeder (categories)
        feeder_structure = {}
        
        # Get voltage columns for overall feeder analysis
        voltage_columns = nmd_info.get('voltage_columns', [])
        
        for feeder_id in active_feeders:
            feeder_data = nmd_df[nmd_df[feeder_id_col] == feeder_id]
            
            if len(feeder_data) == 0:
                continue
                
            # Calculate overall feeder statistics (combining all phases)
            all_voltage_data = []
            for voltage_col in voltage_columns:
                if voltage_col in feeder_data.columns:
                    voltage_data = pd.to_numeric(feeder_data[voltage_col], errors='coerce')
                    all_voltage_data.extend(voltage_data.dropna().tolist())
            
            # Calculate feeder-level statistics
            if all_voltage_data:
                feeder_stats = {
                    'avg_voltage': float(np.mean(all_voltage_data)),
                    'min_voltage': float(np.min(all_voltage_data)),
                    'max_voltage': float(np.max(all_voltage_data)),
                    'data_points': len(all_voltage_data),
                    'customers': []
                }
                
                # Determine voltage quality status for the feeder
                if feeder_stats['avg_voltage'] > 253:
                    status = 'over_voltage'
                elif feeder_stats['avg_voltage'] < 207:
                    status = 'under_voltage'
                else:
                    status = 'normal'
                
                feeder_stats['status'] = status
            else:
                feeder_stats = {
                    'avg_voltage': 0,
                    'min_voltage': 0,
                    'max_voltage': 0,
                    'data_points': 0,
                    'status': 'normal',
                    'customers': []
                }
            
            # Add customers to this feeder if consumer data is available
            if consumers_data:
                for consumer_id, consumer_info in consumers_data.items():
                    if isinstance(consumer_info, dict) and 'feeder' in consumer_info:
                        consumer_feeder = consumer_info['feeder']
                        if str(consumer_feeder) == str(feeder_id):
                            # Add customer to this feeder
                            feeder_stats['customers'].append({
                                'customer_id': consumer_id,
                                'feeder': consumer_feeder,
                                'filename': consumer_info.get('filename', 'Unknown')
                            })
            
            feeder_structure[feeder_id] = feeder_stats
        
        # Build nodes and edges for network graph
        nodes = []
        edges = []
        
        # Transformer node (root)
        nodes.append({
            'id': 'transformer',
            'label': transformer_name,
            'type': 'transformer',
            'level': 0,
            'color': '#2C3E50'
        })
        
        # Calculate positions with better spacing
        num_feeders = len(feeder_structure)
        feeder_spacing = 2.5 / (num_feeders + 1) if num_feeders > 0 else 2.5
        
        feeder_index = 0
        for feeder_id, feeder_stats in feeder_structure.items():
            feeder_index += 1
            feeder_node_id = f'feeder_{feeder_id}'
            
            # Get feeder status for color coding
            status = feeder_stats.get('status', 'normal')
            if status == 'over_voltage':
                feeder_color = '#E74C3C'  # Red for over voltage
            elif status == 'under_voltage':
                feeder_color = '#F39C12'  # Orange for under voltage
            else:
                feeder_color = '#7F8C8D'  # Gray for normal
            
            # Feeder node (category)
            nodes.append({
                'id': feeder_node_id,
                'label': feeder_id,
                'type': 'feeder',
                'level': 1,
                'color': feeder_color,
                'x': feeder_index * feeder_spacing,
                'y': 2,
                'avg_voltage': feeder_stats.get('avg_voltage', 0),
                'min_voltage': feeder_stats.get('min_voltage', 0),
                'max_voltage': feeder_stats.get('max_voltage', 0),
                'data_points': feeder_stats.get('data_points', 0),
                'status': status
            })
            
            # Edge from transformer to feeder
            edges.append({
                'source': 'transformer',
                'target': feeder_node_id
            })
            
            # Customer nodes (directly under feeders, no phase level)
            customers = feeder_stats.get('customers', [])
            customer_index = 0
            for customer in customers:
                customer_node_id = f'customer_{customer["customer_id"]}'
                customer_index += 1
                
                # Check if customer node already exists
                if not any(node['id'] == customer_node_id for node in nodes):
                    nodes.append({
                        'id': customer_node_id,
                        'label': str(customer['customer_id']),
                        'type': 'customer',
                        'level': 2,
                        'color': '#BDC3C7',
                        'x': feeder_index * feeder_spacing,
                        'y': 3 + customer_index * 0.25,
                        'feeder': customer['feeder'],
                        'filename': customer['filename']
                    })
                
                # Edge from feeder directly to customer (no phase level)
                edges.append({
                    'source': feeder_node_id,
                    'target': customer_node_id
                })
        
        # Count total customers
        total_customers = sum(len(feeder_stats.get('customers', [])) for feeder_stats in feeder_structure.values())
        
        return {
            'nodes': nodes,
            'edges': edges,
            'transformer': transformer_name,
            'total_feeders': num_feeders,
            'total_customers': total_customers
        }

    def download_report(self, session_id, filename):
        """Download Power Quality report as JSON"""
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
    
    def _detect_nmd_format(self, df):
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
    
    def _detect_data_format(self, df):
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
                'AVG._VOLTAGE (V)',
            ]
            
            for pattern in single_phase_voltage_patterns:
                if pattern in df.columns:
                    voltage_columns = [pattern]
                    data_info['voltage']['available'] = True
                    data_info['voltage']['columns'] = voltage_columns
                    data_info['voltage']['phase_count'] = 1
                    break
        
        # Check for current columns
        current_columns = []
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
        
        if not data_info['current']['available']:
            single_phase_current_patterns = [
                'PHASE_A_INST._CURRENT (A)',
                'AVG._CURRENT (V)',
            ]
            
            for pattern in single_phase_current_patterns:
                if pattern in df.columns:
                    current_columns = [pattern]
                    data_info['current']['available'] = True
                    data_info['current']['columns'] = current_columns
                    data_info['current']['phase_count'] = 1
                    break
        
        # Check for power factor column
        power_factor_columns = [col for col in df.columns if 'POWER_FACTOR' in col.upper() or 'INST._POWER_FACTOR' in col.upper()]
        if power_factor_columns:
            data_info['power_factor']['available'] = True
            data_info['power_factor']['columns'] = power_factor_columns[:1]
            data_info['power_factor']['phase_count'] = 1
        
        # Check if DATE and TIME columns exist for time series
        if 'DATE' in df.columns and 'TIME' in df.columns:
            try:
                combined_datetime = df['DATE'] + ' ' + df['TIME']
                
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
                    df['time'] = pd.to_datetime(combined_datetime, dayfirst=True, errors='coerce')
                    
            except Exception as e:
                print(f"Error parsing dates: {str(e)}")
                df['time'] = pd.to_datetime('2025-01-01') + pd.to_timedelta(range(len(df)), unit='min')
                
        elif 'time' in df.columns:
            try:
                df['time'] = pd.to_datetime(df['time'], dayfirst=True)
            except:
                df['time'] = pd.to_datetime(df['time'], errors='coerce')
        else:
            df['time'] = pd.to_datetime('2025-01-01') + pd.to_timedelta(range(len(df)), unit='min')
        
        # Return None if no valid parameters found
        if not any([data_info['voltage']['available'], data_info['current']['available'], data_info['power_factor']['available']]):
            return None
        
        return data_info
    
    def _detect_feeder_id_column(self, df: pd.DataFrame) -> Optional[str]:
        """Detect feeder ID column in the DataFrame"""
        for col in ['CUSTOMER_REF', 'Feeder', 'FEEDER', 'FEEDER_ID', 'feeder', 'feeder_id']:
            if col in df.columns:
                return col
        # Try fuzzy match
        for col in df.columns:
            if 'feeder' in str(col).lower() or 'customer_ref' in str(col).lower():
                return col
        return None
    
    def _evaluate_voltage_series(self, series: pd.Series, v_min: float, v_max: float, v_min_strict: float = None, v_max_strict: float = None) -> Dict[str, float]:
        """Evaluate voltage quality metrics for a series"""
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
    
    def _compute_feeder_metrics(self, nmd_df: pd.DataFrame, nmd_info: Dict, feeder_id_col: str, feeders: List[str], v_min: float, v_max: float, v_min_strict: float = None, v_max_strict: float = None) -> List[Dict]:
        """Compute voltage quality metrics for feeders"""
        voltage_cols = [c for c in nmd_info.get('voltage_columns', []) if c in nmd_df.columns]
        results = []
        for feeder in feeders:
            grp = nmd_df[nmd_df[feeder_id_col].astype(str) == str(feeder)]
            phase_metrics: Dict[str, Dict] = {}
            stacked_values = []
            for idx, col in enumerate(voltage_cols):
                phase_name = f"Phase {chr(65 + idx)}"
                m = self._evaluate_voltage_series(grp[col] if col in grp.columns else pd.Series([], dtype=float), v_min, v_max, v_min_strict, v_max_strict)
                phase_metrics[phase_name] = m
                if 'count' in m and m['count'] > 0 and col in grp.columns:
                    stacked_values.append(pd.to_numeric(grp[col], errors='coerce'))
            if stacked_values:
                stacked = pd.concat(stacked_values).dropna()
                overall = self._evaluate_voltage_series(stacked, v_min, v_max, v_min_strict, v_max_strict)
            else:
                overall = {'count': 0, 'within_pct': 0.0, 'over_pct': 0.0, 'under_pct': 0.0, 'min': None, 'max': None, 'mean': None, 'within_strict_pct': 0.0, 'over_strict_pct': 0.0, 'under_strict_pct': 0.0}

            results.append({
                'feeder_ref': str(feeder),
                'phase_metrics': phase_metrics,
                'overall': overall
            })
        return results
    
    def _compute_consumer_metrics(self, consumers_blob: Dict[str, Dict], v_min: float, v_max: float, v_min_strict: float = None, v_max_strict: float = None) -> List[Dict]:
        """Compute voltage quality metrics for consumers"""
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
                    m = self._evaluate_voltage_series(df[col], v_min, v_max, v_min_strict, v_max_strict)
                    phase_metrics[phase_name] = m
                    stacked_values.append(pd.to_numeric(df[col], errors='coerce'))

            if stacked_values:
                stacked = pd.concat(stacked_values).dropna()
                overall = self._evaluate_voltage_series(stacked, v_min, v_max, v_min_strict, v_max_strict)
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
    
    def _generate_pq_suggestions(self, feeders: List[Dict], consumers: List[Dict], limits: Dict[str, float]) -> List[str]:
        """Generate Power Quality improvement suggestions"""
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
    
    def _build_pq_report(self, nmd_df: pd.DataFrame, nmd_info: Dict, feeder_id_col: str, feeders_to_use: List[str], consumers_blob: Dict[str, Dict]) -> Dict:
        """Build comprehensive Power Quality report"""
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
        feeder_results = self._compute_feeder_metrics(
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
        consumer_results = self._compute_consumer_metrics(
            consumers_blob=consumers_blob, 
            v_min=limits['min'], 
            v_max=limits['max'],
            v_min_strict=limits['min_strict'],
            v_max_strict=limits['max_strict']
        )

        # Time range from NMD data
        time_range = get_time_range(nmd_df)

        # Suggestions (Grok AI-like heuristics)
        suggestions = self._generate_pq_suggestions(feeder_results, consumer_results, limits)

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
