#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path

# Import our database paths
from db import DB_PATH

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Pull health database from a Raspberry Pi')
    parser.add_argument('--host', type=str, default='rpi4', 
                       help='Hostname or IP address of the Raspberry Pi (default: rpi4)')
    parser.add_argument('--user', type=str, default='admin',
                       help='Username for SSH connection (default: admin)')
    parser.add_argument('--remote-path', type=str, default=DB_PATH,
                       help=f'Path to the database on the Raspberry Pi (default: {DB_PATH})')
    parser.add_argument('--local-path', type=str, default=f"~/GitHub/pi-health/{DB_PATH}",
                       help=f'Path to save the database locally (default: ~/GitHub/pi-health/{DB_PATH})')
    parser.add_argument('--port', type=int, default=22,
                       help='SSH port (default: 22)')
    parser.add_argument('--identity', type=str, 
                       help='Path to SSH identity file (optional)')
    
    return parser.parse_args()

def pull_database(host, user, remote_path, local_path, port=22, identity=None):
    """
    Pull the database file from the Raspberry Pi using SCP
    
    Args:
        host: Hostname or IP address of the Raspberry Pi
        user: Username for SSH connection
        remote_path: Path to the database on the Raspberry Pi
        local_path: Path to save the database locally
        port: SSH port (default: 22)
        identity: Path to SSH identity file (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Ensure the local directory exists
    local_dir = os.path.dirname(os.path.abspath(local_path))
    os.makedirs(local_dir, exist_ok=True)
    
    # Build the SCP command
    scp_cmd = ['scp']
    
    # Add port if not default
    if port != 22:
        scp_cmd.extend(['-P', str(port)])
    
    # Add identity file if provided
    if identity:
        scp_cmd.extend(['-i', identity])
    
    # Add source and destination
    source = f"{user}@{host}:{remote_path}"
    scp_cmd.extend([source, local_path])
    
    try:
        print(f"Pulling database from {host}...")
        result = subprocess.run(scp_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Successfully pulled database to {local_path}")
            return True
        else:
            print(f"Error pulling database: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Exception during database pull: {e}")
        return False

def main():
    args = parse_args()
    
    success = pull_database(
        host=args.host,
        user=args.user,
        remote_path=args.remote_path,
        local_path=args.local_path,
        port=args.port,
        identity=args.identity
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 