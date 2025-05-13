import unittest
import os
import sqlite3
import datetime
from unittest.mock import patch, MagicMock

# Import the classes to test
from db import HealthDatabase, Metrics


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
            cpu_frequency=1500.0
        )
        
        # Verify all attributes are correctly set
        self.assertEqual(metrics.timestamp, "2023-01-01T12:00:00")
        self.assertEqual(metrics.cpu_percent, 25.5)
        self.assertEqual(metrics.memory_percent, 40.2)
        self.assertEqual(metrics.disk_percent, 60.0)
        self.assertEqual(metrics.uptime, 3600)
        self.assertEqual(metrics.temperature, 50.5)
        self.assertEqual(metrics.cpu_frequency, 1500.0)
    
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
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        metrics = Metrics(
            timestamp="2023-01-01T12:00:00",
            cpu_percent=25.5,
            memory_percent=40.2,
            disk_percent=60.0,
            uptime=3600,
            temperature=50.5,
            cpu_frequency=1500.0
        )
        
        expected_dict = {
            'timestamp': "2023-01-01T12:00:00",
            'cpu_percent': 25.5,
            'memory_percent': 40.2,
            'disk_percent': 60.0,
            'uptime': 3600,
            'temperature': 50.5,
            'cpu_frequency': 1500.0
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
            'cpu_frequency': 1500.0
        }
        
        metrics = Metrics.from_dict(test_dict)
        
        self.assertEqual(metrics.timestamp, "2023-01-01T12:00:00")
        self.assertEqual(metrics.cpu_percent, 25.5)
        self.assertEqual(metrics.memory_percent, 40.2)
        self.assertEqual(metrics.disk_percent, 60.0)
        self.assertEqual(metrics.uptime, 3600)
        self.assertEqual(metrics.temperature, 50.5)
        self.assertEqual(metrics.cpu_frequency, 1500.0)
    
    def test_to_tuple(self):
        """Test conversion to tuple for database insertion"""
        metrics = Metrics(
            timestamp="2023-01-01T12:00:00",
            cpu_percent=25.5,
            memory_percent=40.2,
            disk_percent=60.0,
            uptime=3600,
            temperature=50.5,
            cpu_frequency=1500.0
        )
        
        expected_tuple = (
            "2023-01-01T12:00:00",
            25.5,
            40.2,
            60.0,
            50.5,
            1500.0,
            3600
        )
        
        self.assertEqual(metrics.to_tuple(), expected_tuple)


class TestHealthDatabase(unittest.TestCase):
    """Test cases for the HealthDatabase class"""
    
    def setUp(self):
        """Set up a test database before each test"""
        self.test_db_path = "test_pi_health.db"
        # Ensure the test database doesn't exist
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        # Create a new test database
        self.db = HealthDatabase(db_path=self.test_db_path)
    
    def tearDown(self):
        """Clean up after each test"""
        # Close any connections and remove the test database
        del self.db
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_setup_database(self):
        """Test that the database setup creates the expected structure"""
        # Connect to the database and verify the table exists
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Check if the health_metrics table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='health_metrics'
        """)
        
        table_exists = cursor.fetchone() is not None
        self.assertTrue(table_exists)
        
        # Check the table structure
        cursor.execute("PRAGMA table_info(health_metrics)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        # Verify all expected columns exist with correct types
        self.assertEqual(columns["timestamp"], "TEXT")
        self.assertEqual(columns["cpu_percent"], "REAL")
        self.assertEqual(columns["memory_percent"], "REAL")
        self.assertEqual(columns["disk_percent"], "REAL")
        self.assertEqual(columns["temperature"], "REAL")
        self.assertEqual(columns["cpu_frequency"], "REAL")
        self.assertEqual(columns["uptime"], "REAL")
        
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
            cpu_frequency=1500.0
        )
        
        # Log the metrics
        result = self.db.log_metrics(metrics)
        self.assertTrue(result)
        
        # Verify metrics were stored correctly
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM health_metrics")
        row = dict(cursor.fetchone())
        
        # Verify the stored values
        self.assertEqual(row["timestamp"], "2023-01-01T12:00:00")
        self.assertEqual(row["cpu_percent"], 25.5)
        self.assertEqual(row["memory_percent"], 40.2)
        self.assertEqual(row["disk_percent"], 60.0)
        self.assertEqual(row["uptime"], 3600)
        self.assertEqual(row["temperature"], 50.5)
        self.assertEqual(row["cpu_frequency"], 1500.0)
        
        conn.close()
    
    def test_get_recent_metrics(self):
        """Test retrieving recent metrics"""
        # Log multiple metrics
        for i in range(5):
            metrics = Metrics(
                timestamp=f"2023-01-0{i+1}T12:00:00",
                cpu_percent=25.0 + i,
                memory_percent=40.0 + i,
                disk_percent=60.0 + i,
                uptime=3600 + i * 100,
                temperature=50.0 + i,
                cpu_frequency=1500.0 + i * 10
            )
            self.db.log_metrics(metrics)
        
        # Get recent metrics with limit 3
        results = self.db.get_recent_metrics(limit=3)
        
        # Verify we got the expected number of results
        self.assertEqual(len(results), 3)
        
        # Verify the results are in descending timestamp order
        self.assertEqual(results[0]["timestamp"], "2023-01-05T12:00:00")
        self.assertEqual(results[1]["timestamp"], "2023-01-04T12:00:00")
        self.assertEqual(results[2]["timestamp"], "2023-01-03T12:00:00")
    
    def test_get_metrics_by_timespan(self):
        """Test retrieving metrics by timespan"""
        # This would need a more complex test since get_metrics_by_timespan uses current time
        # We can mock datetime to test this functionality
        
        # For now, we'll just verify that the method doesn't throw an error
        results = self.db.get_metrics_by_timespan(hours=24)
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main() 