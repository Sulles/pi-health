"""
Utility functions for formatting data in visualizations.
"""

def format_bytes(bytes_value):
    """
    Format bytes to appropriate unit (KB, MB, GB)
    
    Args:
        bytes_value: Number of bytes to format
        
    Returns:
        str: Formatted string with appropriate unit
    """
    if bytes_value is None:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

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