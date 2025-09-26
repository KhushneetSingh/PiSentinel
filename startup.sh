#!/bin/bash

# PiSentinel Startup Script
# Place this in /home/pen-test/Desktop/PiSentinel/startup.sh

# Log file
LOG_FILE="/home/pen-test/Desktop/PiSentinel/startup.log"

# Function to log messages
log() {
    echo "$(date): $1" >> "$LOG_FILE"
    echo "$1"
}

# Create log file
touch "$LOG_FILE"
log "Starting PiSentinel..."

# Create required directories
mkdir -p /home/pen-test/Desktop/PiSentinel/captures
log "Created capture directory"

# Install required packages if not already installed
if ! command -v airmon-ng &> /dev/null; then
    log "Installing aircrack-ng suite..."
    sudo apt-get update
    sudo apt-get install -y aircrack-ng
fi

if ! python3 -c "import netifaces" &> /dev/null; then
    log "Installing Python dependencies..."
    sudo pip3 install flask flask-socketio netifaces
fi

# Set proper permissions
sudo chmod -R 755 /home/pen-test/Desktop/PiSentinel
sudo chown -R pen-test:pen-test /home/pen-test/Desktop/PiSentinel

# Start the PiSentinel server
log "Starting PiSentinel server..."
cd /home/pen-test/Desktop/PiSentinel/backend
sudo python3 app.py >> "$LOG_FILE" 2>&1 &

# Wait for server to start
sleep 5

# Display IP information for connecting
log "PiSentinel server started!"
log "Connect to one of these addresses from your browser:"
ip addr | grep "inet " | grep -v "127.0.0.1" | awk '{print "http://"$2}' | cut -d"/" -f1 | sed 's/$/:5000/' >> "$LOG_FILE"
ip addr | grep "inet " | grep -v "127.0.0.1" | awk '{print "http://"$2}' | cut -d"/" -f1 | sed 's/$/:5000/'

log "Startup complete!"