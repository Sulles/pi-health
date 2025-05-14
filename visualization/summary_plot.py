"""
Summary plot implementation for Pi Health visualizations.
"""

import plotly.graph_objects as go

from .base_dashboard import BaseDashboard

class SummaryPlot(BaseDashboard):
    """
    Summary plot implementation showing all metrics on a single chart.
    """
    
    def create_figure(self):
        """
        Create a summary plot with all metrics on one graph
        
        Returns:
            plotly.graph_objects.Figure: The created figure
        """
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(x=self.timestamps, y=self.metrics['cpu_percent'], mode='lines', name='CPU %'))
        fig.add_trace(go.Scatter(x=self.timestamps, y=self.metrics['memory_percent'], mode='lines', name='Memory %'))
        fig.add_trace(go.Scatter(x=self.timestamps, y=self.metrics['disk_percent'], mode='lines', name='Disk %'))
        
        # Add temperature trace (if data exists)
        has_temp_data = self.has_data('temperature')
        if has_temp_data:
            fig.add_trace(go.Scatter(x=self.timestamps, y=self.metrics['temperature'], mode='lines', name='Temperature (°C)'))
        
        # Add CPU frequency trace (if data exists)
        has_freq_data = self.has_data('cpu_frequency')
        if has_freq_data:
            # Normalize CPU frequency to fit on the same scale (divide by 10)
            normalized_freq = [f/10 if f is not None else None for f in self.metrics['cpu_frequency']]
            fig.add_trace(go.Scatter(
                x=self.timestamps, 
                y=normalized_freq, 
                mode='lines', 
                name='CPU Freq (MHz/10)'
            ))
        
        # Add voltage trace (if data exists)
        has_voltage_data = self.has_data('voltage')
        if has_voltage_data:
            # Scale voltage to fit on the same graph (multiply by 10)
            scaled_voltage = [v*10 if v is not None else None for v in self.metrics['voltage']]
            fig.add_trace(go.Scatter(
                x=self.timestamps, 
                y=scaled_voltage, 
                mode='lines', 
                name='Voltage (V) × 10'
            ))
        
        # Add network data if available (only for the main interface)
        if self.network_data and len(self.network_data) > 0:
            # Find the interface with most traffic
            main_interface = self.get_main_network_interface()
            
            if main_interface:
                interface_data = self.network_data[main_interface]
                
                # Convert to MB and normalize to fit scale
                if interface_data['bytes_sent'] and interface_data['bytes_recv']:
                    # Normalized network traffic (MB / 10)
                    sent_mb = [b/(1048576*10) for b in interface_data['bytes_sent']]
                    recv_mb = [b/(1048576*10) for b in interface_data['bytes_recv']]
                    
                    fig.add_trace(go.Scatter(
                        x=interface_data['timestamps'], 
                        y=sent_mb,
                        mode='lines', 
                        name=f'{main_interface} TX (MB/10)', 
                        line=dict(dash='dot')
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=interface_data['timestamps'], 
                        y=recv_mb,
                        mode='lines', 
                        name=f'{main_interface} RX (MB/10)', 
                        line=dict(dash='dot')
                    ))
        
        fig.update_layout(
            title='Raspberry Pi Health Metrics Summary',
            xaxis_title='Time',
            yaxis_title='Value',
            legend=dict(x=0, y=1.1, orientation='h'),
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
            )
        )
        
        return fig 