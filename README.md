# Raspberry Pi Health Monitor

A Python script that periodically monitors and logs Raspberry Pi health metrics to a SQLite database.

## Metrics Collected

- CPU usage percentage
- Memory usage percentage
- Disk usage percentage
- CPU temperature
- CPU frequency
- System uptime

## Installation

1. Clone this repository to your Raspberry Pi:
   ```
   git clone https://github.com/yourusername/pi-health.git
   cd pi-health
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running Directly

You can run the monitoring script directly:

```bash
python monitor.py
```

The script will continue running until interrupted (Ctrl+C).

### Command Line Options

- `--interval SECONDS`: Set the monitoring interval (default: 60 seconds)
- `--db PATH`: Set the database file path (default: pi_health.db)
- `--log-level LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

Example:
```bash
python monitor.py --interval 300 --db ~/health_data.db --log-level DEBUG
```

## Running as a System Service (Recommended)

The best way to run this monitor is as a systemd service, which allows it to:
- Start automatically on boot
- Restart if it crashes
- Run in the background

### Setting up the Systemd Service

1. Copy the service file to the systemd directory:
   ```bash
   sudo cp pi-health.service /etc/systemd/system/
   ```

2. Edit the service file to use the correct paths for your setup:
   ```bash
   sudo nano /etc/systemd/system/pi-health.service
   ```
   
   Update the following lines:
   - `ExecStart`: Path to Python and the monitor script
   - `WorkingDirectory`: Directory where the script is located
   - `User`: User to run the service as (typically 'pi')

3. Enable and start the service:
   ```bash
   sudo systemctl enable pi-health.service
   sudo systemctl start pi-health.service
   ```

4. Check the status:
   ```bash
   sudo systemctl status pi-health.service
   ```

5. View logs:
   ```bash
   sudo journalctl -u pi-health.service
   ```

## Querying the Data

You can query the collected data using SQLite:

```bash
sqlite3 pi_health.db "SELECT * FROM health_metrics ORDER BY timestamp DESC LIMIT 10;"
```

Example queries:

```sql
-- Get average CPU usage by hour for the past day
SELECT 
  strftime('%Y-%m-%d %H', timestamp) as hour, 
  AVG(cpu_percent) as avg_cpu 
FROM health_metrics 
WHERE timestamp > datetime('now', '-1 day') 
GROUP BY hour 
ORDER BY hour;

-- Find temperature spikes
SELECT timestamp, temperature 
FROM health_metrics 
WHERE temperature > 70 
ORDER BY temperature DESC;
```
