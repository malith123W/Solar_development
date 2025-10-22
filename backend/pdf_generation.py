import io
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_agg import FigureCanvasAgg
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from flask import send_file
from utils import session_data

class PDFGenerator:
    """Handles PDF generation for Power Quality reports"""
    
    def generate_power_quality_pdf(self, session_id, transformer_number='T-001'):
        """Generate a comprehensive Power Quality Analysis PDF report"""
        if session_id not in session_data or 'pq' not in session_data[session_id] or 'report' not in session_data[session_id]['pq']:
            raise ValueError('No report available. Generate the report first.')
        
        report = session_data[session_id]['pq']['report']
        nmd_data = session_data[session_id]['pq']['nmd']
        consumers_data = session_data[session_id]['pq'].get('consumers', {})
        
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
                voltage_fig = self.create_voltage_chart(sample_df, voltage_columns, "Voltage Profile Over Time")
                voltage_buffer = self.save_chart_to_buffer(voltage_fig)
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
                current_fig = self.create_current_chart(sample_df, current_columns, "Current Profile Over Time")
                current_buffer = self.save_chart_to_buffer(current_fig)
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
                pf_fig = self.create_power_factor_chart(sample_df, pf_columns, "Power Factor Over Time")
                pf_buffer = self.save_chart_to_buffer(pf_fig)
                pf_img = Image(pf_buffer, width=6*inch, height=3*inch)
                story.append(pf_img)
        
        except Exception as e:
            print(f"Error creating charts: {str(e)}")
            # Add a note if charts couldn't be generated
            story.append(Paragraph("Note: Additional charts could not be generated due to data format issues.", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Power_Quality_Analysis_Report_{transformer_number}.pdf'
        )
    
    def create_voltage_chart(self, df, voltage_columns, title="Voltage Profile"):
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
    
    def create_current_chart(self, df, current_columns, title="Current Profile"):
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
    
    def create_power_factor_chart(self, df, pf_columns, title="Power Factor Profile"):
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
    
    def save_chart_to_buffer(self, fig):
        """Save matplotlib figure to BytesIO buffer"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close(fig)
        return buffer
