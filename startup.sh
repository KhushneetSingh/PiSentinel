#!/usr/bin/env bash
# ===========================================================================
# PiSentinel Startup Script
# ===========================================================================
# Usage:  sudo bash startup.sh
# This script checks dependencies, prepares the environment, and starts
# the PiSentinel dashboard server.
# ===========================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/Backend"
VENV_DIR="${SCRIPT_DIR}/venv"
INTERFACE="${PISENTINEL_INTERFACE:-wlan1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ---------------------------------------------------------------------------
# 1. Check root privileges
# ---------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (sudo)."
    exit 1
fi

log_info "Starting PiSentinel..."
log_info "Project directory: ${SCRIPT_DIR}"

# ---------------------------------------------------------------------------
# 2. Create required directories
# ---------------------------------------------------------------------------
mkdir -p "${SCRIPT_DIR}/captures"
mkdir -p "${SCRIPT_DIR}/logs"
log_info "Directories verified: captures/, logs/"

# ---------------------------------------------------------------------------
# 3. Check system dependencies
# ---------------------------------------------------------------------------
MISSING_DEPS=()
for cmd in airmon-ng airodump-ng aireplay-ng python3; do
    if ! command -v "$cmd" &>/dev/null; then
        MISSING_DEPS+=("$cmd")
    fi
done

if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
    log_warn "Missing system dependencies: ${MISSING_DEPS[*]}"
    log_warn "Install with: sudo apt install -y aircrack-ng python3 python3-pip"
    log_warn "Continuing anyway — some features may not work."
fi

# ---------------------------------------------------------------------------
# 4. Activate virtual environment (if it exists)
# ---------------------------------------------------------------------------
if [[ -d "${VENV_DIR}" ]]; then
    log_info "Activating virtual environment..."
    source "${VENV_DIR}/bin/activate"
else
    log_warn "No virtual environment found at ${VENV_DIR}. Using system Python."
fi

# ---------------------------------------------------------------------------
# 5. Check WiFi interface
# ---------------------------------------------------------------------------
if ip link show "${INTERFACE}" &>/dev/null; then
    log_info "WiFi interface '${INTERFACE}' detected."
else
    log_warn "WiFi interface '${INTERFACE}' not found."
    log_warn "Available interfaces:"
    ip link show | grep -E '^\d+:' | awk '{print "  " $2}' | tr -d ':'
    log_warn "Set PISENTINEL_INTERFACE env var to override."
fi

# ---------------------------------------------------------------------------
# 6. Kill conflicting processes
# ---------------------------------------------------------------------------
log_info "Killing processes that may interfere with monitor mode..."
airmon-ng check kill 2>/dev/null || true

# ---------------------------------------------------------------------------
# 7. Launch PiSentinel
# ---------------------------------------------------------------------------
log_info "Launching PiSentinel server..."
cd "${BACKEND_DIR}"
exec python3 app.py
