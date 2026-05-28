"""
PiSentinel Configuration
========================
Centralized configuration for the PiSentinel application.
All values can be overridden via environment variables.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Base directory of the project (one level up from Backend/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory where packet captures (.pcap / .cap) are stored
CAPTURE_DIR = os.environ.get(
    "PISENTINEL_CAPTURE_DIR",
    os.path.join(BASE_DIR, "captures"),
)

# Directory for application logs
LOG_DIR = os.environ.get(
    "PISENTINEL_LOG_DIR",
    os.path.join(BASE_DIR, "logs"),
)

# ---------------------------------------------------------------------------
# Network Interface
# ---------------------------------------------------------------------------
# The wireless interface to use for monitoring / injection.
# Typical values: "wlan1", "wlan0", "wlan1mon"
MONITOR_INTERFACE = os.environ.get("PISENTINEL_INTERFACE", "wlan1")

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
HOST = os.environ.get("PISENTINEL_HOST", "0.0.0.0")
PORT = int(os.environ.get("PISENTINEL_PORT", "5000"))
DEBUG = os.environ.get("PISENTINEL_DEBUG", "false").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.environ.get("PISENTINEL_LOG_LEVEL", "INFO").upper()

# Maximum log file size in bytes before rotation (default 5 MB)
LOG_MAX_BYTES = int(os.environ.get("PISENTINEL_LOG_MAX_BYTES", str(5 * 1024 * 1024)))

# Number of rotated log backups to keep
LOG_BACKUP_COUNT = int(os.environ.get("PISENTINEL_LOG_BACKUP_COUNT", "3"))

# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------
# How often (seconds) the log-streaming thread pushes updates to the frontend
LOG_STREAM_INTERVAL = float(os.environ.get("PISENTINEL_LOG_STREAM_INTERVAL", "2"))
