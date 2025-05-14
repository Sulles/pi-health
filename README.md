# Raspberry Pi Health Monitor

A Python script that periodically monitors and logs Raspberry Pi health metrics to a SQLite database. It includes tools for viewing metrics as interactive dashboards and retrieving data remotely.

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

## Monitoring Usage

### Running Directly

You can run the monitoring script directly:

```bash
python monitor.py
```

The script will continue running until interrupted (Ctrl+C).

### Command Line Options for monitor.py

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

## Visualizing Data

The project includes a visualization tool that creates interactive dashboards from the collected data.

### Running the Visualization Tool

```bash
python view.py
```

### Command Line Options for view.py

- `--hours HOURS`: Number of hours of data to display (default: 24)
- `--db PATH`: Set the database file path (default: pi-health.db)
- `--output FILE`: Save the dashboard to an HTML file instead of displaying it
- `--view TYPE`: Choose the visualization type (options: dashboard, summary, simple, all)

Examples:
```bash
# View last 48 hours of data
python view.py --hours 48

# Save the simple dashboard to an HTML file
python view.py --output dashboard.html --view simple

# View all dashboard types
python view.py --view all
```

### Visualization Types

- **Simple**: A basic 2x2 dashboard with:
  - CPU & Memory usage
  - Disk usage & Temperature
  - Summary bar chart
  - Table of latest statistics

- **Dashboard**: Detailed multi-panel view with separate graphs for each metric

- **Summary**: Single graph showing all metrics together

## Retrieving Data from Remote Pi

If you're running the monitor on a remote Raspberry Pi, you can use the pull script to retrieve the database file:

```bash
python pull.py
```

### Command Line Options for pull.py

- `--host HOST`: Hostname or IP address of the Raspberry Pi (default: rpi4)
- `--user USER`: Username for SSH connection (default: admin)
- `--remote-path PATH`: Path to the database on the Raspberry Pi (default: pi-health.db)
- `--local-path PATH`: Path to save the database locally (default: ~/GitHub/pi-health/pi-health.db)
- `--port PORT`: SSH port (default: 22)
- `--identity FILE`: Path to SSH identity file (optional)

Example:
```bash
python pull.py --host 192.168.1.100 --user pi --remote-path /home/pi/pi-health/pi-health.db
```

## Querying the Data

You can query the collected data using SQLite:

```bash
sqlite3 pi-health.db "SELECT * FROM health_metrics ORDER BY timestamp DESC LIMIT 10;"
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

## Database Structure

The project uses SQLite to store metrics in a table called `health_metrics` with the following structure:

- `id`: Integer primary key
- `timestamp`: Text (ISO format date/time)
- `cpu_percent`: Real number (0-100)
- `memory_percent`: Real number (0-100)
- `disk_percent`: Real number (0-100)
- `temperature`: Real number (CPU temperature in Celsius)
- `cpu_frequency`: Real number (CPU frequency in MHz)
- `uptime`: Real number (System uptime in seconds)

## Project Structure

- `monitor.py`: Main monitoring script
- `view.py`: Visualization dashboard tool
- `db.py`: Database handling module
- `pull.py`: Remote database retrieval script
- `pi-health.service`: Systemd service configuration file
- `pi-health.db`: SQLite database file (created during runtime)
