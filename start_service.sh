#!/bin/bash
# Pangolin Restart Service Startup Script

echo "🚀 Starting Pangolin Restart Service..."

# Parse command line arguments
CONFIG_FILE="service_config.json"
if [ $# -gt 0 ]; then
    CONFIG_FILE="$1"
fi

echo "📋 Using configuration file: $CONFIG_FILE"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    exit 1
fi

# Check if requirements are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import flask, yaml, requests" 2>/dev/null; then
    echo "⚠️  Installing required dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Check if pangolin directory exists
if [ ! -d "pangolin" ]; then
    echo "❌ Pangolin directory not found. Please run this script from the correct directory."
    exit 1
fi

# Check Docker permissions
echo "🐳 Checking Docker permissions..."
if ! sudo docker --version &> /dev/null; then
    echo "❌ Docker is not available or sudo access denied"
    exit 1
fi

echo "✅ All checks passed"
echo "🌐 Starting service on http://localhost:8080"
echo "📋 Available endpoints:"
echo "   - GET  /health  - Health check"
echo "   - POST /restart - Restart pangolin (command: restart_pangolin)"
echo "   - GET  /config  - Get configuration"
echo "   - POST /config  - Update configuration"
echo ""
echo "💡 To test the service, run: python3 test_service.py"
echo "🛑 Press Ctrl+C to stop the service"
echo ""

# Start the service
python3 pangolin_restart_service.py "$CONFIG_FILE"
