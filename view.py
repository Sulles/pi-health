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
        tuple: (timestamps, metrics_dict) where timestamps is a list of datetime objects
               and metrics_dict contains lists of values for each metric
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
    
    # Return organized data
    metrics_dict = {
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'disk_percent': disk_percent,
        'temperature': temperature,
        'cpu_frequency': cpu_frequency
    }
    
    return timestamps, metrics_dict

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

def create_simple_dashboard(timestamps, metrics):
    """
    Create a simple dashboard with basic visualizations
    
    Args:
        timestamps: List of datetime objects
        metrics: Dictionary containing lists of metric values
        
    Returns:
        fig: Plotly figure object
    """
    # Get latest values for display
    latest = get_latest_values(metrics)
    
    # Create a basic 2x2 grid layout
    fig = sp.make_subplots(
        rows=2, 
        cols=2,
        subplot_titles=(
            "CPU & Memory Usage (%)",
            "Disk Usage & Temperature",
            "All Metrics Summary",
            "Latest Statistics"
        ),
        specs=[
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "table"}]
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
    
    # Bottom left: All metrics summary
    # Sample data to avoid overcrowding if we have too many points
    if len(timestamps) > 30:
        indices = get_evenly_spaced_indices(0, len(timestamps)-1, 30)
        sampled_times = [timestamps[i] for i in indices]
        sampled_cpu = [metrics['cpu_percent'][i] for i in indices]
        sampled_mem = [metrics['memory_percent'][i] for i in indices]
        sampled_disk = [metrics['disk_percent'][i] for i in indices]
        sampled_temp = [metrics['temperature'][i] if metrics['temperature'][i] is not None else 0 for i in indices] if has_temp_data else []
        sampled_freq = [metrics['cpu_frequency'][i] if metrics['cpu_frequency'][i] is not None else 0 for i in indices] 
    else:
        sampled_times = timestamps
        sampled_cpu = metrics['cpu_percent']
        sampled_mem = metrics['memory_percent']
        sampled_disk = metrics['disk_percent']
        sampled_temp = metrics['temperature'] if has_temp_data else []
        sampled_freq = metrics['cpu_frequency']
    
    # Add bar chart with CPU, Memory, and Disk usage
    fig.add_trace(
        go.Bar(
            x=sampled_times, 
            y=sampled_cpu, 
            name='CPU %',
            marker_color='#FF5733',
            opacity=0.7
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=sampled_times, 
            y=sampled_mem, 
            name='Memory %',
            marker_color='#33FF57',
            opacity=0.7
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=sampled_times, 
            y=sampled_disk, 
            name='Disk %',
            marker_color='#3357FF',
            opacity=0.7
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
    
    has_freq_data = any(f is not None for f in metrics['cpu_frequency'])
    if has_freq_data:
        latest_data.append(["CPU Frequency", f"{latest['cpu_frequency']:.0f} MHz"])
    
    latest_data.append(["Last Update", timestamps[-1].strftime("%Y-%m-%d %H:%M:%S")])
    
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
    
    # Update layout for better appearance
    fig.update_layout(
        title='Raspberry Pi Health Dashboard',
        height=800,
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
        row=2, col=1
    )
    
    # Update barmode to stack bars
    fig.update_layout(barmode='group')
    
    return fig

def create_dashboard(timestamps, metrics):
    """
    Create a dashboard with multiple metrics
    
    Args:
        timestamps: List of datetime objects
        metrics: Dictionary containing lists of metric values
        
    Returns:
        fig: Plotly figure object
    """
    # Create subplots: one row for each metric
    fig = sp.make_subplots(
        rows=5, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(
            "CPU Usage (%)", 
            "Memory Usage (%)", 
            "Disk Usage (%)", 
            "CPU Temperature (°C)",
            "CPU Frequency (MHz)"
        )
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
    
    # Update layout
    fig.update_layout(
        title='Raspberry Pi Health Metrics',
        height=1000,
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
        row=5, col=1
    )
    
    return fig

def create_summary_plot(timestamps, metrics):
    """
    Create a summary plot with all metrics on one graph
    
    Args:
        timestamps: List of datetime objects
        metrics: Dictionary containing lists of metric values
        
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
    
    args = parser.parse_args()
    
    # Load data
    timestamps, metrics = load_data(hours=args.hours, db_path=args.db)
    
    if len(timestamps) == 0:
        print(f"No data found for the last {args.hours} hours")
        return
        
    # Create figures based on view type
    if args.view in ['dashboard', 'all']:
        dashboard = create_dashboard(timestamps, metrics)
        if args.output:
            output_file = args.output if args.view == 'dashboard' else f"dashboard_{args.output}"
            dashboard.write_html(output_file)
        else:
            dashboard.show()
    
    if args.view in ['summary', 'all']:
        summary = create_summary_plot(timestamps, metrics)
        if args.output:
            output_file = args.output if args.view == 'summary' else f"summary_{args.output}"
            summary.write_html(output_file)
        else:
            summary.show()
            
    if args.view in ['simple', 'all']:
        simple = create_simple_dashboard(timestamps, metrics)
        if args.output:
            output_file = args.output if args.view == 'simple' else f"simple_{args.output}"
            simple.write_html(output_file)
        else:
            simple.show()

if __name__ == "__main__":
    main() 