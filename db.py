#!/usr/bin/env python3
import sqlite3
import logging
import datetime
import os
from typing import Dict, Any, Optional, List, Union, Tuple

logger = logging.getLogger('pi_health_monitor.db')

# Define database paths as constants
DB_PATH = 'pi-health.db'
TEST_DB_PATH = 'test_pi_health.db'

# Database configuration
DB_CONFIG = {
    'metrics_table': 'health_metrics',
    'network_table': 'network_stats'
}

class NetworkStats:
    """Class representing network statistics for a single interface"""
    
    def __init__(
        self,
        metric_id: int,
        interface: str,
        bytes_sent: int,
        bytes_recv: int,
        packets_sent: int,
        packets_recv: int,
        errin: int,
        errout: int,
        dropin: int,
        dropout: int
    ):
        """
        Initialize a network stats object
        
        Args:
            metric_id: Foreign key to the health_metrics table
            interface: Network interface name
            bytes_sent: Number of bytes sent
            bytes_recv: Number of bytes received
            packets_sent: Number of packets sent
            packets_recv: Number of packets received
            errin: Number of input errors
            errout: Number of output errors
            dropin: Number of input drops
            dropout: Number of output drops
        """
        self.metric_id = metric_id
        self.interface = interface
        self.bytes_sent = bytes_sent
        self.bytes_recv = bytes_recv
        self.packets_sent = packets_sent
        self.packets_recv = packets_recv
        self.errin = errin
        self.errout = errout
        self.dropin = dropin
        self.dropout = dropout
    
    @classmethod
    def get_column_names(cls) -> List[str]:
        """Return the column names for database operations"""
        return [
            "metric_id", "interface", "bytes_sent", "bytes_recv", 
            "packets_sent", "packets_recv", "errin", "errout",
            "dropin", "dropout"
        ]
    
    @classmethod
    def get_column_types(cls) -> Dict[str, str]:
        """Return the column types for database schema creation"""
        return {
            "metric_id": "INTEGER NOT NULL",
            "interface": "TEXT NOT NULL",
            "bytes_sent": "INTEGER",
            "bytes_recv": "INTEGER",
            "packets_sent": "INTEGER",
            "packets_recv": "INTEGER",
            "errin": "INTEGER",
            "errout": "INTEGER",
            "dropin": "INTEGER",
            "dropout": "INTEGER"
        }
    
    @classmethod
    def get_schema_definitions(cls) -> str:
        """Return the column definitions for database schema creation"""
        types = cls.get_column_types()
        return ", ".join([f"{col} {types[col]}" for col in cls.get_column_names()])
    
    @classmethod
    def get_column_names_sql(cls) -> str:
        """Return the column names as a SQL-ready string for database operations"""
        return ", ".join(cls.get_column_names())
    
    @classmethod
    def get_placeholders(cls) -> str:
        """Return the placeholders for SQL prepared statements"""
        return ", ".join(["?" for _ in cls.get_column_names()])
    
    def to_tuple(self) -> tuple:
        """Convert the network stats object to a tuple for database insertion"""
        return (
            self.metric_id,
            self.interface,
            self.bytes_sent,
            self.bytes_recv,
            self.packets_sent,
            self.packets_recv,
            self.errin,
            self.errout,
            self.dropin,
            self.dropout
        )

class Metrics:
    """Class representing system metrics with validation on initialization"""
    
    def __init__(
        self,
        timestamp: str,
        cpu_percent: float,
        memory_percent: float,
        disk_percent: float,
        uptime: float,
        temperature: Optional[float] = None,
        cpu_frequency: Optional[float] = None,
        voltage: Optional[float] = None
    ):
        """
        Initialize a metrics object with validation
        
        Args:
            timestamp: ISO format timestamp
            cpu_percent: CPU usage percentage (0-100)
            memory_percent: Memory usage percentage (0-100)
            disk_percent: Disk usage percentage (0-100)
            uptime: System uptime in seconds
            temperature: CPU temperature in Celsius (optional)
            cpu_frequency: CPU frequency in MHz (optional)
            voltage: Core voltage in Volts (optional)
        """
        self.timestamp = timestamp
        self.cpu_percent = float(cpu_percent)
        self.memory_percent = float(memory_percent)
        self.disk_percent = float(disk_percent)
        self.uptime = float(uptime)
        self.temperature = float(temperature) if temperature is not None else None
        self.cpu_frequency = float(cpu_frequency) if cpu_frequency is not None else None
        self.voltage = float(voltage) if voltage is not None else None
        self.id = None  # Will be set after database insertion
    
    @classmethod
    def get_column_names(cls) -> List[str]:
        """Return the column names for database operations"""
        return [
            "timestamp", "cpu_percent", "memory_percent", "disk_percent",
            "temperature", "cpu_frequency", "uptime", "voltage"
        ]
    
    @classmethod
    def get_column_types(cls) -> Dict[str, str]:
        """Return the column types for database schema creation"""
        return {
            "timestamp": "TEXT NOT NULL",
            "cpu_percent": "REAL",
            "memory_percent": "REAL",
            "disk_percent": "REAL",
            "temperature": "REAL",
            "cpu_frequency": "REAL",
            "uptime": "REAL",
            "voltage": "REAL"
        }
    
    @classmethod
    def get_schema_definitions(cls) -> str:
        """Return the column definitions for database schema creation"""
        types = cls.get_column_types()
        return ", ".join([f"{col} {types[col]}" for col in cls.get_column_names()])
    
    @classmethod
    def get_column_names_sql(cls) -> str:
        """Return the column names as a SQL-ready string for database operations"""
        return ", ".join(cls.get_column_names())
    
    @classmethod
    def get_placeholders(cls) -> str:
        """Return the placeholders for SQL prepared statements"""
        return ", ".join(["?" for _ in cls.get_column_names()])
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Metrics':
        """
        Create a Metrics object from a dictionary
        
        Args:
            data: Dictionary containing metrics data
            
        Returns:
            Metrics: A new Metrics object
            
        Raises:
            TypeError: If required fields are missing or have invalid types
            ValueError: If values cannot be converted to the required types
        """
        return cls(
            timestamp=data['timestamp'],
            cpu_percent=data['cpu_percent'],
            memory_percent=data['memory_percent'],
            disk_percent=data['disk_percent'],
            uptime=data['uptime'],
            temperature=data.get('temperature'),
            cpu_frequency=data.get('cpu_frequency'),
            voltage=data.get('voltage')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the metrics object to a dictionary"""
        return {
            'timestamp': self.timestamp,
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'disk_percent': self.disk_percent,
            'temperature': self.temperature,
            'cpu_frequency': self.cpu_frequency,
            'uptime': self.uptime,
            'voltage': self.voltage
        }
    
    def to_tuple(self) -> tuple:
        """Convert the metrics object to a tuple for database insertion"""
        return (
            self.timestamp,
            self.cpu_percent,
            self.memory_percent,
            self.disk_percent,
            self.temperature,
            self.cpu_frequency,
            self.uptime,
            self.voltage
        )

class HealthDatabase:
    def __init__(self, db_path=DB_PATH):
        """
        Initialize the database connection
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Create the SQLite database and tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create health metrics table
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {DB_CONFIG['metrics_table']} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {Metrics.get_schema_definitions()}
        )
        ''')
        
        # Create network stats table
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {DB_CONFIG['network_table']} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {NetworkStats.get_schema_definitions()},
            FOREIGN KEY (metric_id) REFERENCES {DB_CONFIG['metrics_table']}(id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database setup complete at {self.db_path}")
    
    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def log_metrics(self, metrics: Metrics, network_data: Dict[str, Dict[str, int]] = None) -> bool:
        """
        Log metrics to the SQLite database
        
        Args:
            metrics: Metrics object containing system metrics
            network_data: Dictionary mapping interface names to network statistics
            
        Returns:
            bool: True if metrics were successfully logged, False otherwise
        """
        try:
            assert isinstance(metrics, Metrics), "metrics must be a Metrics object"

            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Insert metrics
            cursor.execute(f'''
            INSERT INTO {DB_CONFIG['metrics_table']} (
                {Metrics.get_column_names_sql()}
            ) VALUES ({Metrics.get_placeholders()})
            ''', metrics.to_tuple())
            
            # Get the inserted row ID
            metrics.id = cursor.lastrowid
            
            # Insert network statistics if provided
            if network_data and metrics.id:
                for interface, stats in network_data.items():
                    net_stats = NetworkStats(
                        metric_id=metrics.id,
                        interface=interface,
                        bytes_sent=stats.get('bytes_sent', 0),
                        bytes_recv=stats.get('bytes_recv', 0),
                        packets_sent=stats.get('packets_sent', 0),
                        packets_recv=stats.get('packets_recv', 0),
                        errin=stats.get('errin', 0),
                        errout=stats.get('errout', 0),
                        dropin=stats.get('dropin', 0),
                        dropout=stats.get('dropout', 0)
                    )
                    
                    cursor.execute(f'''
                    INSERT INTO {DB_CONFIG['network_table']} (
                        {NetworkStats.get_column_names_sql()}
                    ) VALUES ({NetworkStats.get_placeholders()})
                    ''', net_stats.to_tuple())
            
            conn.commit()
            conn.close()
            return True
            
        except (TypeError, ValueError, KeyError) as e:
            logger.error(f"Metrics validation error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error logging metrics: {e}")
            return False
    
    def get_recent_metrics(self, limit=10) -> List[Dict[str, Any]]:
        """Get the most recent metrics from the database
        
        Args:
            limit (int): Maximum number of records to return
            
        Returns:
            list: List of dictionaries containing the metrics
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f'''
        SELECT * FROM {DB_CONFIG['metrics_table']} 
        ORDER BY timestamp DESC 
        LIMIT ?
        ''', (limit,))
        
        metrics_results = [dict(row) for row in cursor.fetchall()]
        
        # For each metric, get its network stats
        for metric in metrics_results:
            metric_id = metric['id']
            cursor.execute(f'''
            SELECT * FROM {DB_CONFIG['network_table']}
            WHERE metric_id = ?
            ''', (metric_id,))
            
            network_results = [dict(row) for row in cursor.fetchall()]
            metric['network_stats'] = network_results
        
        conn.close()
        
        return metrics_results
    
    def get_metrics_by_timespan(self, hours=24) -> List[Dict[str, Any]]:
        """Get metrics from the last specified hours
        
        Args:
            hours (int): Number of hours to look back
            
        Returns:
            list: List of dictionaries containing the metrics
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f'''
        SELECT * FROM {DB_CONFIG['metrics_table']} 
        WHERE timestamp > datetime('now', '-' || ? || ' hours')
        ORDER BY timestamp
        ''', (hours,))
        
        metrics_results = [dict(row) for row in cursor.fetchall()]
        
        # For each metric, get its network stats
        for metric in metrics_results:
            metric_id = metric['id']
            cursor.execute(f'''
            SELECT * FROM {DB_CONFIG['network_table']}
            WHERE metric_id = ?
            ''', (metric_id,))
            
            network_results = [dict(row) for row in cursor.fetchall()]
            metric['network_stats'] = network_results
        
        conn.close()
        
        return metrics_results
    
    def get_network_stats_for_interface(self, interface: str, hours=24) -> List[Dict[str, Any]]:
        """Get network statistics for a specific interface
        
        Args:
            interface (str): Network interface name (e.g., 'eth0', 'wlan0')
            hours (int): Number of hours to look back
            
        Returns:
            list: List of dictionaries containing the network statistics
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f'''
        SELECT n.*, m.timestamp
        FROM {DB_CONFIG['network_table']} n
        JOIN {DB_CONFIG['metrics_table']} m ON n.metric_id = m.id
        WHERE n.interface = ?
        AND m.timestamp > datetime('now', '-' || ? || ' hours')
        ORDER BY m.timestamp
        ''', (interface, hours))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results

# Helper function to create a test database instance
def get_test_db_instance():
    """Create a fresh test database instance for testing"""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    return HealthDatabase(db_path=TEST_DB_PATH) 