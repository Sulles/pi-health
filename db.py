#!/usr/bin/env python3
import sqlite3
import logging
import datetime
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger('pi_health_monitor.db')

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
        cpu_frequency: Optional[float] = None
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
        """
        self.timestamp = timestamp
        self.cpu_percent = float(cpu_percent)
        self.memory_percent = float(memory_percent)
        self.disk_percent = float(disk_percent)
        self.uptime = float(uptime)
        self.temperature = float(temperature) if temperature is not None else None
        self.cpu_frequency = float(cpu_frequency) if cpu_frequency is not None else None
    
    @classmethod
    def get_column_names(cls) -> List[str]:
        """Return the column names for database operations"""
        return [
            "timestamp", "cpu_percent", "memory_percent", "disk_percent",
            "temperature", "cpu_frequency", "uptime"
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
            "uptime": "REAL"
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
            cpu_frequency=data.get('cpu_frequency')
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
            'uptime': self.uptime
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
            self.uptime
        )

class HealthDatabase:
    def __init__(self, db_path='pi_health.db'):
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
        CREATE TABLE IF NOT EXISTS health_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {Metrics.get_schema_definitions()}
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database setup complete at {self.db_path}")
    
    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def log_metrics(self, metrics: Metrics) -> bool:
        """
        Log metrics to the SQLite database
        
        Args:
            metrics: Either a Metrics object or a dictionary containing system metrics
            
        Returns:
            bool: True if metrics were successfully logged, False otherwise
        """
        try:
            assert isinstance(metrics, Metrics), "metrics must be a Metrics object"

            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(f'''
            INSERT INTO health_metrics (
                {Metrics.get_column_names_sql()}
            ) VALUES ({Metrics.get_placeholders()})
            ''', metrics.to_tuple())
            
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
        
        cursor.execute('''
        SELECT * FROM health_metrics 
        ORDER BY timestamp DESC 
        LIMIT ?
        ''', (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
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
        
        cursor.execute('''
        SELECT * FROM health_metrics 
        WHERE timestamp > datetime('now', '-' || ? || ' hours')
        ORDER BY timestamp
        ''', (hours,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results 