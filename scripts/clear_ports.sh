#!/bin/bash

# Script to clear all ports used by qoneqt docker-compose services
# This will stop any processes using these ports

echo "🔍 Checking and clearing ports used by qoneqt services..."
echo ""

# Define all ports used by docker-compose services
PORTS=(
    5432    # PostgreSQL
    6379    # Redis
    5672    # RabbitMQ AMQP
    15672   # RabbitMQ Management
    8080    # API
    3000    # Web Frontend
    8081    # Adminer
    9090    # Prometheus
    9093    # Alertmanager
    3001    # Grafana
)

# Function to kill process using a port
kill_port() {
    local port=$1
    
    # Check with sudo for docker-proxy processes
    local pids=$(sudo lsof -ti:$port 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo "⚠️  Port $port is in use by PID(s): $pids"
        # Show what's using the port
        sudo lsof -i:$port 2>/dev/null || true
        echo "   Killing process(es)..."
        sudo kill -9 $pids 2>/dev/null || true
        sleep 0.5
        echo "✅ Port $port cleared"
    else
        echo "✓  Port $port is already free"
    fi
}

# Check if lsof is installed
if ! command -v lsof &> /dev/null; then
    echo "❌ Error: 'lsof' command not found. Installing..."
    sudo apt-get update && sudo apt-get install -y lsof
fi

# Stop all docker containers first (including orphaned ones)
echo ""
echo "🐳 Stopping all qoneqt containers and removing orphans..."
docker compose down --remove-orphans 2>/dev/null || true

# Also stop any containers that might be in a created/exited state
echo "🧹 Removing any stopped containers..."
docker ps -a --filter "name=qoneqt" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true
echo ""

# Clear each port
for port in "${PORTS[@]}"; do
    kill_port $port
done

echo ""
echo "✨ All ports cleared! You can now run: docker compose up -d"
echo ""
