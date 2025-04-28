from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import subprocess
import os
import threading
import time
import netifaces as ni
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/home/pen-test/Desktop/PiSentinel/pisentinel.log'
)
logger = logging.getLogger('PiSentinel')

app = Flask(__name__, 
            static_folder='../static',
            template_folder='../templates')
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
CAPTURE_DIR = "/home/pen-test/Desktop/PiSentinel/captures"
DEFAULT_MONITOR_INTERFACE = "wlan1"
MANAGEMENT_INTERFACE = "wlan0"  # Interface to keep network connectivity
airodump_process = None
monitoring_active = False

# Helper functions
def kill_blocking_processes():
    """Kill processes that might interfere with monitor mode."""
    try:
        logger.info("Killing blocking processes")
        subprocess.run([
            "sudo", "airmon-ng", "check", "kill"
        ], check=True)
        return True
    except Exception as e:
        logger.error(f"Failed to kill blocking processes: {str(e)}")
        return False

def get_available_interfaces():
    """Get list of wireless interfaces."""
    try:
        result = subprocess.run(
            ["iwconfig"], 
            capture_output=True, 
            text=True,
            check=True
        )
        interfaces = []
        for line in result.stdout.split("\n"):
            if "IEEE 802.11" in line:
                interfaces.append(line.split()[0])
        return interfaces
    except Exception as e:
        logger.error(f"Error getting interfaces: {str(e)}")
        return []

def get_server_ip():
    """Get IP address for the management interface."""
    try:
        for interface in ni.interfaces():
            if interface == MANAGEMENT_INTERFACE:
                addresses = ni.ifaddresses(interface)
                if ni.AF_INET in addresses:
                    return addresses[ni.AF_INET][0]['addr']
        # Fallback: return all addresses
        all_ips = []
        for interface in ni.interfaces():
            addresses = ni.ifaddresses(interface)
            if ni.AF_INET in addresses:
                all_ips.append(f"{interface}: {addresses[ni.AF_INET][0]['addr']}")
        return ", ".join(all_ips)
    except Exception as e:
        logger.error(f"Error getting IP: {str(e)}")
        return "Unknown"

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/system_info')
def system_info():
    interfaces = get_available_interfaces()
    return jsonify({
        'interfaces': interfaces,
        'server_ip': get_server_ip(),
        'monitoring_active': monitoring_active
    })

# Background tasks
def stream_logs():
    """Continuously stream logs to the frontend."""
    log_file = os.path.join(CAPTURE_DIR, "airodump.log")
    while True:
        try:
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    logs = f.read()
                    socketio.emit("log_update", {"logs": logs})
        except Exception as e:
            logger.error(f"Error streaming logs: {str(e)}")
        socketio.sleep(2)

# Socket.IO events
@socketio.on("start_monitoring")
def start_monitoring(data):
    """Start monitoring mode and airodump-ng."""
    global airodump_process, monitoring_active
    try:
        # Get interface from request or use default
        interface = data.get("interface", DEFAULT_MONITOR_INTERFACE)
        
        # Make sure capture directory exists
        os.makedirs(CAPTURE_DIR, exist_ok=True)
        
        # Kill network manager and wpa_supplicant
        kill_blocking_processes()
        
        # Start monitor mode
        logger.info(f"Starting monitor mode on {interface}")
        monitor_result = subprocess.run(
            ["sudo", "airmon-ng", "start", interface], 
            capture_output=True,
            text=True
        )
        
        # Determine monitor interface name (might be interface + "mon")
        monitor_interface = interface
        if "monitor mode enabled on" in monitor_result.stdout:
            for line in monitor_result.stdout.split("\n"):
                if "monitor mode enabled on" in line:
                    parts = line.split()
                    for part in parts:
                        if "mon" in part:
                            monitor_interface = part
                            break
        
        # Start airodump-ng for capturing
        log_file = os.path.join(CAPTURE_DIR, "airodump.log")
        airodump_process = subprocess.Popen(
            [
                "sudo", "airodump-ng", 
                "-w", os.path.join(CAPTURE_DIR, "capture"), 
                "--output-format", "pcap,csv", 
                monitor_interface
            ],
            stdout=open(log_file, "w"),
            stderr=subprocess.STDOUT,
        )
        
        monitoring_active = True
        emit("status_update", {"status": f"Monitoring started on {monitor_interface}"})
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        emit("status_update", {"status": f"Error: {str(e)}"})

@socketio.on("stop_monitoring")
def stop_monitoring():
    """Stop monitoring mode and airodump-ng."""
    global airodump_process, monitoring_active
    try:
        if airodump_process:
            airodump_process.terminate()
            airodump_process = None
        
        # Get available interfaces to determine monitor interface name
        interfaces = get_available_interfaces()
        for interface in interfaces:
            if "mon" in interface:
                subprocess.run(["sudo", "airmon-ng", "stop", interface], check=True)
        
        # Restart network services
        subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], check=False)
        subprocess.run(["sudo", "systemctl", "restart", "wpa_supplicant"], check=False)
        
        monitoring_active = False
        emit("status_update", {"status": "Monitoring stopped"})
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        emit("status_update", {"status": f"Error: {str(e)}"})

@socketio.on("send_deauth")
def send_deauth(data):
    """Send a deauth attack."""
    try:
        target_ap = data["target_ap"]
        target_client = data.get("target_client", "FF:FF:FF:FF:FF:FF")
        
        # Get monitor interface
        monitor_interface = None
        interfaces = get_available_interfaces()
        for interface in interfaces:
            if "mon" in interface:
                monitor_interface = interface
                break
        
        if not monitor_interface:
            emit("status_update", {"status": "Error: No monitor interface found"})
            return
            
        # Run deauth attack
        subprocess.run(
            [
                "sudo", "aireplay-ng", 
                "--deauth", "10", 
                "-a", target_ap, 
                "-c", target_client, 
                monitor_interface
            ],
            check=True,
        )
        
        emit("status_update", {"status": f"Deauth attack sent to {target_ap}"})
    except Exception as e:
        logger.error(f"Error sending deauth: {str(e)}")
        emit("status_update", {"status": f"Error: {str(e)}"})

@socketio.on("fetch_logs")
def fetch_logs():
    """Send captured logs to the frontend."""
    try:
        logs = []
        if os.path.exists(CAPTURE_DIR):
            for file in os.listdir(CAPTURE_DIR):
                if file.endswith(".cap") or file.endswith(".csv"):
                    logs.append(file)
        
        # Also show available interfaces
        interfaces = get_available_interfaces()
        server_ip = get_server_ip()
        
        emit("log_update", {"logs": logs})
        emit("interface_update", {"interfaces": interfaces, "server_ip": server_ip})
    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}")
        emit("log_update", {"logs": [f"Error: {str(e)}"]})

if __name__ == "__main__":
    print("Starting PiSentinel server...")
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    print(f"Capture directory: {CAPTURE_DIR}")
    threading.Thread(target=stream_logs, daemon=True).start()
    print("Log streaming thread started")
    
    server_ip = get_server_ip()
    print(f"Server running at http://{server_ip}:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)