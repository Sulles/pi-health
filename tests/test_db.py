import unittest
import os
import sqlite3
import datetime
from unittest.mock import patch, MagicMock

# Import the classes to test
from db import Metrics, NetworkStats, TEST_DB_PATH, DB_CONFIG, get_test_db_instance


class TestMetrics(unittest.TestCase):
    """Test cases for the Metrics class"""
    
    def test_initialization(self):
        """Test that a Metrics object can be properly initialized"""
        # Create a test metrics object
        metrics = Metrics(
            timestamp="2023-01-01T12:00:00",
            cpu_percent=25.5,
            memory_percent=40.2,
            disk_percent=60.0,
            uptime=3600,
            temperature=50.5,
            cpu_frequency=1500.0,
            voltage=1.2
        )
        
        # Verify all attributes are correctly set
        self.assertEqual(metrics.timestamp, "2023-01-01T12:00:00")
        self.assertEqual(metrics.cpu_percent, 25.5)
        self.assertEqual(metrics.memory_percent, 40.2)
        self.assertEqual(metrics.disk_percent, 60.0)
        self.assertEqual(metrics.uptime, 3600)
        self.assertEqual(metrics.temperature, 50.5)
        self.assertEqual(metrics.cpu_frequency, 1500.0)
        self.assertEqual(metrics.voltage, 1.2)
    
    def test_optional_fields(self):
        """Test that optional fields are properly handled"""
        # Create metrics without optional fields
        metrics = Metrics(
            timestamp="2023-01-01T12:00:00",
            cpu_percent=25.5,
            memory_percent=40.2,
            disk_percent=60.0,
            uptime=3600
        )
        
        # Verify optional fields are None
        self.assertIsNone(metrics.temperature)
        self.assertIsNone(metrics.cpu_frequency)
        self.assertIsNone(metrics.voltage)
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        metrics = Metrics(
            timestamp="2023-01-01T12:00:00",
            cpu_percent=25.5,
            memory_percent=40.2,
            disk_percent=60.0,
            uptime=3600,
            temperature=50.5,
            cpu_frequency=1500.0,
            voltage=1.2
        )
        
        expected_dict = {
            'timestamp': "2023-01-01T12:00:00",
            'cpu_percent': 25.5,
            'memory_percent': 40.2,
            'disk_percent': 60.0,
            'uptime': 3600,
            'temperature': 50.5,
            'cpu_frequency': 1500.0,
            'voltage': 1.2
        }
        
        self.assertEqual(metrics.to_dict(), expected_dict)
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        test_dict = {
            'timestamp': "2023-01-01T12:00:00",
            'cpu_percent': 25.5,
            'memory_percent': 40.2,
            'disk_percent': 60.0,
            'uptime': 3600,
            'temperature': 50.5,
            'cpu_frequency': 1500.0,
            'voltage': 1.2
        }
        
        metrics = Metrics.from_dict(test_dict)
        
        self.assertEqual(metrics.timestamp, "2023-01-01T12:00:00")
        self.assertEqual(metrics.cpu_percent, 25.5)
        self.assertEqual(metrics.memory_percent, 40.2)
        self.assertEqual(metrics.disk_percent, 60.0)
        self.assertEqual(metrics.uptime, 3600)
        self.assertEqual(metrics.temperature, 50.5)
        self.assertEqual(metrics.cpu_frequency, 1500.0)
        self.assertEqual(metrics.voltage, 1.2)
    
    def test_to_tuple(self):
        """Test conversion to tuple for database insertion"""
        metrics = Metrics(
            timestamp="2023-01-01T12:00:00",
            cpu_percent=25.5,
            memory_percent=40.2,
            disk_percent=60.0,
            uptime=3600,
            temperature=50.5,
            cpu_frequency=1500.0,
            voltage=1.2
        )
        
        expected_tuple = (
            "2023-01-01T12:00:00",
            25.5,
            40.2,
            60.0,
            50.5,
            1500.0,
            3600,
            1.2
        )
        
        self.assertEqual(metrics.to_tuple(), expected_tuple)


class TestNetworkStats(unittest.TestCase):
    """Test cases for the NetworkStats class"""
    
    def test_initialization(self):
        """Test that a NetworkStats object can be properly initialized"""
        # Create a test network stats object
        net_stats = NetworkStats(
            metric_id=1,
            interface="eth0",
            bytes_sent=1000,
            bytes_recv=2000,
            packets_sent=10,
            packets_recv=20,
            errin=1,
            errout=2,
            dropin=3,
            dropout=4
        )
        
        # Verify all attributes are correctly set
        self.assertEqual(net_stats.metric_id, 1)
        self.assertEqual(net_stats.interface, "eth0")
        self.assertEqual(net_stats.bytes_sent, 1000)
        self.assertEqual(net_stats.bytes_recv, 2000)
        self.assertEqual(net_stats.packets_sent, 10)
        self.assertEqual(net_stats.packets_recv, 20)
        self.assertEqual(net_stats.errin, 1)
        self.assertEqual(net_stats.errout, 2)
        self.assertEqual(net_stats.dropin, 3)
        self.assertEqual(net_stats.dropout, 4)
    
    def test_to_tuple(self):
        """Test conversion to tuple for database insertion"""
        net_stats = NetworkStats(
            metric_id=1,
            interface="eth0",
            bytes_sent=1000,
            bytes_recv=2000,
            packets_sent=10,
            packets_recv=20,
            errin=1,
            errout=2,
            dropin=3,
            dropout=4
        )
        
        expected_tuple = (
            1,
            "eth0",
            1000,
            2000,
            10,
            20,
            1,
            2,
            3,
            4
        )
        
        self.assertEqual(net_stats.to_tuple(), expected_tuple)


class TestHealthDatabase(unittest.TestCase):
    """Test cases for the HealthDatabase class"""
    
    def setUp(self):
        """Set up a test database before each test"""
        # Make sure any existing test DB is removed
        try:
            if os.path.exists(TEST_DB_PATH):
                os.remove(TEST_DB_PATH)
        except PermissionError:
            # If we can't remove it now, we'll try again later
            pass
            
        # Use the test database utility function
        self.db = get_test_db_instance()
        self.test_db_path = TEST_DB_PATH
    
    def tearDown(self):
        """Clean up after each test"""
        # Close any connections and remove the test database
        conn = getattr(self.db, '_connection', None)
        if conn:
            conn.close()
        del self.db
        
        # Try to remove the test DB
        try:
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
        except PermissionError:
            # We'll let the next test handle it
            pass
    
    def test_setup_database(self):
        """Test that the database setup creates the expected structure"""
        # Connect to the database and verify the tables exist
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Check if the health_metrics table exists
        cursor.execute(f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{DB_CONFIG['metrics_table']}'
        """)
        
        table_exists = cursor.fetchone() is not None
        self.assertTrue(table_exists)
        
        # Check if the network_stats table exists
        cursor.execute(f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{DB_CONFIG['network_table']}'
        """)
        
        table_exists = cursor.fetchone() is not None
        self.assertTrue(table_exists)
        
        # Check the metrics table structure
        cursor.execute(f"PRAGMA table_info({DB_CONFIG['metrics_table']})")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        # Verify all expected columns exist with correct types
        self.assertEqual(columns["timestamp"], "TEXT")
        self.assertEqual(columns["cpu_percent"], "REAL")
        self.assertEqual(columns["memory_percent"], "REAL")
        self.assertEqual(columns["disk_percent"], "REAL")
        self.assertEqual(columns["temperature"], "REAL")
        self.assertEqual(columns["cpu_frequency"], "REAL")
        self.assertEqual(columns["uptime"], "REAL")
        self.assertEqual(columns["voltage"], "REAL")
        
        # Check the network_stats table structure
        cursor.execute(f"PRAGMA table_info({DB_CONFIG['network_table']})")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        # Verify network stats columns
        self.assertEqual(columns["metric_id"], "INTEGER")
        self.assertEqual(columns["interface"], "TEXT")
        self.assertEqual(columns["bytes_sent"], "INTEGER")
        self.assertEqual(columns["bytes_recv"], "INTEGER")
        
        conn.close()
    
    def test_log_metrics(self):
        """Test logging metrics to the database"""
        # Create a test metrics object
        metrics = Metrics(
            timestamp="2023-01-01T12:00:00",
            cpu_percent=25.5,
            memory_percent=40.2,
            disk_percent=60.0,
            uptime=3600,
            temperature=50.5,
            cpu_frequency=1500.0,
            voltage=1.2
        )
        
        # Create test network data
        network_data = {
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
        
        # Log the metrics
        result = self.db.log_metrics(metrics, network_data)
        self.assertTrue(result)
        
        # Verify metrics were stored correctly
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {DB_CONFIG['metrics_table']}")
        row = dict(cursor.fetchone())
        
        # Verify the stored values
        self.assertEqual(row["timestamp"], "2023-01-01T12:00:00")
        self.assertEqual(row["cpu_percent"], 25.5)
        self.assertEqual(row["memory_percent"], 40.2)
        self.assertEqual(row["disk_percent"], 60.0)
        self.assertEqual(row["uptime"], 3600)
        self.assertEqual(row["temperature"], 50.5)
        self.assertEqual(row["cpu_frequency"], 1500.0)
        self.assertEqual(row["voltage"], 1.2)
        
        # Get the metric ID for checking network stats
        metric_id = row["id"]
        
        # Verify network stats were stored correctly
        cursor.execute(f"SELECT * FROM {DB_CONFIG['network_table']} WHERE metric_id = ?", (metric_id,))
        net_row = dict(cursor.fetchone())
        
        self.assertEqual(net_row["interface"], "eth0")
        self.assertEqual(net_row["bytes_sent"], 1000)
        self.assertEqual(net_row["bytes_recv"], 2000)
        self.assertEqual(net_row["packets_sent"], 10)
        self.assertEqual(net_row["packets_recv"], 20)
        
        conn.close()
    
    def test_get_recent_metrics(self):
        """Test retrieving recent metrics"""
        # Log multiple metrics with network data
        for i in range(5):
            metrics = Metrics(
                timestamp=f"2023-01-0{i+1}T12:00:00",
                cpu_percent=25.0 + i,
                memory_percent=40.0 + i,
                disk_percent=60.0 + i,
                uptime=3600 + i * 100,
                temperature=50.0 + i,
                cpu_frequency=1500.0 + i * 10,
                voltage=1.2 + i * 0.1
            )
            
            network_data = {
                f"eth{i}": {
                    "bytes_sent": 1000 * (i + 1),
                    "bytes_recv": 2000 * (i + 1),
                    "packets_sent": 10 * (i + 1),
                    "packets_recv": 20 * (i + 1),
                    "errin": i,
                    "errout": i,
                    "dropin": i,
                    "dropout": i
                }
            }
            
            self.db.log_metrics(metrics, network_data)
        
        # Get recent metrics with limit 3
        results = self.db.get_recent_metrics(limit=3)
        
        # Verify we got the expected number of results
        self.assertEqual(len(results), 3)
        
        # Verify the results are in descending timestamp order
        self.assertEqual(results[0]["timestamp"], "2023-01-05T12:00:00")
        self.assertEqual(results[1]["timestamp"], "2023-01-04T12:00:00")
        self.assertEqual(results[2]["timestamp"], "2023-01-03T12:00:00")
        
        # Check that network stats are included for each metric
        for result in results:
            self.assertIn("network_stats", result)
            self.assertIsInstance(result["network_stats"], list)
            if len(result["network_stats"]) > 0:
                net_stat = result["network_stats"][0]
                self.assertIn("interface", net_stat)
                self.assertIn("bytes_sent", net_stat)
    
    def test_get_network_stats_for_interface(self):
        """Test retrieving network stats for a specific interface"""
        # Log metrics with network data for a specific interface
        metrics = Metrics(
            timestamp=datetime.datetime.now().isoformat(),  # Use current timestamp instead of fixed past date
            cpu_percent=25.5,
            memory_percent=40.2,
            disk_percent=60.0,
            uptime=3600,
            temperature=50.5,
            cpu_frequency=1500.0,
            voltage=1.2
        )
        
        network_data = {
            "eth0": {
                "bytes_sent": 1000,
                "bytes_recv": 2000,
                "packets_sent": 10,
                "packets_recv": 20,
                "errin": 1,
                "errout": 2,
                "dropin": 3,
                "dropout": 4
            },
            "wlan0": {
                "bytes_sent": 5000,
                "bytes_recv": 6000,
                "packets_sent": 50,
                "packets_recv": 60,
                "errin": 5,
                "errout": 6,
                "dropin": 7,
                "dropout": 8
            }
        }
        
        self.db.log_metrics(metrics, network_data)
        
        # Verify data was actually saved by checking the metrics table
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {DB_CONFIG['metrics_table']}")
        metric_row = cursor.fetchone()
        self.assertIsNotNone(metric_row, "No metrics were saved to the database")
        
        # Check that network data was saved
        cursor.execute(f"SELECT * FROM {DB_CONFIG['network_table']}")
        all_net_rows = cursor.fetchall()
        self.assertGreater(len(all_net_rows), 0, "No network stats were saved to the database")
        
        # Get network stats for eth0 with a larger hours window
        results = self.db.get_network_stats_for_interface("eth0", hours=24*365)  # Use a full year to ensure test data is included
        
        # Verify we got the expected results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["interface"], "eth0")
        self.assertEqual(results[0]["bytes_sent"], 1000)
        self.assertEqual(results[0]["bytes_recv"], 2000)
        
        # Get network stats for wlan0
        results = self.db.get_network_stats_for_interface("wlan0", hours=24*365)  # Use a full year
        
        # Verify we got the expected results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["interface"], "wlan0")
        self.assertEqual(results[0]["bytes_sent"], 5000)
        self.assertEqual(results[0]["bytes_recv"], 6000)
        
        conn.close()


if __name__ == "__main__":
    unittest.main() 