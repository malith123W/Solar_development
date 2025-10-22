import pandas as pd
import plotly.graph_objects as go
import plotly.utils
import json
import io
from flask import jsonify, send_file
from utils import session_data, calculate_statistics

class GraphGenerator:
    """Handles graph generation and visualization for power data"""
    
    def generate_filtered_graph(self, session_id, parameter_type, start_date, end_date):
        """Generate graph with time filtering"""
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
        graph_data = self.generate_graph_data(df, parameter_type, data_info)

        # Calculate statistics for the filtered range and selected parameter
        stats_all = calculate_statistics(df, data_info)
        selected_stats = stats_all.get(parameter_type, {})
        
        return jsonify({
            'success': True,
            'graph_data': graph_data,
            'filtered_rows': len(df),
            'statistics': selected_stats
        })
    
    def generate_nmd_graph(self, session_id, customer_ref, start_date, end_date):
        """Generate NMD graph for specific customer"""
        if session_id not in session_data:
            return jsonify({'error': 'Session not found'}), 404
        
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
        graph_data = self.generate_nmd_graph_data(df, nmd_info, customer_ref)
        
        return jsonify({
            'success': True,
            'graph_data': graph_data,
            'filtered_rows': len(df),
            'customer_ref': customer_ref
        })
    
    def download_graph(self, session_id, parameter_type, format_type, start_date, end_date):
        """Download graph as image file"""
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
        fig = self.create_plotly_figure(df, parameter_type, data_info)
        
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
    
    def generate_graph_data(self, df, parameter_type, data_info):
        """Generate graph data for Plotly based on parameter type"""
        try:
            if not data_info[parameter_type]['available']:
                return {
                    "data": [{"x": [], "y": [], "type": "scatter", "name": f"No {parameter_type} data available"}],
                    "layout": {"title": f"Error: No {parameter_type} data available", "height": 600}
                }
            
            fig = self.create_plotly_figure(df, parameter_type, data_info)
            return json.loads(fig.to_json())
        except Exception as e:
            print(f"Error generating graph data: {str(e)}")
            return {
                "data": [{"x": [], "y": [], "type": "scatter", "name": "Error"}],
                "layout": {"title": "Error: Could not generate graph data", "height": 600}
            }
    
    def generate_nmd_graph_data(self, df, nmd_info, customer_ref):
        """Generate graph data for NMD three-phase voltage analysis"""
        try:
            if not nmd_info['voltage_columns']:
                return {
                    "data": [{"x": [], "y": [], "type": "scatter", "name": "No voltage data available"}],
                    "layout": {"title": f"Error: No voltage data available for customer {customer_ref}", "height": 600}
                }
            
            fig = self.create_nmd_plotly_figure(df, nmd_info, customer_ref)
            return json.loads(fig.to_json())
        except Exception as e:
            print(f"Error generating NMD graph data: {str(e)}")
            return {
                "data": [{"x": [], "y": [], "type": "scatter", "name": "Error"}],
                "layout": {"title": "Error: Could not generate NMD graph data", "height": 600}
            }
    
    def create_plotly_figure(self, df, parameter_type, data_info):
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
    
    def create_nmd_plotly_figure(self, df, nmd_info, customer_ref):
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
