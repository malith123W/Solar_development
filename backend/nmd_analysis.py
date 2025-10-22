import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from flask import jsonify
from utils import session_data
from scipy.stats import pearsonr
# Removed sklearn dependency - using numpy for MSE calculation
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

class NMDAnalysisProcessor:
    """Handles NMD analysis for feeder-customer correlation and assignment"""
    
    def __init__(self):
        self.upload_folder = 'uploads'
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def upload_feeder_nmd(self, file, session_id: str):
        """Upload and process NMD feeder CSV file"""
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(self.upload_folder, f"{session_id}_feeder_{filename}")
            file.save(filepath)
            
            # Read and process CSV
            df = pd.read_csv(filepath)
            
            # Detect and validate format
            feeder_info = self._detect_feeder_format(df)
            if not feeder_info:
                return jsonify({'error': 'Invalid feeder CSV format. Required: DATE, TIME, and voltage columns'}), 400
            
            # Process datetime
            df = self._process_datetime(df)
            
            # Store in session
            if session_id not in session_data:
                session_data[session_id] = {}
            
            session_data[session_id]['feeder_data'] = {
                'dataframe': df,
                'info': feeder_info,
                'filename': filename,
                'filepath': filepath
            }
            
            # Clean up temporary file
            try:
                os.remove(filepath)
            except:
                pass
            
            return jsonify({
                'success': True,
                'message': 'Feeder NMD file uploaded successfully',
                'feeder_info': feeder_info,
                'row_count': len(df),
                'time_range': self._get_time_range(df),
                'feeders': feeder_info.get('all_feeder_refs', [feeder_info['feeder_id']])
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing feeder file: {str(e)}'}), 500
    
    def upload_customer_files(self, files, session_id: str):
        """Upload and process multiple customer CSV files"""
        try:
            if session_id not in session_data:
                return jsonify({'error': 'Please upload feeder NMD file first'}), 400
            
            customer_data = {}
            total_customers = 0
            
            for file in files:
                if file.filename == '':
                    continue
                    
                # Save file temporarily
                filename = secure_filename(file.filename)
                filepath = os.path.join(self.upload_folder, f"{session_id}_customer_{filename}")
                file.save(filepath)
                
                # Read and process CSV
                df = pd.read_csv(filepath)
                
                # Detect and validate format
                customer_info = self._detect_customer_format(df)
                if not customer_info:
                    continue
                
                # Process datetime
                df = self._process_datetime(df)
                
                # Extract customer ID from filename or data
                customer_id = self._extract_customer_id(filename, df)
                
                customer_data[customer_id] = {
                    'dataframe': df,
                    'info': customer_info,
                    'filename': filename
                }
                total_customers += 1
                
                # Clean up temporary file
                try:
                    os.remove(filepath)
                except:
                    pass
            
            if not customer_data:
                return jsonify({'error': 'No valid customer files found'}), 400
            
            # Store in session
            session_data[session_id]['customer_data'] = customer_data
            
            return jsonify({
                'success': True,
                'message': f'Successfully uploaded {total_customers} customer files',
                'customer_count': total_customers,
                'customer_ids': list(customer_data.keys())
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing customer files: {str(e)}'}), 500
    
    def analyze_correlations(self, session_id: str):
        """Perform correlation analysis between customers and feeders"""
        try:
            if session_id not in session_data:
                return jsonify({'error': 'Session not found'}), 404
            
            session = session_data[session_id]
            if 'feeder_data' not in session or 'customer_data' not in session:
                return jsonify({'error': 'Both feeder and customer data required'}), 400
            
            feeder_df = session['feeder_data']['dataframe']
            customer_data = session['customer_data']
            feeder_info = session['feeder_data']['info']
            
            # Get all unique feeders from the NMD data
            if 'all_feeder_refs' in feeder_info:
                all_feeders = feeder_info['all_feeder_refs']
            else:
                all_feeders = [feeder_info['feeder_id']]
            
            results = {
                'assignments': [],
                'feeder_summary': {},
                'analysis_metadata': {
                    'total_customers': len(customer_data),
                    'total_feeders': len(all_feeders),
                    'analysis_timestamp': datetime.now().isoformat(),
                    'time_window_minutes': 15,
                    'available_feeders': all_feeders
                }
            }
            
            # Process each customer
            for customer_id, customer_info in customer_data.items():
                try:
                    customer_df = customer_info['dataframe']
                    customer_voltage_cols = customer_info['info']['voltage_columns']
                    
                    # Find best feeder match for this customer across all feeders
                    best_match = self._find_best_feeder_match_multi(
                        customer_df, customer_voltage_cols,
                        feeder_df, feeder_info['voltage_columns'],
                        all_feeders
                    )
                    
                    if best_match:
                        assignment = {
                            'customer_id': customer_id,
                            'assigned_feeder': best_match['feeder_id'],
                            'correlation': best_match['correlation'],
                            'rmse': best_match['rmse'],
                            'aligned_points': best_match['aligned_points'],
                            'customer_filename': customer_info['filename'],
                            'score': best_match['score']
                        }
                        
                        # Add phase analysis if available
                        if 'phase_analysis' in best_match:
                            assignment['phase_analysis'] = best_match['phase_analysis']
                            assignment['phase_assignments'] = best_match['phase_analysis']['phase_assignments']
                        
                        results['assignments'].append(assignment)
                        
                except Exception as e:
                    # Continue with other customers even if one fails
                    continue
            
            # Sort assignments by correlation (highest first)
            results['assignments'].sort(key=lambda x: x['correlation'], reverse=True)
            
            # Group results by feeder
            feeder_groups = {}
            for assignment in results['assignments']:
                feeder_id = assignment['assigned_feeder']
                if feeder_id not in feeder_groups:
                    feeder_groups[feeder_id] = []
                feeder_groups[feeder_id].append(assignment)
            
            results['feeder_summary'] = feeder_groups
            
            # Calculate summary statistics
            if results['assignments']:
                correlations = [a['correlation'] for a in results['assignments']]
                rmse_values = [a['rmse'] for a in results['assignments']]
                
                results['summary_stats'] = {
                    'avg_correlation': float(np.mean(correlations)),
                    'max_correlation': float(np.max(correlations)),
                    'min_correlation': float(np.min(correlations)),
                    'avg_rmse': float(np.mean(rmse_values)),
                    'max_rmse': float(np.max(rmse_values)),
                    'min_rmse': float(np.min(rmse_values))
                }
            
            # Store results in session
            session_data[session_id]['analysis_results'] = results
            
            # Provide detailed success message
            if len(results['assignments']) > 0:
                message = f'Analysis completed successfully. {len(results["assignments"])} customers assigned to feeders.'
            else:
                message = 'Analysis completed but no customer-feeder matches found. Check data quality and time alignment.'
            
            return jsonify({
                'success': True,
                'message': message,
                'results': results
            })
            
        except Exception as e:
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
    
    def _detect_feeder_format(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect feeder NMD CSV format - VOLTAGE ONLY for correlation analysis"""
        info = {
            'has_date': False,
            'has_time': False,
            'voltage_columns': [],
            'feeder_id': None
        }
        
        # Check for DATE and TIME columns
        if 'DATE' in df.columns and 'TIME' in df.columns:
            info['has_date'] = True
            info['has_time'] = True
        
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
        
        # Extract feeder ID from data - check CUSTOMER_REF first (for NMD data)
        if 'CUSTOMER_REF' in df.columns:
            # For NMD data, CUSTOMER_REF contains feeder information
            unique_refs = df['CUSTOMER_REF'].dropna().unique()
            if len(unique_refs) > 0:
                # Use the first unique feeder reference
                info['feeder_id'] = str(unique_refs[0]).strip()
                info['all_feeder_refs'] = [str(ref).strip() for ref in unique_refs]
            else:
                info['feeder_id'] = 'FEEDER_001'
        elif 'FEEDER_ID' in df.columns:
            info['feeder_id'] = df['FEEDER_ID'].iloc[0] if len(df) > 0 else 'FEEDER_001'
        elif 'TRANSFORMER_ID' in df.columns:
            info['feeder_id'] = df['TRANSFORMER_ID'].iloc[0] if len(df) > 0 else 'FEEDER_001'
        else:
            info['feeder_id'] = 'FEEDER_001'  # Default
        
        # Validate required components
        if not (info['has_date'] and info['has_time'] and info['voltage_columns']):
            return None
        
        return info
    
    def _detect_customer_format(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect customer CSV format - VOLTAGE ONLY for correlation analysis"""
        info = {
            'has_date': False,
            'has_time': False,
            'voltage_columns': []
        }
        
        # Check for DATE and TIME columns
        if 'DATE' in df.columns and 'TIME' in df.columns:
            info['has_date'] = True
            info['has_time'] = True
        
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
        
        # Validate required components
        if not (info['has_date'] and info['has_time'] and info['voltage_columns']):
            return None
        
        return info
    
    def _process_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process DATE and TIME columns into datetime"""
        if 'DATE' in df.columns and 'TIME' in df.columns:
            try:
                # Combine DATE and TIME
                combined_datetime = df['DATE'].astype(str) + ' ' + df['TIME'].astype(str)
                
                # Try different date formats
                for date_format in ['%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                    try:
                        df['datetime'] = pd.to_datetime(combined_datetime, format=date_format)
                        break
                    except:
                        continue
                else:
                    # Fallback to pandas automatic parsing with dayfirst=True for DD/MM/YYYY format
                    df['datetime'] = pd.to_datetime(combined_datetime, dayfirst=True, errors='coerce')
                
                # Remove rows with invalid datetime
                df = df.dropna(subset=['datetime'])
                
            except Exception as e:
                # Create dummy datetime if parsing fails
                df['datetime'] = pd.to_datetime('2025-01-01') + pd.to_timedelta(range(len(df)), unit='min')
        
        return df
    
    def _extract_customer_id(self, filename: str, df: pd.DataFrame) -> str:
        """Extract customer ID from filename or data"""
        # Check if there's a customer ID column in the data first
        if 'CUSTOMER_REF' in df.columns:
            customer_ref = df['CUSTOMER_REF'].iloc[0] if len(df) > 0 else None
            if customer_ref:
                return str(customer_ref)
        
        if 'CUSTOMER_ID' in df.columns:
            customer_id = df['CUSTOMER_ID'].iloc[0] if len(df) > 0 else None
            if customer_id:
                return str(customer_id)
        
        # Try to extract from filename (remove extension)
        customer_id = os.path.splitext(filename)[0]
        
        # If filename is just numbers, use it as customer ID
        if customer_id.isdigit():
            return f"CUSTOMER_{customer_id}"
        
        return customer_id
    
    def _find_best_feeder_match_multi(self, customer_df: pd.DataFrame, customer_voltage_cols: List[str],
                                     feeder_df: pd.DataFrame, feeder_voltage_cols: List[str], 
                                     all_feeders: List[str]) -> Optional[Dict]:
        """Find the best feeder match for a customer across multiple feeders (Step 1: Feeder Correlation)"""
        best_match = None
        best_score = -1
        
        # Step 1: Find the best feeder using simple correlation (no phase analysis yet)
        for feeder_id in all_feeders:
            # Filter feeder data for this specific feeder
            feeder_data = feeder_df[feeder_df['CUSTOMER_REF'] == feeder_id] if 'CUSTOMER_REF' in feeder_df.columns else feeder_df
            
            if len(feeder_data) == 0:
                continue
            
            # Use simple correlation analysis (first voltage column only)
            customer_voltage_col = customer_voltage_cols[0] if customer_voltage_cols else None
            feeder_voltage_col = feeder_voltage_cols[0] if feeder_voltage_cols else None
            
            if not customer_voltage_col or not feeder_voltage_col:
                continue
            
            # Align customer and feeder data by timestamp
            aligned_data = self._align_timestamps(customer_df, customer_voltage_col, 
                                                feeder_data, feeder_voltage_col)
            
            if aligned_data is None or len(aligned_data) < 10:
                continue
            
            customer_voltage = aligned_data['customer_voltage'].values
            feeder_voltage = aligned_data['feeder_voltage'].values
            
            # Calculate correlation
            try:
                correlation, _ = pearsonr(customer_voltage, feeder_voltage)
                if np.isnan(correlation):
                    correlation = 0
            except:
                correlation = 0
            
            # Calculate RMSE using numpy
            try:
                mse = np.mean((customer_voltage - feeder_voltage) ** 2)
                rmse = np.sqrt(mse)
            except:
                rmse = float('inf')
            
            # Calculate combined score with new formula
            # Normalize RMSE relative to nominal voltage (230V)
            normalized_rmse = rmse / 230.0
            # New scoring: Score = |r| - 0.5 × RMSE_norm
            score = abs(correlation) - (0.5 * normalized_rmse)
            
            # Update best match if this is better
            if score > best_score:
                best_score = score
                best_match = {
                    'feeder_id': feeder_id,
                    'correlation': float(correlation),
                    'rmse': float(rmse),
                    'score': float(score),
                    'aligned_points': len(aligned_data),
                    'feeder_data': feeder_data  # Store feeder data for phase analysis
                }
        
        if best_match:
            # Step 2: Now perform phase analysis with the best feeder
            phase_analysis = self._analyze_phase_correlation(
                customer_df, customer_voltage_cols,
                best_match['feeder_data'], feeder_voltage_cols
            )
            
            if phase_analysis:
                best_match['phase_analysis'] = phase_analysis
                best_match['phase_assignments'] = phase_analysis['phase_assignments']
        
        return best_match
    
    def _analyze_phase_correlation(self, customer_df: pd.DataFrame, customer_voltage_cols: List[str],
                                  feeder_df: pd.DataFrame, feeder_voltage_cols: List[str]) -> Optional[Dict]:
        """Analyze correlation between customer phases and feeder phases"""
        try:
            phase_matches = []
            best_correlation = -1
            best_rmse = float('inf')
            best_aligned_points = 0
            
            # For each customer phase
            for i, customer_voltage_col in enumerate(customer_voltage_cols):
                customer_phase_name = f"Phase {chr(65 + i)}"  # A, B, C
                
                # Test against each feeder phase
                for j, feeder_voltage_col in enumerate(feeder_voltage_cols):
                    feeder_phase_name = f"Phase {chr(65 + j)}"  # A, B, C
                    
                    # Align customer and feeder data by timestamp
                    aligned_data = self._align_timestamps(customer_df, customer_voltage_col, 
                                                        feeder_df, feeder_voltage_col)
                    
                    if aligned_data is None or len(aligned_data) < 10:
                        continue
                    
                    customer_voltage = aligned_data['customer_voltage'].values
                    feeder_voltage = aligned_data['feeder_voltage'].values
                    
                    # Calculate correlation
                    try:
                        correlation, _ = pearsonr(customer_voltage, feeder_voltage)
                        if np.isnan(correlation):
                            correlation = 0
                    except:
                        correlation = 0
                    
                    # Calculate RMSE using numpy
                    try:
                        mse = np.mean((customer_voltage - feeder_voltage) ** 2)
                        rmse = np.sqrt(mse)
                    except:
                        rmse = float('inf')
                    
                    # Calculate combined score with new formula
                    # Normalize RMSE relative to nominal voltage (230V)
                    normalized_rmse = rmse / 230.0
                    # New scoring: Score = |r| - 0.5 × RMSE_norm
                    score = abs(correlation) - (0.5 * normalized_rmse)
                    
                    phase_match = {
                        'customer_phase': customer_phase_name,
                        'customer_voltage_col': customer_voltage_col,
                        'feeder_phase': feeder_phase_name,
                        'feeder_voltage_col': feeder_voltage_col,
                        'correlation': float(correlation),
                        'rmse': float(rmse),
                        'score': float(score),
                        'aligned_points': len(aligned_data)
                    }
                    
                    phase_matches.append(phase_match)
                    
                    # Track best overall metrics
                    if correlation > best_correlation:
                        best_correlation = correlation
                    if rmse < best_rmse:
                        best_rmse = rmse
                    if len(aligned_data) > best_aligned_points:
                        best_aligned_points = len(aligned_data)
            
            if not phase_matches:
                return None
            
            # Determine phase assignments
            phase_assignments = self._determine_phase_assignments(phase_matches, len(customer_voltage_cols))
            
            return {
                'phase_matches': phase_matches,
                'phase_assignments': phase_assignments,
                'best_correlation': float(best_correlation),
                'best_rmse': float(best_rmse),
                'best_aligned_points': best_aligned_points
            }
            
        except Exception as e:
            return None
    
    def _determine_phase_assignments(self, phase_matches: List[Dict], num_customer_phases: int) -> List[Dict]:
        """Determine the best phase assignments for customer phases"""
        assignments = []
        
        # For single-phase customers, find the best feeder phase match
        if num_customer_phases == 1:
            best_match = max(phase_matches, key=lambda x: x['score'])
            assignment = {
                'customer_phase': best_match['customer_phase'],
                'assigned_feeder_phase': best_match['feeder_phase'],
                'correlation': best_match['correlation'],
                'rmse': best_match['rmse'],
                'score': best_match['score'],
                'aligned_points': best_match['aligned_points']
            }
            assignments.append(assignment)
        
        # For multi-phase customers (2, 3, or more phases), find the best alignment
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
                assignment = {
                    'customer_phase': customer_phase,
                    'assigned_feeder_phase': best_match['feeder_phase'],
                    'correlation': best_match['correlation'],
                    'rmse': best_match['rmse'],
                    'score': best_match['score'],
                    'aligned_points': best_match['aligned_points']
                }
                assignments.append(assignment)
        
        return assignments
    
    def _find_best_feeder_match(self, customer_df: pd.DataFrame, customer_voltage_cols: List[str],
                               feeder_df: pd.DataFrame, feeder_voltage_cols: List[str]) -> Optional[Dict]:
        """Find the best feeder match for a customer based on correlation and RMSE (legacy method)"""
        # Use the multi-feeder method with a single feeder
        return self._find_best_feeder_match_multi(customer_df, customer_voltage_cols, 
                                                 feeder_df, feeder_voltage_cols, ['FEEDER_001'])
    
    def _align_timestamps(self, customer_df: pd.DataFrame, customer_col: str,
                         feeder_df: pd.DataFrame, feeder_col: str, 
                         time_window_minutes: int = 15) -> Optional[pd.DataFrame]:
        """Align customer and feeder data by timestamp within time window"""
        try:
            # Ensure datetime columns exist
            if 'datetime' not in customer_df.columns or 'datetime' not in feeder_df.columns:
                return None
            
            # Clean data - remove NaN values and ensure numeric voltage values
            customer_clean = customer_df[['datetime', customer_col]].dropna()
            feeder_clean = feeder_df[['datetime', feeder_col]].dropna()
            
            # Convert voltage columns to numeric, removing any non-numeric values
            customer_clean[customer_col] = pd.to_numeric(customer_clean[customer_col], errors='coerce')
            feeder_clean[feeder_col] = pd.to_numeric(feeder_clean[feeder_col], errors='coerce')
            
            # Remove rows with NaN voltage values
            customer_clean = customer_clean.dropna()
            feeder_clean = feeder_clean.dropna()
            
            if len(customer_clean) == 0 or len(feeder_clean) == 0:
                return None
            
            # Sort by datetime to ensure proper alignment
            customer_clean = customer_clean.sort_values('datetime')
            feeder_clean = feeder_clean.sort_values('datetime')
            
            # Convert to numpy arrays for faster processing
            customer_times = customer_clean['datetime'].values
            customer_voltages = customer_clean[customer_col].values
            feeder_times = feeder_clean['datetime'].values
            feeder_voltages = feeder_clean[feeder_col].values
            
            # Find aligned pairs within time window
            aligned_pairs = []
            time_window = pd.Timedelta(minutes=time_window_minutes)
            
            for i, customer_time in enumerate(customer_times):
                # Find closest feeder reading within time window
                time_diffs = np.abs(feeder_times - customer_time)
                valid_indices = time_diffs <= time_window
                
                if np.any(valid_indices):
                    # Get the closest match
                    closest_idx = np.argmin(time_diffs[valid_indices])
                    valid_feeder_indices = np.where(valid_indices)[0]
                    feeder_idx = valid_feeder_indices[closest_idx]
                    
                    # Calculate time difference in minutes
                    time_diff_minutes = time_diffs[feeder_idx] / np.timedelta64(1, 'm')
                    
                    aligned_pairs.append({
                        'customer_voltage': float(customer_voltages[i]),
                        'feeder_voltage': float(feeder_voltages[feeder_idx]),
                        'time_diff_minutes': float(time_diff_minutes),
                        'customer_time': customer_time,
                        'feeder_time': feeder_times[feeder_idx]
                    })
            
            if len(aligned_pairs) < 10:  # Need minimum aligned points for reliable correlation
                return None
            
            return pd.DataFrame(aligned_pairs)
            
        except Exception as e:
            return None
    
    def _get_time_range(self, df: pd.DataFrame) -> Dict:
        """Get time range from dataframe"""
        if 'datetime' in df.columns:
            min_time = df['datetime'].min()
            max_time = df['datetime'].max()
            return {
                'min_datetime': min_time.strftime('%Y-%m-%dT%H:%M'),
                'max_datetime': max_time.strftime('%Y-%m-%dT%H:%M'),
                'duration_hours': (max_time - min_time).total_seconds() / 3600
            }
        return {}
    
    def get_visualization_data(self, session_id: str, customer_id: str, feeder_id: str = 'FEEDER_001'):
        """Get data for visualization of customer vs feeder voltage curves"""
        try:
            if session_id not in session_data:
                return jsonify({'error': 'Session not found'}), 404
            
            session = session_data[session_id]
            if 'customer_data' not in session or 'feeder_data' not in session:
                return jsonify({'error': 'Customer and feeder data required'}), 400
            
            if customer_id not in session['customer_data']:
                return jsonify({'error': 'Customer not found'}), 404
            
            customer_df = session['customer_data'][customer_id]['dataframe']
            feeder_df = session['feeder_data']['dataframe']
            
            customer_voltage_col = session['customer_data'][customer_id]['info']['voltage_columns'][0]
            feeder_voltage_col = session['feeder_data']['info']['voltage_columns'][0]
            
            # Filter feeder data for the specific feeder if CUSTOMER_REF column exists
            if 'CUSTOMER_REF' in feeder_df.columns:
                feeder_data = feeder_df[feeder_df['CUSTOMER_REF'] == feeder_id]
                if len(feeder_data) == 0:
                    return jsonify({'error': f'Feeder {feeder_id} not found in data'}), 404
            else:
                feeder_data = feeder_df
            
            # Align data
            aligned_data = self._align_timestamps(customer_df, customer_voltage_col,
                                                feeder_data, feeder_voltage_col)
            
            if aligned_data is None:
                return jsonify({'error': 'No aligned data found'}), 400
            
            # Prepare visualization data with time series
            viz_data = {
                'customer_voltage': aligned_data['customer_voltage'].tolist(),
                'feeder_voltage': aligned_data['feeder_voltage'].tolist(),
                'time_diffs': aligned_data['time_diff_minutes'].tolist(),
                'customer_times': [str(t) for t in aligned_data['customer_time']],
                'feeder_times': [str(t) for t in aligned_data['feeder_time']],
                'aligned_points': len(aligned_data),
                'customer_id': customer_id,
                'feeder_id': feeder_id
            }
            
            return jsonify({
                'success': True,
                'visualization_data': viz_data
            })
            
        except Exception as e:
            return jsonify({'error': f'Error getting visualization data: {str(e)}'}), 500
    
    def get_analysis_results(self, session_id: str):
        """Get detailed analysis results for display"""
        try:
            if session_id not in session_data:
                return jsonify({'error': 'Session not found'}), 404
            
            session = session_data[session_id]
            if 'analysis_results' not in session:
                return jsonify({'error': 'No analysis results found. Run analysis first.'}), 400
            
            results = session['analysis_results']
            
            return jsonify({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            return jsonify({'error': f'Error getting analysis results: {str(e)}'}), 500
    
    def generate_network_graph(self, session_id: str, transformer_name: str = 'Transformer'):
        """Generate hierarchical network graph visualization data"""
        try:
            if session_id not in session_data:
                return jsonify({'error': 'Session not found'}), 404
            
            session = session_data[session_id]
            if 'analysis_results' not in session:
                return jsonify({'error': 'No analysis results found. Run analysis first.'}), 400
            
            results = session['analysis_results']
            assignments = results.get('assignments', [])
            
            if not assignments:
                return jsonify({'error': 'No customer assignments found'}), 400
            
            # Build hierarchical structure
            graph_data = self._build_hierarchical_graph(assignments, transformer_name)
            
            return jsonify({
                'success': True,
                'graph_data': graph_data
            })
            
        except Exception as e:
            return jsonify({'error': f'Error generating network graph: {str(e)}'}), 500
    
    def _build_hierarchical_graph(self, assignments: List[Dict], transformer_name: str) -> Dict:
        """Build hierarchical graph structure for visualization"""
        # Organize data by feeder and phase
        feeder_structure = {}
        
        for assignment in assignments:
            customer_id = assignment['customer_id']
            feeder_id = assignment['assigned_feeder']
            phase_assignments = assignment.get('phase_assignments', [])
            
            # Initialize feeder if not exists
            if feeder_id not in feeder_structure:
                feeder_structure[feeder_id] = {
                    'Phase A': [],
                    'Phase B': [],
                    'Phase C': []
                }
            
            # Add customer to appropriate phases
            if phase_assignments:
                for phase_assignment in phase_assignments:
                    assigned_phase = phase_assignment['assigned_feeder_phase']
                    if assigned_phase in feeder_structure[feeder_id]:
                        feeder_structure[feeder_id][assigned_phase].append({
                            'customer_id': customer_id,
                            'customer_phase': phase_assignment['customer_phase'],
                            'correlation': phase_assignment['correlation'],
                            'score': phase_assignment['score']
                        })
            else:
                # If no phase assignments, add to Phase A by default
                feeder_structure[feeder_id]['Phase A'].append({
                    'customer_id': customer_id,
                    'correlation': assignment.get('correlation', 0),
                    'score': assignment.get('score', 0)
                })
        
        # Build nodes and edges for network graph
        nodes = []
        edges = []
        node_positions = {}
        
        # Transformer node (root)
        nodes.append({
            'id': 'transformer',
            'label': transformer_name,
            'type': 'transformer',
            'level': 0,
            'color': '#2C3E50'
        })
        
        # Calculate positions
        num_feeders = len(feeder_structure)
        feeder_spacing = 1.0 / (num_feeders + 1)
        
        feeder_index = 0
        for feeder_id, phases in feeder_structure.items():
            feeder_index += 1
            feeder_node_id = f'feeder_{feeder_id}'
            
            # Feeder node
            nodes.append({
                'id': feeder_node_id,
                'label': feeder_id,
                'type': 'feeder',
                'level': 1,
                'color': '#7F8C8D',
                'x': feeder_index * feeder_spacing,
                'y': 1
            })
            
            # Edge from transformer to feeder
            edges.append({
                'source': 'transformer',
                'target': feeder_node_id
            })
            
            # Phase nodes
            phase_colors = {
                'Phase A': '#E74C3C',  # Red
                'Phase B': '#F39C12',  # Yellow/Orange
                'Phase C': '#3498DB'   # Blue
            }
            
            phase_index = 0
            for phase_name, customers in phases.items():
                if not customers:
                    continue
                    
                phase_node_id = f'phase_{feeder_id}_{phase_name.replace(" ", "_")}'
                phase_index += 1
                
                # Phase node
                nodes.append({
                    'id': phase_node_id,
                    'label': phase_name,
                    'type': 'phase',
                    'level': 2,
                    'color': phase_colors.get(phase_name, '#95A5A6'),
                    'x': (feeder_index - 0.5 + (phase_index - 1) * 0.33) * feeder_spacing,
                    'y': 2
                })
                
                # Edge from feeder to phase
                edges.append({
                    'source': feeder_node_id,
                    'target': phase_node_id
                })
                
                # Customer nodes
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
                            'level': 3,
                            'color': '#BDC3C7',
                            'correlation': customer.get('correlation', 0),
                            'score': customer.get('score', 0),
                            'x': (feeder_index - 0.5 + (phase_index - 1) * 0.33) * feeder_spacing,
                            'y': 3 + customer_index * 0.15
                        })
                    
                    # Edge from phase to customer
                    edges.append({
                        'source': phase_node_id,
                        'target': customer_node_id
                    })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'transformer': transformer_name,
            'total_feeders': num_feeders,
            'total_customers': len(assignments)
        }
    
    def generate_corrected_data(self, session_id: str):
        """Generate corrected customer data with proper phase labels"""
        try:
            if session_id not in session_data:
                return jsonify({'error': 'Session not found'}), 404
            
            session = session_data[session_id]
            if 'analysis_results' not in session or 'customer_data' not in session:
                return jsonify({'error': 'No analysis results found. Run analysis first.'}), 400
            
            results = session['analysis_results']
            customer_data = session['customer_data']
            
            corrected_customers = {}
            
            for assignment in results['assignments']:
                customer_id = assignment['customer_id']
                if customer_id not in customer_data:
                    continue
                
                customer_df = customer_data[customer_id]['dataframe'].copy()
                
                # Apply phase corrections if phase analysis is available
                if 'phase_assignments' in assignment:
                    corrected_df = self._apply_phase_corrections(customer_df, assignment['phase_assignments'])
                    corrected_customers[customer_id] = {
                        'original_data': customer_df.to_dict('records'),
                        'corrected_data': corrected_df.to_dict('records'),
                        'phase_assignments': assignment['phase_assignments'],
                        'filename': customer_data[customer_id]['filename']
                    }
                else:
                    # No phase corrections available
                    corrected_customers[customer_id] = {
                        'original_data': customer_df.to_dict('records'),
                        'corrected_data': customer_df.to_dict('records'),
                        'phase_assignments': [],
                        'filename': customer_data[customer_id]['filename']
                    }
            
            return jsonify({
                'success': True,
                'corrected_customers': corrected_customers,
                'total_customers': len(corrected_customers)
            })
            
        except Exception as e:
            return jsonify({'error': f'Error generating corrected data: {str(e)}'}), 500
    
    def _apply_phase_corrections(self, customer_df: pd.DataFrame, phase_assignments: List[Dict]) -> pd.DataFrame:
        """Apply phase corrections to customer data"""
        corrected_df = customer_df.copy()
        
        for assignment in phase_assignments:
            customer_phase = assignment['customer_phase']
            assigned_feeder_phase = assignment['assigned_feeder_phase']
            
            # Find the customer voltage column for this phase
            customer_voltage_col = None
            for col in corrected_df.columns:
                if 'PHASE_A_INST._VOLTAGE' in col and customer_phase == 'Phase A':
                    customer_voltage_col = col
                    break
                elif 'PHASE_B_INST._VOLTAGE' in col and customer_phase == 'Phase B':
                    customer_voltage_col = col
                    break
                elif 'PHASE_C_INST._VOLTAGE' in col and customer_phase == 'Phase C':
                    customer_voltage_col = col
                    break
            
            if customer_voltage_col:
                # Create new column name with corrected phase
                new_col_name = customer_voltage_col.replace(
                    f'PHASE_{customer_phase.split()[-1]}_INST._VOLTAGE',
                    f'PHASE_{assigned_feeder_phase.split()[-1]}_INST._VOLTAGE'
                )
                
                # Rename the column
                corrected_df = corrected_df.rename(columns={customer_voltage_col: new_col_name})
        
        return corrected_df


def secure_filename(filename: str) -> str:
    """Secure filename for file uploads"""
    import re
    # Remove any path separators and keep only alphanumeric, dots, dashes, underscores
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    return filename
