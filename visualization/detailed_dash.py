"""
Detailed dashboard implementation for Pi Health visualizations.
"""

import plotly.graph_objects as go
import plotly.subplots as sp

from .base_dashboard import BaseDashboard

class DetailedDashboard(BaseDashboard):
    """
    Detailed dashboard implementation with separate plots for each metric.
    """
    
    def create_figure(self):
        """
        Create a dashboard with multiple metrics, each on its own row
        
        Returns:
            plotly.graph_objects.Figure: The created figure
        """
        # Calculate how many rows we need
        base_rows = 5  # CPU, Memory, Disk, Temperature, CPU Frequency
        has_voltage_data = self.has_data('voltage')
        voltage_row = 1 if has_voltage_data else 0
        network_rows = 1 if self.network_data else 0
        
        total_rows = base_rows + voltage_row + network_rows
        
        # Create subplots: one row for each metric
        row_titles = [
            "CPU Usage (%)", 
            "Memory Usage (%)", 
            "Disk Usage (%)", 
            "CPU Temperature (°C)",
            "CPU Frequency (MHz)"
        ]
        
        if has_voltage_data:
            row_titles.append("Voltage (V)")
        
        if self.network_data:
            row_titles.append("Network Traffic (MB)")
        
        fig = sp.make_subplots(
            rows=total_rows, 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=row_titles
        )
        
        # Add CPU usage trace
        fig.add_trace(
            go.Scatter(x=self.timestamps, y=self.metrics['cpu_percent'], mode='lines', name='CPU %'),
            row=1, col=1
        )
        
        # Add memory usage trace
        fig.add_trace(
            go.Scatter(x=self.timestamps, y=self.metrics['memory_percent'], mode='lines', name='Memory %'),
            row=2, col=1
        )
        
        # Add disk usage trace
        fig.add_trace(
            go.Scatter(x=self.timestamps, y=self.metrics['disk_percent'], mode='lines', name='Disk %'),
            row=3, col=1
        )
        
        # Add temperature trace (if data exists)
        has_temp_data = self.has_data('temperature')
        if has_temp_data:
            fig.add_trace(
                go.Scatter(x=self.timestamps, y=self.metrics['temperature'], mode='lines', name='Temperature'),
                row=4, col=1
            )
        
        # Add CPU frequency trace (if data exists)
        has_freq_data = self.has_data('cpu_frequency')
        if has_freq_data:
            fig.add_trace(
                go.Scatter(x=self.timestamps, y=self.metrics['cpu_frequency'], mode='lines', name='CPU Freq'),
                row=5, col=1
            )
        
        # Add voltage trace if available
        current_row = 6
        if has_voltage_data:
            fig.add_trace(
                go.Scatter(x=self.timestamps, y=self.metrics['voltage'], mode='lines', name='Voltage'),
                row=current_row, col=1
            )
            current_row += 1
        
        # Add network data if available
        if self.network_data and len(self.network_data) > 0:
            # Find the interface with most traffic
            main_interface = self.get_main_network_interface()
            
            if main_interface:
                interface_data = self.network_data[main_interface]
                
                # Convert bytes to MB
                sent_mb = [b/1048576 for b in interface_data['bytes_sent']] if interface_data['bytes_sent'] else []
                recv_mb = [b/1048576 for b in interface_data['bytes_recv']] if interface_data['bytes_recv'] else []
                
                # Add network traces
                if sent_mb and recv_mb:
                    fig.add_trace(
                        go.Scatter(
                            x=interface_data['timestamps'], 
                            y=sent_mb,
                            mode='lines', 
                            name=f'{main_interface} TX (MB)', 
                            line=dict(width=2, color='#4CAF50')
                        ),
                        row=current_row, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=interface_data['timestamps'], 
                            y=recv_mb,
                            mode='lines', 
                            name=f'{main_interface} RX (MB)', 
                            line=dict(width=2, color='#2196F3')
                        ),
                        row=current_row, col=1
                    )
        
        # Update layout
        fig.update_layout(
            title='Raspberry Pi Health Metrics',
            height=150 * total_rows,  # Adjust height based on number of rows
            legend_tracegroupgap=180,
            hovermode='x unified'
        )
        
        # Add range selector
        fig.update_xaxes(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1h", step="hour", stepmode="backward"),
                    dict(count=6, label="6h", step="hour", stepmode="backward"),
                    dict(count=12, label="12h", step="hour", stepmode="backward"),
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            row=total_rows, col=1
        )
        
        return fig 