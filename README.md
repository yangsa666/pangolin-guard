# Pangolin Restart Service

A Python service that listens for HTTP commands to restart Pangolin containers with randomized port assignments.

## Features

- HTTP API to trigger container restarts
- Automatic port randomization within configurable ranges
- Updates both `docker-compose.yml` and `config.yml` files
- Thread-safe operations with locking
- Comprehensive logging
- Health check endpoint
- Configuration management via API

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure the service has sudo access for Docker commands (add to sudoers if needed):
   ```bash
   # Add to /etc/sudoers.d/pangolin-restart
   your_user ALL=(ALL) NOPASSWD: /usr/bin/docker
   ```

3. Update the configuration if needed (see Configuration section)

## Usage

### Start the Service

```bash
python3 pangolin_restart_service.py
```

The service will start on port 8080 by default.

### Trigger a Restart

Send a POST request to the `/restart` endpoint:

```bash
# Using curl with JSON
curl -X POST http://localhost:8080/restart \
  -H "Content-Type: application/json" \
  -d '{"command": "restart_pangolin"}'

# Using curl with form data
curl -X POST http://localhost:8080/restart \
  -d "command=restart_pangolin"
```

### Health Check

```bash
curl http://localhost:8080/health
```

### Get Configuration

```bash
curl http://localhost:8080/config
```

### Update Configuration via API

```bash
# Update port range
curl -X POST http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{
    "port_range": {
      "min": 40000,
      "max": 50000
    }
  }'

# Update service settings
curl -X POST http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{
    "service": {
      "listen_port": 9090,
      "log_level": "DEBUG"
    }
  }'

# Disable sudo for Docker (useful for development)
curl -X POST http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{
    "docker": {
      "use_sudo": false
    }
  }'
```

## Configuration

The service uses a standalone configuration file `service_config.json`. If this file doesn't exist, it will be created with default values:

```json
{
  "service": {
    "listen_host": "0.0.0.0",
    "listen_port": 8080,
    "log_level": "INFO",
    "log_to_file": true,
    "log_file": "pangolin_restart_service.log"
  },
  "pangolin": {
    "directory": "./pangolin",
    "docker_compose_file": "docker-compose.yml",
    "config_file": "config/config.yml"
  },
  "port_range": {
    "min": 50000,
    "max": 60000
  },
  "docker": {
    "use_sudo": true,
    "timeout": 120
  }
}
```

### Configuration Sections

#### Service Configuration
- `listen_host`: Host to bind the HTTP server to
- `listen_port`: Port for the HTTP server
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `log_to_file`: Whether to log to a file
- `log_file`: Log file name

#### Pangolin Configuration
- `directory`: Path to the pangolin directory
- `docker_compose_file`: Name of the docker-compose file
- `config_file`: Path to the config.yml file relative to pangolin directory

#### Port Range Configuration
- `min`: Minimum port for random selection
- `max`: Maximum port for random selection

#### Docker Configuration
- `use_sudo`: Whether to use sudo for Docker commands
- `timeout`: Timeout for Docker commands in seconds

### Using Different Configuration Files

You can specify a custom configuration file when starting the service:

```bash
# Use default config (service_config.json)
python3 pangolin_restart_service.py

# Use custom config file
python3 pangolin_restart_service.py service_config_dev.json

# Use production config
python3 pangolin_restart_service.py /etc/pangolin/service_config_prod.json
```

## Systemd Service Installation

1. Copy the service file:
   ```bash
   sudo cp pangolin-restart.service /etc/systemd/system/
   ```

2. Update the paths in the service file:
   ```bash
   sudo nano /etc/systemd/system/pangolin-restart.service
   # Update WorkingDirectory and ExecStart paths
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable pangolin-restart.service
   sudo systemctl start pangolin-restart.service
   ```

4. Check service status:
   ```bash
   sudo systemctl status pangolin-restart.service
   ```

## API Endpoints

### POST /restart
Triggers a Pangolin restart with port randomization.

**Request Body:**
```json
{
  "command": "restart_pangolin"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Pangolin restarted successfully with port 52341"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "pangolin-restart-service",
  "config": {
    "port_range": {"min": 50000, "max": 60000},
    "pangolin_directory": "./pangolin"
  }
}
```

### GET /config
Returns current configuration.

### POST /config
Updates configuration (requires JSON body with config updates).

## Restart Process

When a restart is triggered, the service performs these steps:

1. **Generate Random Port**: Selects a random port within the configured range
2. **Stop Containers**: Runs `sudo docker compose down` in the pangolin directory
3. **Update docker-compose.yml**: Updates the gerbil service port mappings
4. **Update config.yml**: Updates the `gerbil.start_port` configuration
5. **Start Containers**: Runs `sudo docker compose up -d` to restart services

## Logging

The service logs to both:
- `pangolin_restart_service.log` file
- Console output

Log levels include INFO, WARNING, and ERROR messages for debugging.

## Security Considerations

- The service runs with sudo privileges for Docker commands
- Consider firewall rules to restrict access to the service port
- Use authentication/authorization if deploying in production
- Monitor the service logs for unauthorized access attempts

## Troubleshooting

1. **Permission Issues**: Ensure the user can run sudo docker commands
2. **Port Conflicts**: Check that generated ports are not in use
3. **File Permissions**: Ensure the service can read/write the configuration files
4. **Docker Issues**: Verify Docker and docker-compose are installed and working

## Examples

### Automated Restart Script
```bash
#!/bin/bash
response=$(curl -s -X POST http://localhost:8080/restart \
  -H "Content-Type: application/json" \
  -d '{"command": "restart_pangolin"}')

if echo "$response" | grep -q '"status":"success"'; then
  echo "Restart successful"
  exit 0
else
  echo "Restart failed: $response"
  exit 1
fi
```

### Monitoring Script
```bash
#!/bin/bash
# Check if service is healthy
curl -f http://localhost:8080/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "Service is healthy"
else
  echo "Service is down"
  # Restart service logic here
fi
```
