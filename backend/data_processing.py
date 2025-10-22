import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from flask import jsonify
from utils import session_data, get_time_range, calculate_statistics

class DataProcessor:
    """Handles CSV data processing and format detection for general power data"""
    
    def process_upload(self, file, session_id):
        """Process uploaded CSV file and detect data format"""
        print(f"Processing file: {file.filename}")
        df = pd.read_csv(file)
        print(f"CSV loaded with {len(df)} rows and columns: {list(df.columns)}")
        
        # Detect data format and available parameters
        data_info = self.detect_data_format(df)
        
        if not data_info:
            return jsonify({'error': 'CSV must contain voltage, current, or power factor columns'}), 400
        
        # Store data in session
        session_data[session_id] = {
            'data': df.to_dict('records'),
            'columns': df.columns.tolist(),
            'filename': file.filename,
            'data_info': data_info,
            'row_count': len(df)
        }
        
        # Generate initial graph with voltage data
        initial_parameter = 'voltage' if data_info['voltage']['available'] else 'current' if data_info['current']['available'] else 'power_factor'
        
        # Calculate basic statistics
        stats = calculate_statistics(df, data_info)
        
        # Extract time range information
        time_range = get_time_range(df)
        
        return jsonify({
            'success': True,
            'data_info': data_info,
            'statistics': stats,
            'time_range': time_range,
            'columns': df.columns.tolist(),
            'filename': file.filename,
            'row_count': len(df),
            'initial_parameter': initial_parameter
        })
    
    def detect_data_format(self, df):
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


class NMDProcessor:
    """Handles NMD (Network Monitoring Device) data processing"""
    
    def process_upload(self, file, session_id):
        """Process uploaded NMD CSV file"""
        print(f"Processing NMD file: {file.filename}")
        df = pd.read_csv(file)
        print(f"NMD CSV loaded with {len(df)} rows and columns: {list(df.columns)}")
        
        # Detect NMD data format
        nmd_info = self.detect_nmd_format(df)
        
        if not nmd_info:
            return jsonify({'error': 'CSV must contain Date, Time, CUSTOMER_REF, and three-phase voltage columns'}), 400
        
        # Store data in session
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
        stats = self.calculate_nmd_statistics(df, nmd_info)
        
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
    
    def detect_nmd_format(self, df):
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
    
    def calculate_nmd_statistics(self, df, nmd_info):
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
