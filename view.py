#!/usr/bin/env python3
import plotly.graph_objects as go
import plotly.subplots as sp
import argparse
import datetime
from db import HealthDatabase, DB_PATH

def load_data(hours=24, db_path=DB_PATH):
    """
    Load data from the database into a list of dictionaries
    
    Args:
        hours: Number of hours of data to retrieve
        db_path: Path to SQLite database
        
    Returns:
        tuple: (timestamps, metrics_dict, network_data) where timestamps is a list of datetime objects,
               metrics_dict contains lists of values for each metric, and network_data contains
               network statistics by interface
    """
    db = HealthDatabase(db_path=db_path)
    raw_metrics = db.get_metrics_by_timespan(hours=hours)
    
    # Initialize lists to store data
    timestamps = []
    cpu_percent = []
    memory_percent = []
    disk_percent = []
    temperature = []
    cpu_frequency = []
    voltage = []  # New: voltage data
    
    # Initialize dictionaries for network data
    network_data = {}
    
    # Process the data
    for metric in raw_metrics:
        # Convert timestamp string to datetime object
        timestamp = datetime.datetime.fromisoformat(metric['timestamp'])
        timestamps.append(timestamp)
        
        # Extract metrics
        cpu_percent.append(metric['cpu_percent'])
        memory_percent.append(metric['memory_percent'])
        disk_percent.append(metric['disk_percent'])
        temperature.append(metric['temperature'])
        cpu_frequency.append(metric['cpu_frequency'])
        voltage.append(metric.get('voltage'))  # New: voltage data
        
        # Process network data if available
        if 'network_stats' in metric and metric['network_stats']:
            for net_stat in metric['network_stats']:
                interface = net_stat['interface']
                
                # Initialize interface data if not exists
                if interface not in network_data:
                    network_data[interface] = {
                        'timestamps': [],
                        'bytes_sent': [],
                        'bytes_recv': [],
                        'packets_sent': [],
                        'packets_recv': [],
                        'errin': [],
                        'errout': [],
                        'dropin': [],
                        'dropout': []
                    }
                
                # Add data for this timestamp
                network_data[interface]['timestamps'].append(timestamp)
                network_data[interface]['bytes_sent'].append(net_stat['bytes_sent'])
                network_data[interface]['bytes_recv'].append(net_stat['bytes_recv'])
                network_data[interface]['packets_sent'].append(net_stat['packets_sent'])
                network_data[interface]['packets_recv'].append(net_stat['packets_recv'])
                network_data[interface]['errin'].append(net_stat['errin'])
                network_data[interface]['errout'].append(net_stat['errout'])
                network_data[interface]['dropin'].append(net_stat['dropin'])
                network_data[interface]['dropout'].append(net_stat['dropout'])
    
    # Return organized data
    metrics_dict = {
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'disk_percent': disk_percent,
        'temperature': temperature,
        'cpu_frequency': cpu_frequency,
        'voltage': voltage  # New: voltage data
    }
    
    return timestamps, metrics_dict, network_data

def get_latest_values(metrics):
    """
    Get the latest values for each metric
    
    Args:
        metrics: Dictionary containing lists of metric values
        
    Returns:
        dict: Latest values for each metric
    """
    latest = {}
    for key, values in metrics.items():
        if values and values[-1] is not None:
            latest[key] = values[-1]
        else:
            latest[key] = 0
    return latest

def calculate_moving_average(values, window_size):
    """
    Calculate moving average without using numpy
    
    Args:
        values: List of values to calculate moving average
        window_size: Size of the moving window
        
    Returns:
        list: Moving average values
    """
    results = []
    for i in range(len(values) - window_size + 1):
        window = values[i:i + window_size]
        # Filter out None values
        valid_values = [v for v in window if v is not None]
        if valid_values:
            results.append(sum(valid_values) / len(valid_values))
        else:
            results.append(0)
    return results

def get_evenly_spaced_indices(start, end, num):
    """
    Get evenly spaced indices without using numpy
    
    Args:
        start: Start index
        end: End index
        num: Number of indices to generate
        
    Returns:
        list: Evenly spaced indices
    """
    if num <= 1:
        return [start]
    
    indices = []
    step = (end - start) / (num - 1)
    
    for i in range(num):
        index = int(start + i * step)
        indices.append(min(index, end))  # Ensure we don't exceed the end
        
    return indices

def create_simple_dashboard(timestamps, metrics, network_data=None):
    """
    Create a simple dashboard with basic visualizations
    
    Args:
        timestamps: List of datetime objects
        metrics: Dictionary containing lists of metric values
        network_data: Dictionary of network statistics by interface
        
    Returns:
        fig: Plotly figure object
    """
    # Get latest values for display
    latest = get_latest_values(metrics)
    
    # Add an extra row if we have network data
    rows = 3 if network_data else 2
    
    # Create a grid layout
    fig = sp.make_subplots(
        rows=rows, 
        cols=2,
        subplot_titles=(
            "CPU & Memory Usage (%)",
            "Disk Usage & Temperature",
            "Voltage & CPU Frequency", 
            "Latest Statistics",
            *([f"Network Traffic"] if network_data else [])
        ),
        specs=[
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "table"}],
            *([
                [{"type": "xy", "colspan": 2}, None],
              ] if network_data else [])
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )
    
    # Top left: CPU and Memory
    fig.add_trace(
        go.Scatter(
            x=timestamps, 
            y=metrics['cpu_percent'], 
            mode='lines', 
            name='CPU %', 
            line=dict(width=2, color='#FF5733')
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=timestamps, 
            y=metrics['memory_percent'], 
            mode='lines', 
            name='Memory %', 
            line=dict(width=2, color='#33FF57')
        ),
        row=1, col=1
    )
    
    # Top right: Disk and Temperature
    fig.add_trace(
        go.Scatter(
            x=timestamps, 
            y=metrics['disk_percent'], 
            mode='lines', 
            name='Disk %', 
            line=dict(width=2, color='#3357FF')
        ),
        row=1, col=2
    )
    
    # Add temperature if available
    has_temp_data = any(t is not None for t in metrics['temperature'])
    if has_temp_data:
        fig.add_trace(
            go.Scatter(
                x=timestamps, 
                y=metrics['temperature'], 
                mode='lines', 
                name='Temperature (°C)', 
                line=dict(width=2, color='#FF33A1')
            ),
            row=1, col=2
        )
    
    # Add voltage and frequency to the bottom left
    has_voltage_data = any(v is not None for v in metrics['voltage'])
    has_freq_data = any(f is not None for f in metrics['cpu_frequency'])
    
    if has_voltage_data:
        fig.add_trace(
            go.Scatter(
                x=timestamps, 
                y=metrics['voltage'], 
                mode='lines', 
                name='Voltage (V)', 
                line=dict(width=2, color='#6A0DAD')
            ),
            row=2, col=1
        )
    
    if has_freq_data:
        fig.add_trace(
            go.Scatter(
                x=timestamps, 
                y=metrics['cpu_frequency'], 
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
    
    latest_data.append(["Last Update", timestamps[-1].strftime("%Y-%m-%d %H:%M:%S")])
    
    # Add network stats if available
    if network_data:
        for interface, data in network_data.items():
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
    if network_data and rows > 2:
        # Find the interface with most traffic
        main_interface = max(network_data.keys(), 
                            key=lambda x: sum(network_data[x]['bytes_sent']) + 
                                         sum(network_data[x]['bytes_recv']) 
                                         if network_data[x]['bytes_sent'] and network_data[x]['bytes_recv'] else 0)
        
        interface_data = network_data[main_interface]
        
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
        height=900 if network_data else 800,
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
                side="right"
            ),
            yaxis3=dict(
                title="Voltage (V)",
                anchor="x",
                side="left"
            )
        )
    elif has_freq_data:
        fig.update_yaxes(title_text="CPU Frequency (MHz)", row=2, col=1)
    
    # Update yaxis for network chart if available
    if network_data and rows > 2:
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

def format_bytes(bytes_value):
    """
    Format bytes to appropriate unit (KB, MB, GB)
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def create_dashboard(timestamps, metrics, network_data=None):
    """
    Create a dashboard with multiple metrics
    
    Args:
        timestamps: List of datetime objects
        metrics: Dictionary containing lists of metric values
        network_data: Dictionary of network statistics by interface
        
    Returns:
        fig: Plotly figure object
    """
    # Calculate how many rows we need
    base_rows = 5  # CPU, Memory, Disk, Temperature, CPU Frequency
    has_voltage_data = any(v is not None for v in metrics['voltage'])
    voltage_row = 1 if has_voltage_data else 0
    network_rows = 1 if network_data else 0
    
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
    
    if network_data:
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
        go.Scatter(x=timestamps, y=metrics['cpu_percent'], mode='lines', name='CPU %'),
        row=1, col=1
    )
    
    # Add memory usage trace
    fig.add_trace(
        go.Scatter(x=timestamps, y=metrics['memory_percent'], mode='lines', name='Memory %'),
        row=2, col=1
    )
    
    # Add disk usage trace
    fig.add_trace(
        go.Scatter(x=timestamps, y=metrics['disk_percent'], mode='lines', name='Disk %'),
        row=3, col=1
    )
    
    # Add temperature trace (if data exists)
    has_temp_data = any(t is not None for t in metrics['temperature'])
    if has_temp_data:
        fig.add_trace(
            go.Scatter(x=timestamps, y=metrics['temperature'], mode='lines', name='Temperature'),
            row=4, col=1
        )
    
    # Add CPU frequency trace (if data exists)
    has_freq_data = any(f is not None for f in metrics['cpu_frequency'])
    if has_freq_data:
        fig.add_trace(
            go.Scatter(x=timestamps, y=metrics['cpu_frequency'], mode='lines', name='CPU Freq'),
            row=5, col=1
        )
    
    # Add voltage trace if available
    current_row = 6
    if has_voltage_data:
        fig.add_trace(
            go.Scatter(x=timestamps, y=metrics['voltage'], mode='lines', name='Voltage'),
            row=current_row, col=1
        )
        current_row += 1
    
    # Add network data if available
    if network_data and len(network_data) > 0:
        # Find the interface with most traffic
        main_interface = max(network_data.keys(), 
                            key=lambda x: sum(network_data[x]['bytes_sent']) + 
                                         sum(network_data[x]['bytes_recv']) 
                                         if network_data[x]['bytes_sent'] and network_data[x]['bytes_recv'] else 0)
        
        interface_data = network_data[main_interface]
        
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

def create_summary_plot(timestamps, metrics, network_data=None):
    """
    Create a summary plot with all metrics on one graph
    
    Args:
        timestamps: List of datetime objects
        metrics: Dictionary containing lists of metric values
        network_data: Dictionary of network statistics by interface
        
    Returns:
        fig: Plotly figure object
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(x=timestamps, y=metrics['cpu_percent'], mode='lines', name='CPU %'))
    fig.add_trace(go.Scatter(x=timestamps, y=metrics['memory_percent'], mode='lines', name='Memory %'))
    fig.add_trace(go.Scatter(x=timestamps, y=metrics['disk_percent'], mode='lines', name='Disk %'))
    
    # Add temperature trace (if data exists)
    has_temp_data = any(t is not None for t in metrics['temperature'])
    if has_temp_data:
        fig.add_trace(go.Scatter(x=timestamps, y=metrics['temperature'], mode='lines', name='Temperature (°C)'))
    
    # Add CPU frequency trace (if data exists)
    has_freq_data = any(f is not None for f in metrics['cpu_frequency'])
    if has_freq_data:
        # Normalize CPU frequency to fit on the same scale (divide by 10)
        normalized_freq = [f/10 if f is not None else None for f in metrics['cpu_frequency']]
        fig.add_trace(go.Scatter(
            x=timestamps, 
            y=normalized_freq, 
            mode='lines', 
            name='CPU Freq (MHz/10)'
        ))
    
    # Add voltage trace (if data exists)
    has_voltage_data = any(v is not None for v in metrics['voltage'])
    if has_voltage_data:
        # Scale voltage to fit on the same graph (multiply by 10)
        scaled_voltage = [v*10 if v is not None else None for v in metrics['voltage']]
        fig.add_trace(go.Scatter(
            x=timestamps, 
            y=scaled_voltage, 
            mode='lines', 
            name='Voltage (V) × 10'
        ))
    
    # Add network data if available (only for the main interface)
    if network_data and len(network_data) > 0:
        # Find the interface with most traffic
        main_interface = max(network_data.keys(), 
                            key=lambda x: sum(network_data[x]['bytes_sent']) + 
                                         sum(network_data[x]['bytes_recv']) 
                                         if network_data[x]['bytes_sent'] and network_data[x]['bytes_recv'] else 0)
        
        interface_data = network_data[main_interface]
        
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

def main():
    parser = argparse.ArgumentParser(description='View Raspberry Pi Health Metrics')
    parser.add_argument('--hours', type=int, default=24, help='Hours of data to display')
    parser.add_argument('--db', type=str, default=DB_PATH, help='SQLite database path')
    parser.add_argument('--output', type=str, help='Output HTML file (optional)')
    parser.add_argument('--view', choices=['dashboard', 'summary', 'simple', 'all'], default='simple', 
                        help='View type: dashboard (separate plots), summary (all on one), simple (basic dashboard), or all')
    parser.add_argument('--interface', type=str, help='Specific network interface to monitor (optional)')
    
    args = parser.parse_args()
    
    # Load data
    timestamps, metrics, network_data = load_data(hours=args.hours, db_path=args.db)
    
    if len(timestamps) == 0:
        print(f"No data found for the last {args.hours} hours")
        return
    
    # Filter network data if interface is specified
    if args.interface and network_data:
        if args.interface in network_data:
            network_data = {args.interface: network_data[args.interface]}
        else:
            print(f"Interface {args.interface} not found. Available interfaces: {', '.join(network_data.keys()) if network_data else 'none'}")
            if not network_data:
                network_data = None
        
    # Create figures based on view type
    if args.view in ['dashboard', 'all']:
        dashboard = create_dashboard(timestamps, metrics, network_data)
        if args.output:
            output_file = args.output if args.view == 'dashboard' else f"dashboard_{args.output}"
            dashboard.write_html(output_file)
        else:
            dashboard.show()
    
    if args.view in ['summary', 'all']:
        summary = create_summary_plot(timestamps, metrics, network_data)
        if args.output:
            output_file = args.output if args.view == 'summary' else f"summary_{args.output}"
            summary.write_html(output_file)
        else:
            summary.show()
            
    if args.view in ['simple', 'all']:
        simple = create_simple_dashboard(timestamps, metrics, network_data)
        if args.output:
            output_file = args.output if args.view == 'simple' else f"simple_{args.output}"
            simple.write_html(output_file)
        else:
            simple.show()

if __name__ == "__main__":
    main() 