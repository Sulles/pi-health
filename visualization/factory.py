"""
Factory functions for creating various types of dashboards.
"""

from .simple_dashboard import SimpleDashboard
from .detailed_dash import DetailedDashboard
from .summary_plot import SummaryPlot

def create_dashboard(dashboard_type, timestamps, metrics, network_data=None):
    """
    Factory function to create a dashboard of the specified type
    
    Args:
        dashboard_type: Type of dashboard to create ('simple', 'detailed', 'summary')
        timestamps: List of datetime objects
        metrics: Dictionary containing lists of values for each metric
        network_data: Dictionary of network statistics by interface (optional)
        
    Returns:
        plotly.graph_objects.Figure: The created figure
    
    Raises:
        ValueError: If the dashboard type is not supported
    """
    if dashboard_type == 'simple':
        return SimpleDashboard(timestamps, metrics, network_data).create_figure()
    elif dashboard_type == 'detailed':
        return DetailedDashboard(timestamps, metrics, network_data).create_figure()
    elif dashboard_type == 'summary':
        return SummaryPlot(timestamps, metrics, network_data).create_figure()
    else:
        raise ValueError(f"Unsupported dashboard type: {dashboard_type}") 