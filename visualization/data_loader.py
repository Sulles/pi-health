"""
Data loading functions for the Pi Health Visualization package.
"""

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

def filter_network_data(network_data, interface):
    """
    Filter network data to only include a specific interface
    
    Args:
        network_data: Dictionary of network data by interface
        interface: Interface name to filter for
        
    Returns:
        dict: Filtered network data
    """
    if not network_data or not interface:
        return network_data
        
    if interface in network_data:
        return {interface: network_data[interface]}
    
    return {} 