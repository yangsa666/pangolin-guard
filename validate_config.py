#!/usr/bin/env python3
"""
Configuration validation script for Pangolin Restart Service
"""

import json
import sys
import os

def validate_config(config_file):
    """Validate the configuration file"""
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration file: {e}")
        return False
    except (IOError, OSError) as e:
        print(f"❌ Error reading configuration file: {e}")
        return False
    
    errors = []
    warnings = []
    
    # Check required sections
    required_sections = ['service', 'pangolin', 'port_range', 'docker']
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    # Validate service section
    if 'service' in config:
        service = config['service']
        if 'listen_port' in service:
            port = service['listen_port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                errors.append(f"Invalid listen_port: {port} (must be 1-65535)")
        
        if 'log_level' in service:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
            if service['log_level'] not in valid_levels:
                errors.append(f"Invalid log_level: {service['log_level']} (must be one of {valid_levels})")
    
    # Validate pangolin section
    if 'pangolin' in config:
        pangolin = config['pangolin']
        if 'directory' in pangolin:
            if not os.path.exists(pangolin['directory']):
                warnings.append(f"Pangolin directory does not exist: {pangolin['directory']}")
            elif 'docker_compose_file' in pangolin:
                compose_path = os.path.join(pangolin['directory'], pangolin['docker_compose_file'])
                if not os.path.exists(compose_path):
                    warnings.append(f"Docker compose file not found: {compose_path}")
            elif 'config_file' in pangolin:
                config_path = os.path.join(pangolin['directory'], pangolin['config_file'])
                if not os.path.exists(config_path):
                    warnings.append(f"Pangolin config file not found: {config_path}")
    
    # Validate port range
    if 'port_range' in config:
        port_range = config['port_range']
        if 'min' in port_range and 'max' in port_range:
            min_port = port_range['min']
            max_port = port_range['max']
            
            if not isinstance(min_port, int) or not isinstance(max_port, int):
                errors.append("Port range min and max must be integers")
            elif min_port >= max_port:
                errors.append(f"Port range min ({min_port}) must be less than max ({max_port})")
            elif min_port < 1024:
                warnings.append(f"Port range min ({min_port}) is below 1024 (privileged ports)")
            elif max_port > 65535:
                errors.append(f"Port range max ({max_port}) exceeds maximum port number (65535)")
    
    # Validate docker section
    if 'docker' in config:
        docker = config['docker']
        if 'timeout' in docker:
            if not isinstance(docker['timeout'], int) or docker['timeout'] <= 0:
                errors.append(f"Docker timeout must be a positive integer, got: {docker['timeout']}")
    
    # Print results
    if errors:
        print("❌ Configuration validation failed:")
        for error in errors:
            print(f"   • {error}")
    
    if warnings:
        print("⚠️  Configuration warnings:")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not errors and not warnings:
        print("✅ Configuration is valid")
    elif not errors:
        print("✅ Configuration is valid (with warnings)")
    
    return len(errors) == 0

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate_config.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    print(f"🔍 Validating configuration file: {config_file}")
    
    if validate_config(config_file):
        print("🎉 Configuration validation passed!")
        sys.exit(0)
    else:
        print("💥 Configuration validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
