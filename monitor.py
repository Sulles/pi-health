#!/usr/bin/env python3
import os
import time
import logging
import psutil
import datetime
import argparse
import subprocess
import json

# Import our database module
from db import HealthDatabase, Metrics, DB_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pi_health_monitor')

class HealthMonitor:
    def __init__(self, interval=60, db_path=DB_PATH):
        """
        Initialize the health monitor
        
        Args:
            interval: Monitoring interval in seconds
            db_path: Path to SQLite database
        """
        self.interval = interval
        self.db = HealthDatabase(db_path=db_path)
        
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
    
    def get_voltage(self):
        """Get core voltage information"""
        try:
            # Use vcgencmd to get voltage information
            result = subprocess.run(['vcgencmd', 'measure_volts', 'core'], 
                                   capture_output=True, text=True, check=True)
            # Parse the output which is in the format "volt=1.2345V"
            voltage_str = result.stdout.strip()
            if voltage_str.startswith('volt='):
                # Extract the numeric part and remove the 'V' at the end
                voltage = float(voltage_str[5:-1])
                return voltage
            return None
        except (subprocess.SubprocessError, ValueError, FileNotFoundError) as e:
            logger.error(f"Error getting voltage information: {e}")
            return None
    
    def get_network_stats(self):
        """Get network I/O statistics
        
        Returns:
            dict: Dictionary mapping interface names to network statistics dictionaries
        """
        try:
            # Get network counters for all interfaces
            net_io = psutil.net_io_counters(pernic=True)
            
            # Convert to a format that can be stored in the database
            stats = {}
            for interface, counters in net_io.items():
                stats[interface] = {
                    "bytes_sent": counters.bytes_sent,
                    "bytes_recv": counters.bytes_recv,
                    "packets_sent": counters.packets_sent,
                    "packets_recv": counters.packets_recv,
                    "errin": counters.errin,
                    "errout": counters.errout,
                    "dropin": counters.dropin,
                    "dropout": counters.dropout
                }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting network statistics: {e}")
            return None
    
    def get_system_metrics(self):
        """
        Collect system health metrics
        
        Returns:
            Metrics: A Metrics object with current system data
        """
        # Get CPU frequency if available
        cpu_freq = psutil.cpu_freq()
        cpu_frequency = cpu_freq.current if cpu_freq else None
        
        # Create metrics object directly
        return Metrics(
            timestamp=datetime.datetime.now().isoformat(),
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=psutil.virtual_memory().percent,
            disk_percent=psutil.disk_usage('/').percent,
            temperature=self.get_cpu_temperature(),
            cpu_frequency=cpu_frequency,
            uptime=time.time() - psutil.boot_time(),
            voltage=self.get_voltage()
        )
    
    def run(self):
        """Main monitoring loop"""
        logger.info(f"Starting health monitoring with {self.interval}s interval")
        
        try:
            while True:
                # Get metrics
                metrics = self.get_system_metrics()
                
                # Get network stats
                network_stats = self.get_network_stats()
                
                # Log both to the database
                if self.db.log_metrics(metrics, network_stats):
                    logger.debug(f"Logged metrics: {metrics.to_dict()}")
                else:
                    logger.error("Failed to log metrics")
                
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")

def main():
    parser = argparse.ArgumentParser(description='Raspberry Pi Health Monitor')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    parser.add_argument('--db', type=str, default=DB_PATH, help='SQLite database path')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default='INFO', help='Set the logging level')
    
    args = parser.parse_args()
    
    # Set log level
    logger.setLevel(getattr(logging, args.log_level))
    
    # Create the monitor
    monitor = HealthMonitor(
        interval=args.interval,
        db_path=args.db
    )
    
    # Run monitoring loop
    monitor.run()

if __name__ == "__main__":
    main()
