import unittest
import os
import time
import json
from unittest.mock import patch, MagicMock, mock_open
import subprocess

# Import the class to test
from monitor import HealthMonitor
from db import Metrics, TEST_DB_PATH


class TestHealthMonitor(unittest.TestCase):
    """Test cases for the HealthMonitor class"""
    
    def setUp(self):
        """Set up before each test"""
        # Remove the test database if it exists and create a fresh monitor
        try:
            if os.path.exists(TEST_DB_PATH):
                os.remove(TEST_DB_PATH)
        except PermissionError:
            # If we can't remove it now, we'll try later
            pass
        
        # Create a monitor with a short interval for testing
        self.monitor = HealthMonitor(interval=1, db_path=TEST_DB_PATH)
    
    def tearDown(self):
        """Clean up after each test"""
        # Close any database connections
        db = getattr(self.monitor, 'db', None)
        if db:
            conn = getattr(db, '_connection', None)
            if conn:
                conn.close()
        
        # Remove the test database if it exists
        try:
            if os.path.exists(TEST_DB_PATH):
                os.remove(TEST_DB_PATH)
        except PermissionError:
            # We'll let the next test handle it
            pass
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.cpu_freq')
    @patch('psutil.boot_time')
    @patch('time.time')
    @patch('monitor.HealthMonitor.get_voltage')
    def test_get_system_metrics(self, mock_get_voltage, mock_time, mock_boot_time, mock_cpu_freq, 
                               mock_disk_usage, mock_virtual_memory, mock_cpu_percent):
        """Test getting system metrics"""
        # Mock the psutil functions
        mock_time.return_value = 3700  # Current time
        mock_boot_time.return_value = 100  # Boot time (3600 seconds ago)
        mock_get_voltage.return_value = 1.2  # Voltage
        
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
            self.assertEqual(metrics.voltage, 1.2)  # From mock
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
    
    def test_get_voltage(self):
        """Test getting voltage information"""
        # Create a test monitor
        monitor = self.monitor
        
        # Test successful case with a mock
        with patch('subprocess.run') as mock_run:
            # Mock successful call
            mock_process = MagicMock()
            mock_process.stdout = "volt=1.2345V"
            mock_run.return_value = mock_process
            
            # Call the method
            voltage = monitor.get_voltage()
            
            # Verify the voltage was correctly parsed
            self.assertEqual(voltage, 1.2345)
        
        # Test error case with a different mock
        with patch('subprocess.run') as mock_run:
            # Make subprocess.run raise an exception
            mock_run.side_effect = subprocess.SubprocessError("Command not found")
            
            # Call the method - it should handle the exception internally
            voltage = monitor.get_voltage()
            
            # Verify method returns None on error
            self.assertIsNone(voltage)
    
    @patch('psutil.net_io_counters')
    def test_get_network_stats(self, mock_net_io):
        """Test getting network statistics"""
        # Mock network I/O counters
        mock_net_io.return_value = {
            "eth0": MagicMock(
                bytes_sent=1000,
                bytes_recv=2000,
                packets_sent=10,
                packets_recv=20,
                errin=1,
                errout=2,
                dropin=3,
                dropout=4
            ),
            "wlan0": MagicMock(
                bytes_sent=5000,
                bytes_recv=6000,
                packets_sent=50,
                packets_recv=60,
                errin=5,
                errout=6,
                dropin=7,
                dropout=8
            )
        }
        
        # Call the method
        network_stats = self.monitor.get_network_stats()
        
        # Verify the network stats were correctly collected
        self.assertIsInstance(network_stats, dict)
        self.assertIn("eth0", network_stats)
        self.assertIn("wlan0", network_stats)
        
        # Check eth0 stats
        eth0_stats = network_stats["eth0"]
        self.assertEqual(eth0_stats["bytes_sent"], 1000)
        self.assertEqual(eth0_stats["bytes_recv"], 2000)
        self.assertEqual(eth0_stats["packets_sent"], 10)
        self.assertEqual(eth0_stats["packets_recv"], 20)
        
        # Check wlan0 stats
        wlan0_stats = network_stats["wlan0"]
        self.assertEqual(wlan0_stats["bytes_sent"], 5000)
        self.assertEqual(wlan0_stats["bytes_recv"], 6000)
        self.assertEqual(wlan0_stats["packets_sent"], 50)
        self.assertEqual(wlan0_stats["packets_recv"], 60)
        
        # Test error handling
        mock_net_io.side_effect = Exception("Network error")
        network_stats = self.monitor.get_network_stats()
        self.assertIsNone(network_stats)
    
    @patch('monitor.HealthMonitor.get_system_metrics')
    @patch('monitor.HealthMonitor.get_network_stats')
    @patch('time.sleep', side_effect=KeyboardInterrupt)  # Raise KeyboardInterrupt to stop the loop
    def test_run_keyboard_interrupt(self, mock_sleep, mock_get_network, mock_get_metrics):
        """Test that the run method handles keyboard interrupts"""
        # Mock the metrics and network stats
        mock_metrics = MagicMock()
        mock_network = {
            "eth0": {
                "bytes_sent": 1000,
                "bytes_recv": 2000,
                "packets_sent": 10,
                "packets_recv": 20,
                "errin": 1,
                "errout": 2,
                "dropin": 3,
                "dropout": 4
            }
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_network.return_value = mock_network
        
        # Patch the log_metrics method to avoid database operations
        with patch.object(self.monitor.db, 'log_metrics', return_value=True) as mock_log:
            # Should not raise an exception
            self.monitor.run()
            
            # Verify methods were called
            mock_get_metrics.assert_called_once()
            mock_get_network.assert_called_once()
            mock_log.assert_called_once_with(mock_metrics, mock_network)
    
    @patch('monitor.HealthMonitor.get_system_metrics')
    @patch('monitor.HealthMonitor.get_network_stats')
    @patch('time.sleep', side_effect=Exception("Test exception"))  # Raise an exception to test error handling
    def test_run_exception(self, mock_sleep, mock_get_network, mock_get_metrics):
        """Test that the run method handles general exceptions"""
        # Mock the metrics and network stats
        mock_metrics = MagicMock()
        mock_network = {
            "eth0": {
                "bytes_sent": 1000,
                "bytes_recv": 2000,
                "packets_sent": 10,
                "packets_recv": 20,
                "errin": 1,
                "errout": 2,
                "dropin": 3,
                "dropout": 4
            }
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_network.return_value = mock_network
        
        # Patch the log_metrics method to avoid database operations
        with patch.object(self.monitor.db, 'log_metrics', return_value=True) as mock_log:
            # Should not raise an exception
            self.monitor.run()
            
            # Verify methods were called
            mock_get_metrics.assert_called_once()
            mock_get_network.assert_called_once()
            mock_log.assert_called_once_with(mock_metrics, mock_network)


if __name__ == "__main__":
    unittest.main() 