#!/usr/bin/env python3
"""
Pangolin Restart Service

A service that listens for HTTP commands to restart Pangolin containers
with randomized port assignments.
"""

import json
import logging
import os
import random
import subprocess
import sys
import yaml
from flask import Flask, request, jsonify
from threading import Lock

# Global configuration
CONFIG = {}
logger = None

# Default configuration
DEFAULT_CONFIG = {
    "service": {
        "listen_host": "0.0.0.0",
        "listen_port": 8080,
        "log_level": "INFO",
        "log_to_file": True,
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
        "use_sudo": True,
        "timeout": 120
    }
}

app = Flask(__name__)
restart_lock = Lock()


def load_config(config_file="service_config.json"):
    """Load configuration from config file"""
    global CONFIG, logger
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                CONFIG = json.load(f)
            print(f"Loaded configuration from {config_file}")
        except Exception as e:
            print(f"Failed to load config file {config_file}: {e}")
            print("Using default configuration")
            CONFIG = DEFAULT_CONFIG.copy()
    else:
        # Create default config file
        CONFIG = DEFAULT_CONFIG.copy()
        try:
            with open(config_file, 'w') as f:
                json.dump(CONFIG, f, indent=2)
            print(f"Created default configuration file: {config_file}")
        except Exception as e:
            print(f"Failed to create config file {config_file}: {e}")
    
    # Setup logging after config is loaded
    setup_logging()


def setup_logging():
    """Setup logging based on configuration"""
    global logger
    
    log_level = getattr(logging, CONFIG["service"]["log_level"].upper(), logging.INFO)
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if CONFIG["service"]["log_to_file"]:
        handlers.append(logging.FileHandler(CONFIG["service"]["log_file"]))
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    logger = logging.getLogger(__name__)


def run_command(command, cwd=None):
    """Execute a shell command and return the result"""
    try:
        logger.info(f"Executing: {command}")
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=CONFIG["docker"]["timeout"]
        )
        
        if result.returncode == 0:
            logger.info(f"Command succeeded: {command}")
            if result.stdout.strip():
                logger.debug(f"Output: {result.stdout.strip()}")
        else:
            logger.error(f"Command failed: {command}")
            logger.error(f"Error: {result.stderr.strip()}")
            
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return False, "", "Command timed out"
    except Exception as e:
        logger.error(f"Failed to execute command: {command}, Error: {e}")
        return False, "", str(e)


def stop_containers():
    """Stop the Pangolin docker containers"""
    logger.info("Stopping Pangolin containers...")
    sudo_prefix = "sudo " if CONFIG["docker"]["use_sudo"] else ""
    success, stdout, stderr = run_command(
        f"{sudo_prefix}docker compose down",
        cwd=CONFIG["pangolin"]["directory"]
    )
    return success


def start_containers():
    """Start the Pangolin docker containers"""
    logger.info("Starting Pangolin containers...")
    sudo_prefix = "sudo " if CONFIG["docker"]["use_sudo"] else ""
    success, stdout, stderr = run_command(
        f"{sudo_prefix}docker compose up -d",
        cwd=CONFIG["pangolin"]["directory"]
    )
    return success


def generate_random_port():
    """Generate a random port within the configured range"""
    port = random.randint(CONFIG["port_range"]["min"], CONFIG["port_range"]["max"])
    logger.info(f"Generated random port: {port}")
    return port


def update_docker_compose_port(new_port):
    """Update the gerbil port in docker-compose.yml"""
    compose_file_path = os.path.join(
        CONFIG["pangolin"]["directory"],
        CONFIG["pangolin"]["docker_compose_file"]
    )
    
    try:
        with open(compose_file_path, 'r') as f:
            compose_data = yaml.safe_load(f)
        
        # Update the ports in the gerbil service
        if 'services' in compose_data and 'gerbil' in compose_data['services']:
            gerbil_service = compose_data['services']['gerbil']
            if 'ports' in gerbil_service:
                # Update the UDP port mapping (first port entry)
                for i, port_mapping in enumerate(gerbil_service['ports']):
                    if isinstance(port_mapping, str):
                        if '/udp' in port_mapping:
                            gerbil_service['ports'][i] = f"{new_port}:{new_port}/udp"
                            logger.info(f"Updated UDP port mapping to: {new_port}:{new_port}/udp")
                        elif port_mapping.startswith('443:443') and '/udp' not in port_mapping:
                            gerbil_service['ports'][i] = f"{new_port}:{new_port}"
                            logger.info(f"Updated TCP port mapping to: {new_port}:{new_port}")
        
        # Write the updated compose file
        with open(compose_file_path, 'w') as f:
            yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Successfully updated docker-compose.yml with port {new_port}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update docker-compose.yml: {e}")
        return False


def update_config_port(new_port):
    """Update the gerbil start_port in config.yml"""
    config_file_path = os.path.join(
        CONFIG["pangolin"]["directory"],
        CONFIG["pangolin"]["config_file"]
    )
    
    try:
        with open(config_file_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Update the gerbil start_port
        if 'gerbil' in config_data:
            config_data['gerbil']['start_port'] = new_port
            logger.info(f"Updated gerbil start_port to: {new_port}")
        else:
            logger.error("gerbil section not found in config.yml")
            return False
        
        # Write the updated config file
        with open(config_file_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Successfully updated config.yml with port {new_port}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update config.yml: {e}")
        return False


def restart_pangolin():
    """Complete restart process with port randomization"""
    try:
        # Generate new random port
        new_port = generate_random_port()
        
        # Stop containers
        if not stop_containers():
            return False, "Failed to stop containers"
        
        # Update docker-compose.yml
        if not update_docker_compose_port(new_port):
            return False, "Failed to update docker-compose.yml"
        
        # Update config.yml
        if not update_config_port(new_port):
            return False, "Failed to update config.yml"
        
        # Start containers
        if not start_containers():
            return False, "Failed to start containers"
        
        logger.info(f"Successfully restarted Pangolin with new port: {new_port}")
        return True, f"Pangolin restarted successfully with port {new_port}"
        
    except Exception as e:
        logger.error(f"Restart process failed: {e}")
        return False, f"Restart failed: {str(e)}"


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "pangolin-restart-service",
        "config": {
            "port_range": CONFIG["port_range"],
            "pangolin_directory": CONFIG["pangolin"]["directory"],
            "listen_port": CONFIG["service"]["listen_port"]
        }
    })


@app.route('/restart', methods=['POST'])
def handle_restart():
    """Handle restart command"""
    with restart_lock:
        try:
            # Check if request contains the restart command
            data = request.get_json() if request.is_json else {}
            command = data.get('command', '') if data else request.form.get('command', '')
            
            if command != 'restart_pangolin':
                return jsonify({
                    "error": "Invalid command. Expected 'restart_pangolin'"
                }), 400
            
            logger.info("Received restart_pangolin command")
            
            # Execute restart process
            success, message = restart_pangolin()
            
            if success:
                return jsonify({
                    "status": "success",
                    "message": message
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": message
                }), 500
                
        except Exception as e:
            logger.error(f"Error handling restart request: {e}")
            return jsonify({
                "status": "error",
                "message": f"Internal server error: {str(e)}"
            }), 500


@app.route('/config', methods=['GET'])
def get_config():
    """Get current service configuration"""
    return jsonify(CONFIG)


@app.route('/config', methods=['POST'])
def update_config():
    """Update service configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Deep merge the configuration
        def deep_merge(target, source):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
        
        # Update configuration
        deep_merge(CONFIG, data)
        
        # Save to file
        with open("service_config.json", 'w') as f:
            json.dump(CONFIG, f, indent=2)
        
        # Re-setup logging if service config changed
        if 'service' in data:
            setup_logging()
        
        logger.info("Configuration updated")
        return jsonify({
            "status": "success",
            "message": "Configuration updated",
            "config": CONFIG
        })
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to update configuration: {str(e)}"
        }), 500


if __name__ == '__main__':
    # Load configuration
    config_file = sys.argv[1] if len(sys.argv) > 1 else "service_config.json"
    load_config(config_file)
    
    # Validate pangolin directory exists
    if not os.path.exists(CONFIG["pangolin"]["directory"]):
        logger.error(f"Pangolin directory not found: {CONFIG['pangolin']['directory']}")
        sys.exit(1)
    
    logger.info(f"Starting Pangolin Restart Service...")
    logger.info(f"Listening on {CONFIG['service']['listen_host']}:{CONFIG['service']['listen_port']}")
    logger.info(f"Port range: {CONFIG['port_range']['min']}-{CONFIG['port_range']['max']}")
    logger.info(f"Pangolin directory: {CONFIG['pangolin']['directory']}")
    logger.info(f"Docker sudo: {CONFIG['docker']['use_sudo']}")
    
    app.run(
        host=CONFIG["service"]["listen_host"],
        port=CONFIG["service"]["listen_port"],
        debug=False
    )
