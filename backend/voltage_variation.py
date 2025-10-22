import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
import json

class VoltageVariationAnalyzer:
    """Analyzes voltage variation across the grid from transformer to NMD readings"""
    
    def __init__(self):
        self.voltage_limits = {
            'nominal': 230.0,
            'min_standard': 207.0,
            'max_standard': 253.0,
            'min_strict': 216.0,
            'max_strict': 244.0
        }
    
    def analyze_voltage_variation(self, nmd_df: pd.DataFrame, nmd_info: Dict, 
                                feeder_id_col: str, feeders: List[str], 
                                consumers_data: Dict, transformer_voltage: float = 230.0) -> Dict:
        """
        Analyze voltage variation from transformer to NMD readings
        
        Args:
            nmd_df: NMD readings DataFrame
            nmd_info: NMD data format information
            feeder_id_col: Column containing feeder IDs
            feeders: List of feeder IDs to analyze
            consumers_data: Consumer data for each feeder
            transformer_voltage: Assumed transformer voltage (default 230V)
        
        Returns:
            Dictionary containing voltage variation analysis
        """
        
        # Get voltage columns
        voltage_cols = nmd_info.get('voltage_columns', [])
        if not voltage_cols:
            return {'error': 'No voltage columns found in NMD data'}
        
        # Analyze each feeder
        feeder_analysis = {}
        overall_stats = {
            'total_readings': 0,
            'voltage_drops': [],
            'voltage_variations': [],
            'worst_feeder': None,
            'best_feeder': None
        }
        
        for feeder in feeders:
            # Filter data for this feeder
            feeder_data = nmd_df[nmd_df[feeder_id_col] == feeder].copy()
            
            if len(feeder_data) == 0:
                continue
            
            # Calculate voltage statistics for each phase
            phase_analysis = {}
            feeder_voltage_drops = []
            feeder_variations = []
            
            for phase, col in enumerate(voltage_cols, 1):
                if col not in feeder_data.columns:
                    continue
                
                voltage_data = pd.to_numeric(feeder_data[col], errors='coerce').dropna()
                if len(voltage_data) == 0:
                    continue
                
                # Calculate voltage drop from transformer
                voltage_drop = transformer_voltage - voltage_data
                voltage_variation = voltage_data.std()
                
                phase_analysis[f'phase_{phase}'] = {
                    'mean_voltage': float(voltage_data.mean()),
                    'min_voltage': float(voltage_data.min()),
                    'max_voltage': float(voltage_data.max()),
                    'voltage_drop_mean': float(voltage_drop.mean()),
                    'voltage_drop_max': float(voltage_drop.max()),
                    'voltage_variation': float(voltage_variation),
                    'readings_count': len(voltage_data),
                    'within_limits_standard': float(((voltage_data >= self.voltage_limits['min_standard']) & 
                                                   (voltage_data <= self.voltage_limits['max_standard'])).mean() * 100),
                    'within_limits_strict': float(((voltage_data >= self.voltage_limits['min_strict']) & 
                                                  (voltage_data <= self.voltage_limits['max_strict'])).mean() * 100)
                }
                
                feeder_voltage_drops.extend(voltage_drop.tolist())
                feeder_variations.append(voltage_variation)
            
            # Calculate overall feeder statistics
            if feeder_voltage_drops:
                feeder_analysis[feeder] = {
                    'phases': phase_analysis,
                    'overall_voltage_drop_mean': float(np.mean(feeder_voltage_drops)),
                    'overall_voltage_drop_max': float(np.max(feeder_voltage_drops)),
                    'overall_voltage_variation': float(np.mean(feeder_variations)),
                    'total_readings': len(feeder_data),
                    'consumer_count': len(consumers_data.get(feeder, {}))
                }
                
                # Update overall statistics
                overall_stats['total_readings'] += len(feeder_data)
                overall_stats['voltage_drops'].extend(feeder_voltage_drops)
                overall_stats['voltage_variations'].extend(feeder_variations)
        
        # Calculate overall statistics
        if overall_stats['voltage_drops']:
            overall_stats['overall_voltage_drop_mean'] = float(np.mean(overall_stats['voltage_drops']))
            overall_stats['overall_voltage_drop_max'] = float(np.max(overall_stats['voltage_drops']))
            overall_stats['overall_voltage_variation'] = float(np.mean(overall_stats['voltage_variations']))
            
            # Find worst and best feeders
            feeder_drop_means = {feeder: data['overall_voltage_drop_mean'] 
                               for feeder, data in feeder_analysis.items()}
            if feeder_drop_means:
                overall_stats['worst_feeder'] = max(feeder_drop_means, key=feeder_drop_means.get)
                overall_stats['best_feeder'] = min(feeder_drop_means, key=feeder_drop_means.get)
        
        return {
            'transformer_voltage': transformer_voltage,
            'voltage_limits': self.voltage_limits,
            'feeder_analysis': feeder_analysis,
            'overall_stats': overall_stats,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def create_voltage_variation_graph(self, analysis_data: Dict) -> Dict:
        """
        Create interactive voltage variation visualization
        
        Args:
            analysis_data: Output from analyze_voltage_variation
        
        Returns:
            Dictionary containing Plotly graph data
        """
        
        if 'error' in analysis_data:
            return {'error': analysis_data['error']}
        
        feeder_analysis = analysis_data['feeder_analysis']
        overall_stats = analysis_data['overall_stats']
        
        if not feeder_analysis:
            return {'error': 'No feeder data available for visualization'}
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Voltage Drop by Feeder',
                'Voltage Variation by Feeder', 
                'Voltage Distribution (All Feeders)',
                'Feeder Performance Comparison'
            ],
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "histogram"}, {"type": "scatter"}]]
        )
        
        # Prepare data for visualization
        feeders = list(feeder_analysis.keys())
        voltage_drops = [feeder_analysis[f]['overall_voltage_drop_mean'] for f in feeders]
        voltage_variations = [feeder_analysis[f]['overall_voltage_variation'] for f in feeders]
        reading_counts = [feeder_analysis[f]['total_readings'] for f in feeders]
        
        # 1. Voltage Drop by Feeder (Bar Chart)
        fig.add_trace(
            go.Bar(
                x=feeders,
                y=voltage_drops,
                name='Voltage Drop (V)',
                marker_color='#E74C3C',
                text=[f'{drop:.1f}V' for drop in voltage_drops],
                textposition='auto'
            ),
            row=1, col=1
        )
        
        # 2. Voltage Variation by Feeder (Bar Chart)
        fig.add_trace(
            go.Bar(
                x=feeders,
                y=voltage_variations,
                name='Voltage Variation (V)',
                marker_color='#3498DB',
                text=[f'{var:.1f}V' for var in voltage_variations],
                textposition='auto'
            ),
            row=1, col=2
        )
        
        # 3. Voltage Distribution (Histogram)
        all_voltage_drops = overall_stats.get('voltage_drops', [])
        if all_voltage_drops:
            fig.add_trace(
                go.Histogram(
                    x=all_voltage_drops,
                    name='Voltage Drop Distribution',
                    marker_color='#9B59B6',
                    nbinsx=20
                ),
                row=2, col=1
            )
        
        # 4. Feeder Performance Comparison (Scatter)
        fig.add_trace(
            go.Scatter(
                x=voltage_drops,
                y=voltage_variations,
                mode='markers+text',
                text=feeders,
                textposition='top center',
                marker=dict(
                    size=reading_counts,
                    sizemode='diameter',
                    sizeref=max(reading_counts)/50,
                    color=voltage_drops,
                    colorscale='RdYlGn_r',
                    showscale=True,
                    colorbar=dict(title="Voltage Drop (V)")
                ),
                name='Feeder Performance',
                hovertemplate='<b>%{text}</b><br>' +
                            'Voltage Drop: %{x:.1f}V<br>' +
                            'Voltage Variation: %{y:.1f}V<br>' +
                            'Readings: %{marker.size}<extra></extra>'
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Voltage Variation Analysis: Transformer to NMD Readings',
                'x': 0.5,
                'font': {'size': 16}
            },
            height=800,
            showlegend=False,
            font=dict(size=12)
        )
        
        # Update axes
        fig.update_xaxes(title_text="Feeders", row=1, col=1)
        fig.update_yaxes(title_text="Voltage Drop (V)", row=1, col=1)
        
        fig.update_xaxes(title_text="Feeders", row=1, col=2)
        fig.update_yaxes(title_text="Voltage Variation (V)", row=1, col=2)
        
        fig.update_xaxes(title_text="Voltage Drop (V)", row=2, col=1)
        fig.update_yaxes(title_text="Frequency", row=2, col=1)
        
        fig.update_xaxes(title_text="Voltage Drop (V)", row=2, col=2)
        fig.update_yaxes(title_text="Voltage Variation (V)", row=2, col=2)
        
        return {
            'graph_data': fig.to_dict(),
            'summary': {
                'total_feeders': len(feeders),
                'worst_feeder': overall_stats.get('worst_feeder'),
                'best_feeder': overall_stats.get('best_feeder'),
                'overall_voltage_drop_mean': overall_stats.get('overall_voltage_drop_mean', 0),
                'overall_voltage_drop_max': overall_stats.get('overall_voltage_drop_max', 0),
                'overall_voltage_variation': overall_stats.get('overall_voltage_variation', 0)
            }
        }
    
    def create_voltage_profile_graph(self, analysis_data: Dict, selected_feeders: List[str] = None) -> Dict:
        """
        Create voltage profile visualization showing voltage drop along feeders
        
        Args:
            analysis_data: Output from analyze_voltage_variation
            selected_feeders: List of feeders to include (if None, includes all)
        
        Returns:
            Dictionary containing Plotly graph data
        """
        
        if 'error' in analysis_data:
            return {'error': analysis_data['error']}
        
        feeder_analysis = analysis_data['feeder_analysis']
        transformer_voltage = analysis_data['transformer_voltage']
        
        if not feeder_analysis:
            return {'error': 'No feeder data available for visualization'}
        
        # Filter feeders if specified
        feeders_to_plot = selected_feeders if selected_feeders else list(feeder_analysis.keys())
        feeders_to_plot = [f for f in feeders_to_plot if f in feeder_analysis]
        
        if not feeders_to_plot:
            return {'error': 'No valid feeders selected for visualization'}
        
        # Create voltage profile graph
        fig = go.Figure()
        
        # Add voltage limits as horizontal lines
        limits = analysis_data['voltage_limits']
        fig.add_hline(y=limits['min_standard'], line_dash="dash", line_color="red", 
                     annotation_text="Min Standard (207V)")
        fig.add_hline(y=limits['max_standard'], line_dash="dash", line_color="red",
                     annotation_text="Max Standard (253V)")
        fig.add_hline(y=limits['min_strict'], line_dash="dot", line_color="orange",
                     annotation_text="Min Strict (216V)")
        fig.add_hline(y=limits['max_strict'], line_dash="dot", line_color="orange",
                     annotation_text="Max Strict (244V)")
        fig.add_hline(y=limits['nominal'], line_dash="solid", line_color="green",
                     annotation_text="Nominal (230V)")
        
        # Add voltage profiles for each feeder
        colors = px.colors.qualitative.Set3
        for i, feeder in enumerate(feeders_to_plot):
            feeder_data = feeder_analysis[feeder]
            phases = feeder_data['phases']
            
            # Create voltage profile points (transformer -> feeder -> customers)
            x_positions = [0, 1, 2]  # Transformer, Feeder, End of feeder
            voltage_points = [transformer_voltage]
            
            # Calculate average voltage at feeder end
            phase_voltages = []
            for phase_key, phase_data in phases.items():
                phase_voltages.append(phase_data['mean_voltage'])
            
            if phase_voltages:
                avg_feeder_voltage = np.mean(phase_voltages)
                voltage_points.append(avg_feeder_voltage)
                voltage_points.append(avg_feeder_voltage)  # End of feeder
            else:
                voltage_points.extend([transformer_voltage, transformer_voltage])
            
            # Plot voltage profile
            fig.add_trace(go.Scatter(
                x=x_positions,
                y=voltage_points,
                mode='lines+markers',
                name=f'Feeder {feeder}',
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=8),
                hovertemplate=f'<b>Feeder {feeder}</b><br>' +
                             'Position: %{x}<br>' +
                             'Voltage: %{y:.1f}V<extra></extra>'
            ))
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Voltage Profile: Transformer to Feeder End',
                'x': 0.5,
                'font': {'size': 16}
            },
            xaxis_title='Grid Position (Transformer → Feeder → End)',
            yaxis_title='Voltage (V)',
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Update x-axis
        fig.update_xaxes(
            tickmode='array',
            tickvals=[0, 1, 2],
            ticktext=['Transformer', 'Feeder Start', 'Feeder End'],
            showgrid=True
        )
        
        return {
            'graph_data': fig.to_dict(),
            'feeders_analyzed': feeders_to_plot,
            'transformer_voltage': transformer_voltage
        }
    
    def generate_voltage_variation_report(self, analysis_data: Dict) -> Dict:
        """
        Generate comprehensive voltage variation report
        
        Args:
            analysis_data: Output from analyze_voltage_variation
        
        Returns:
            Dictionary containing report data
        """
        
        if 'error' in analysis_data:
            return {'error': analysis_data['error']}
        
        feeder_analysis = analysis_data['feeder_analysis']
        overall_stats = analysis_data['overall_stats']
        voltage_limits = analysis_data['voltage_limits']
        
        # Generate recommendations
        recommendations = []
        
        if overall_stats.get('overall_voltage_drop_mean', 0) > 10:
            recommendations.append("High voltage drop detected. Consider transformer tap adjustment or feeder reinforcement.")
        
        if overall_stats.get('overall_voltage_variation', 0) > 5:
            recommendations.append("High voltage variation detected. Check for load imbalances and consider load balancing.")
        
        worst_feeder = overall_stats.get('worst_feeder')
        if worst_feeder:
            worst_drop = feeder_analysis[worst_feeder]['overall_voltage_drop_mean']
            if worst_drop > 15:
                recommendations.append(f"Feeder {worst_feeder} shows excessive voltage drop ({worst_drop:.1f}V). Priority for reinforcement.")
        
        # Count feeders with issues
        feeders_with_issues = 0
        for feeder, data in feeder_analysis.items():
            if data['overall_voltage_drop_mean'] > 10:
                feeders_with_issues += 1
        
        return {
            'summary': {
                'total_feeders': len(feeder_analysis),
                'feeders_with_issues': feeders_with_issues,
                'overall_voltage_drop_mean': overall_stats.get('overall_voltage_drop_mean', 0),
                'overall_voltage_drop_max': overall_stats.get('overall_voltage_drop_max', 0),
                'overall_voltage_variation': overall_stats.get('overall_voltage_variation', 0),
                'worst_feeder': worst_feeder,
                'best_feeder': overall_stats.get('best_feeder')
            },
            'recommendations': recommendations,
            'voltage_limits': voltage_limits,
            'analysis_timestamp': analysis_data.get('analysis_timestamp')
        }
