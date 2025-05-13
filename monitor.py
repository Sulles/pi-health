#!/usr/bin/env python3
import os
import time
import sqlite3
import logging
import psutil
import datetime
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pi_health_monitor')

class HealthMonitor:
    def __init__(self, db_path='pi_health.db', interval=60):
        """
        Initialize the health monitor
        
        Args:
            db_path: Path to SQLite database
            interval: Monitoring interval in seconds
        """
        self.db_path = db_path
        self.interval = interval
        self.setup_database()
        
    def setup_database(self):
        """Create the SQLite database and tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create health metrics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cpu_percent REAL,
            memory_percent REAL,
            disk_percent REAL,
            temperature REAL,
            cpu_frequency REAL,
            uptime REAL
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database setup complete at {self.db_path}")
    
    def get_cpu_temperature(self):
        """Get CPU temperature in Celsius"""
        try:
            # Raspberry Pi specific temperature file
            temp_file = "/sys/class/thermal/thermal_zone0/temp"
            if os.path.exists(temp_file):
                with open(temp_file, "r") as f:
                    temp = float(f.read()) / 1000.0
                return temp
            return None
        except Exception as e:
            logger.error(f"Error getting CPU temperature: {e}")
            return None
    
    def get_system_metrics(self):
        """Collect system health metrics"""
        metrics = {
            'timestamp': datetime.datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'temperature': self.get_cpu_temperature(),
            'cpu_frequency': psutil.cpu_freq().current if psutil.cpu_freq() else None,
            'uptime': time.time() - psutil.boot_time()
        }
        return metrics
    
    def log_metrics(self, metrics):
        """Log metrics to the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO health_metrics (
            timestamp, cpu_percent, memory_percent, disk_percent, 
            temperature, cpu_frequency, uptime
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics['timestamp'],
            metrics['cpu_percent'],
            metrics['memory_percent'],
            metrics['disk_percent'],
            metrics['temperature'],
            metrics['cpu_frequency'],
            metrics['uptime']
        ))
        
        conn.commit()
        conn.close()
    
    def run(self):
        """Main monitoring loop"""
        logger.info(f"Starting health monitoring with {self.interval}s interval")
        
        try:
            while True:
                metrics = self.get_system_metrics()
                self.log_metrics(metrics)
                logger.debug(f"Logged metrics: {metrics}")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")

def main():
    parser = argparse.ArgumentParser(description='Raspberry Pi Health Monitor')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    parser.add_argument('--db', type=str, default='pi_health.db', help='SQLite database path')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default='INFO', help='Set the logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logger.setLevel(getattr(logging, args.log_level))
    
    # Create the monitor
    monitor = HealthMonitor(
        db_path=args.db,
        interval=args.interval
    )
    
    # Run monitoring loop
    monitor.run()

if __name__ == "__main__":
    main()
