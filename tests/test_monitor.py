import unittest
import os
import time
from unittest.mock import patch, MagicMock, mock_open

# Import the class to test
from monitor import HealthMonitor
from db import Metrics


class TestHealthMonitor(unittest.TestCase):
    """Test cases for the HealthMonitor class"""
    
    def setUp(self):
        """Set up before each test"""
        # Create a test database path
        self.test_db_path = "test_pi_health.db"
        # Remove the test database if it exists
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        # Create a monitor with a short interval for testing
        self.monitor = HealthMonitor(db_path=self.test_db_path, interval=1)
    
    def tearDown(self):
        """Clean up after each test"""
        # Remove the test database if it exists
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.cpu_freq')
    @patch('psutil.boot_time')
    @patch('time.time')
    def test_get_system_metrics(self, mock_time, mock_boot_time, mock_cpu_freq, 
                               mock_disk_usage, mock_virtual_memory, mock_cpu_percent):
        """Test getting system metrics"""
        # Mock the psutil functions
        mock_time.return_value = 3700  # Current time
        mock_boot_time.return_value = 100  # Boot time (3600 seconds ago)
        
        # Mock CPU frequency
        mock_cpu_freq_obj = MagicMock()
        mock_cpu_freq_obj.current = 1500.0
        mock_cpu_freq.return_value = mock_cpu_freq_obj
        
        # Mock disk usage
        mock_disk_obj = MagicMock()
        mock_disk_obj.percent = 60.0
        mock_disk_usage.return_value = mock_disk_obj
        
        # Mock memory usage
        mock_memory_obj = MagicMock()
        mock_memory_obj.percent = 40.0
        mock_virtual_memory.return_value = mock_memory_obj
        
        # Mock CPU percent
        mock_cpu_percent.return_value = 25.0
        
        # Mock the temperature file
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # Simulate no temperature file
            
            # Get system metrics
            metrics = self.monitor.get_system_metrics()
            
            # Verify the metrics
            self.assertIsInstance(metrics, Metrics)
            self.assertEqual(metrics.cpu_percent, 25.0)
            self.assertEqual(metrics.memory_percent, 40.0)
            self.assertEqual(metrics.disk_percent, 60.0)
            self.assertEqual(metrics.cpu_frequency, 1500.0)
            self.assertEqual(metrics.uptime, 3600)  # time.time() - boot_time
            self.assertIsNone(metrics.temperature)  # No temperature file
    
    @patch('monitor.HealthMonitor.get_cpu_temperature')
    def test_get_cpu_temperature(self, mock_get_temp):
        """Test getting CPU temperature"""
        # Test when temperature file exists
        mock_get_temp.return_value = 50.5
        
        temp = self.monitor.get_cpu_temperature()
        self.assertEqual(temp, 50.5)
        
        # Test when temperature file doesn't exist or has an error
        mock_get_temp.return_value = None
        
        temp = self.monitor.get_cpu_temperature()
        self.assertIsNone(temp)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="50500")
    def test_get_cpu_temperature_with_file(self, mock_file, mock_exists):
        """Test reading CPU temperature from file"""
        # Mock that the temperature file exists
        mock_exists.return_value = True
        
        # Call the method
        temp = self.monitor.get_cpu_temperature()
        
        # Verify the temperature was read correctly and converted
        self.assertEqual(temp, 50.5)  # 50500 / 1000
        
        # Test error handling
        mock_file.side_effect = Exception("Test error")
        temp = self.monitor.get_cpu_temperature()
        self.assertIsNone(temp)
    
    @patch('monitor.HealthMonitor.get_system_metrics')
    @patch('time.sleep', side_effect=KeyboardInterrupt)  # Raise KeyboardInterrupt to stop the loop
    def test_run_keyboard_interrupt(self, mock_sleep, mock_get_metrics):
        """Test that the run method handles keyboard interrupts"""
        # Mock the get_system_metrics method
        mock_metrics = MagicMock()
        mock_get_metrics.return_value = mock_metrics
        
        # Should not raise an exception
        self.monitor.run()
        
        # Verify get_system_metrics was called
        mock_get_metrics.assert_called_once()
    
    @patch('monitor.HealthMonitor.get_system_metrics')
    @patch('time.sleep', side_effect=Exception("Test exception"))  # Raise an exception to test error handling
    def test_run_exception(self, mock_sleep, mock_get_metrics):
        """Test that the run method handles general exceptions"""
        # Mock the get_system_metrics method
        mock_metrics = MagicMock()
        mock_get_metrics.return_value = mock_metrics
        
        # Should not raise an exception
        self.monitor.run()
        
        # Verify get_system_metrics was called
        mock_get_metrics.assert_called_once()


if __name__ == "__main__":
    unittest.main() 