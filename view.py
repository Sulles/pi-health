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
    parser.add_argument('--view', choices=['dashboard', 'summary', 'both'], default='both', 
                        help='View type: dashboard (separate plots), summary (all on one), or both')
    
    args = parser.parse_args()
    
    # Load data
    timestamps, metrics = load_data(hours=args.hours, db_path=args.db)
    
    if len(timestamps) == 0:
        print(f"No data found for the last {args.hours} hours")
        return
        
    # Create figures based on view type
    if args.view in ['dashboard', 'both']:
        dashboard = create_dashboard(timestamps, metrics)
        if args.output:
            output_file = args.output if args.view == 'dashboard' else f"dashboard_{args.output}"
            dashboard.write_html(output_file)
        else:
            dashboard.show()
    
    if args.view in ['summary', 'both']:
        summary = create_summary_plot(timestamps, metrics)
        if args.output:
            output_file = args.output if args.view == 'summary' else f"summary_{args.output}"
            summary.write_html(output_file)
        else:
            summary.show()

if __name__ == "__main__":
    main() 