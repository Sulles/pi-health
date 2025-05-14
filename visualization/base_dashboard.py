"""
Base dashboard class for Pi Health visualizations.
"""

class BaseDashboard:
    """Base class for all dashboard implementations"""
    
    def __init__(self, timestamps, metrics, network_data=None):
        """
        Initialize the base dashboard
        
        Args:
            timestamps: List of datetime objects
            metrics: Dictionary containing lists of values for each metric
            network_data: Dictionary of network statistics by interface (optional)
        """
        self.timestamps = timestamps
        self.metrics = metrics
        self.network_data = network_data
    
    def has_data(self, metric_name):
        """
        Check if a metric has valid data
        
        Args:
            metric_name: Name of the metric to check
            
        Returns:
            bool: True if the metric has valid data, False otherwise
        """
        return any(v is not None for v in self.metrics.get(metric_name, []))
    
    def get_main_network_interface(self):
        """
        Get the network interface with the most traffic
        
        Returns:
            str: Name of the main network interface, or None if no network data
        """
        if not self.network_data:
            return None
            
        return max(self.network_data.keys(), 
                  key=lambda x: sum(self.network_data[x]['bytes_sent']) + 
                               sum(self.network_data[x]['bytes_recv']) 
                               if self.network_data[x]['bytes_sent'] and 
                                  self.network_data[x]['bytes_recv'] else 0)
    
    def create_figure(self):
        """
        Create the visualization figure.
        To be implemented by subclasses.
        
        Returns:
            plotly.graph_objects.Figure: The created figure
        """
        raise NotImplementedError("Subclasses must implement create_figure()") 