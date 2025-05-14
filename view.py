#!/usr/bin/env python3
"""
Main entry point for the Pi Health visualization tools.

This script provides a command-line interface for viewing metrics
collected by the Raspberry Pi Health Monitor.
"""

import argparse
from db import DB_PATH

from visualization.data_loader import load_data, filter_network_data
from visualization.factory import create_dashboard

def main():
    """Main entry point for the visualization tool"""
    parser = argparse.ArgumentParser(description='View Raspberry Pi Health Metrics')
    parser.add_argument('--hours', type=int, default=24, help='Hours of data to display')
    parser.add_argument('--db', type=str, default=DB_PATH, help='SQLite database path')
    parser.add_argument('--output', type=str, help='Output HTML file (optional)')
    parser.add_argument('--view', choices=['detailed', 'summary', 'simple', 'all'], default='simple', 
                        help='View type: detailed (separate plots), summary (all on one), simple (basic dashboard), or all')
    parser.add_argument('--interface', type=str, help='Specific network interface to monitor (optional)')
    
    args = parser.parse_args()
    
    # Load data
    timestamps, metrics, network_data = load_data(hours=args.hours, db_path=args.db)
    
    if len(timestamps) == 0:
        print(f"No data found for the last {args.hours} hours")
        return
    
    # Filter network data if interface is specified
    if args.interface:
        network_data = filter_network_data(network_data, args.interface)
        if not network_data and args.interface:
            print(f"Interface {args.interface} not found. Available interfaces: {', '.join(network_data.keys()) if network_data else 'none'}")
    
    # Create figures based on view type
    if args.view in ['detailed', 'all']:
        detailed = create_dashboard('detailed', timestamps, metrics, network_data)
        if args.output:
            output_file = args.output if args.view == 'detailed' else f"detailed_{args.output}"
            detailed.write_html(output_file)
            print(f"Detailed dashboard saved to {output_file}")
        else:
            detailed.show()
    
    if args.view in ['summary', 'all']:
        summary = create_dashboard('summary', timestamps, metrics, network_data)
        if args.output:
            output_file = args.output if args.view == 'summary' else f"summary_{args.output}"
            summary.write_html(output_file)
            print(f"Summary plot saved to {output_file}")
        else:
            summary.show()
            
    if args.view in ['simple', 'all']:
        simple = create_dashboard('simple', timestamps, metrics, network_data)
        if args.output:
            output_file = args.output if args.view == 'simple' else f"simple_{args.output}"
            simple.write_html(output_file)
            print(f"Simple dashboard saved to {output_file}")
        else:
            simple.show()

if __name__ == "__main__":
    main() 