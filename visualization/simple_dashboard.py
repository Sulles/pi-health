"""
Simple dashboard implementation for Pi Health visualizations.
"""

import plotly.graph_objects as go
import plotly.subplots as sp

from .base_dashboard import BaseDashboard
from .formatters import format_bytes, get_latest_values

class SimpleDashboard(BaseDashboard):
    """
    Simple dashboard implementation with a basic layout and key metrics.
    """
    
    def create_figure(self):
        """
        Create a simple dashboard with basic visualizations
        
        Returns:
            plotly.graph_objects.Figure: The created figure
        """
        # Get latest values for display
        latest = get_latest_values(self.metrics)
        
        # Add an extra row if we have network data
        rows = 3 if self.network_data else 2
        
        # Create a grid layout
        fig = sp.make_subplots(
            rows=rows, 
            cols=2,
            subplot_titles=(
                "CPU & Memory Usage (%)",
                "Disk Usage & Temperature",
                "Voltage & CPU Frequency", 
                "Latest Statistics",
                *([f"Network Traffic"] if self.network_data else [])
            ),
            specs=[
                [{"type": "xy"}, {"type": "xy"}],
                [{"type": "xy"}, {"type": "table"}],
                *([
                    [{"type": "xy", "colspan": 2}, None],
                  ] if self.network_data else [])
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.08,
        )
        
        # Top left: CPU and Memory
        fig.add_trace(
            go.Scatter(
                x=self.timestamps, 
                y=self.metrics['cpu_percent'], 
                mode='lines', 
                name='CPU %', 
                line=dict(width=2, color='#FF5733')
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=self.timestamps, 
                y=self.metrics['memory_percent'], 
                mode='lines', 
                name='Memory %', 
                line=dict(width=2, color='#33FF57')
            ),
            row=1, col=1
        )
        
        # Top right: Disk and Temperature
        fig.add_trace(
            go.Scatter(
                x=self.timestamps, 
                y=self.metrics['disk_percent'], 
                mode='lines', 
                name='Disk %', 
                line=dict(width=2, color='#3357FF')
            ),
            row=1, col=2
        )
        
        # Add temperature if available
        has_temp_data = self.has_data('temperature')
        if has_temp_data:
            fig.add_trace(
                go.Scatter(
                    x=self.timestamps, 
                    y=self.metrics['temperature'], 
                    mode='lines', 
                    name='Temperature (°C)', 
                    line=dict(width=2, color='#FF33A1')
                ),
                row=1, col=2
            )
        
        # Add voltage and frequency to the bottom left
        has_voltage_data = self.has_data('voltage')
        has_freq_data = self.has_data('cpu_frequency')
        
        if has_voltage_data:
            fig.add_trace(
                go.Scatter(
                    x=self.timestamps, 
                    y=self.metrics['voltage'], 
                    mode='lines', 
                    name='Voltage (V)', 
                    line=dict(width=2, color='#6A0DAD')
                ),
                row=2, col=1
            )
        
        if has_freq_data:
            fig.add_trace(
                go.Scatter(
                    x=self.timestamps, 
                    y=self.metrics['cpu_frequency'], 
                    mode='lines', 
                    name='CPU Freq (MHz)', 
                    line=dict(width=2, color='#FFA500'),
                    yaxis="y2"
                ),
                row=2, col=1
            )
        
        # Bottom right: Table with latest values
        latest_data = [
            ["CPU Usage", f"{latest['cpu_percent']:.1f}%"],
            ["Memory Usage", f"{latest['memory_percent']:.1f}%"],
            ["Disk Usage", f"{latest['disk_percent']:.1f}%"]
        ]
        
        if has_temp_data:
            latest_data.append(["Temperature", f"{latest['temperature']:.1f}°C"])
        
        if has_freq_data:
            latest_data.append(["CPU Frequency", f"{latest['cpu_frequency']:.0f} MHz"])
        
        if has_voltage_data:
            latest_data.append(["Voltage", f"{latest['voltage']:.4f} V"])
        
        latest_data.append(["Last Update", self.timestamps[-1].strftime("%Y-%m-%d %H:%M:%S")])
        
        # Add network stats if available
        if self.network_data:
            for interface, data in self.network_data.items():
                if data['bytes_sent'] and data['bytes_recv']:
                    latest_rx = data['bytes_recv'][-1]
                    latest_tx = data['bytes_sent'][-1]
                    latest_data.append([f"{interface} RX", f"{format_bytes(latest_rx)}"])
                    latest_data.append([f"{interface} TX", f"{format_bytes(latest_tx)}"])
        
        fig.add_trace(
            go.Table(
                header=dict(
                    values=["Metric", "Value"],
                    fill_color='#4472C4',
                    align='center',
                    font=dict(color='white', size=14)
                ),
                cells=dict(
                    values=list(zip(*latest_data)),  # Transpose data for table format
                    fill_color=['#E6F0FF', '#FFFFFF'],
                    align=['left', 'right'],
                    font=dict(size=13),
                    height=30
                )
            ),
            row=2, col=2
        )
        
        # Add network traffic visualization if available
        if self.network_data and rows > 2:
            # Find the interface with most traffic
            main_interface = self.get_main_network_interface()
            if main_interface:
                interface_data = self.network_data[main_interface]
                
                # Convert bytes to MB
                sent_mb = [b/1048576 for b in interface_data['bytes_sent']] if interface_data['bytes_sent'] else []
                recv_mb = [b/1048576 for b in interface_data['bytes_recv']] if interface_data['bytes_recv'] else []
                
                fig.add_trace(
                    go.Scatter(
                        x=interface_data['timestamps'], 
                        y=sent_mb,
                        mode='lines', 
                        name=f'{main_interface} TX (MB)', 
                        line=dict(width=2, color='#4CAF50')
                    ),
                    row=3, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=interface_data['timestamps'], 
                        y=recv_mb,
                        mode='lines', 
                        name=f'{main_interface} RX (MB)', 
                        line=dict(width=2, color='#2196F3')
                    ),
                    row=3, col=1
                )
        
        # Update layout for better appearance
        fig.update_layout(
            title='Raspberry Pi Health Dashboard',
            height=900 if self.network_data else 800,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_white",
            margin=dict(l=20, r=20, t=60, b=20),
        )
        
        # Update yaxis for both top charts
        fig.update_yaxes(title_text="Percentage (%)", row=1, col=1)
        
        if has_temp_data:
            # Create a secondary y-axis for temperature
            fig.update_yaxes(
                title_text="Disk (%) / Temperature (°C)",
                row=1, col=2
            )
        else:
            fig.update_yaxes(title_text="Disk Usage (%)", row=1, col=2)
        
        # Update yaxis for voltage/frequency graph
        if has_voltage_data:
            fig.update_yaxes(title_text="Voltage (V)", row=2, col=1)
        
        if has_freq_data and has_voltage_data:
            # Add a secondary y-axis for CPU frequency
            fig.update_layout(
                yaxis2=dict(
                    title="CPU Frequency (MHz)",
                    anchor="x",
                    overlaying="y3",
                    side="left"
                ),
                yaxis3=dict(
                    title="Voltage (V)",
                    anchor="x",
                    side="right"
                )
            )
        elif has_freq_data:
            fig.update_yaxes(title_text="CPU Frequency (MHz)", row=2, col=1)
        
        # Update yaxis for network chart if available
        if self.network_data and rows > 2:
            fig.update_yaxes(title_text="Data Transferred (MB)", row=3, col=1)
        
        # Add range selector to the bottom chart
        fig.update_xaxes(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1h", step="hour", stepmode="backward"),
                    dict(count=6, label="6h", step="hour", stepmode="backward"),
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            row=rows, col=1
        )
        
        return fig 