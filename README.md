# Portable Pentesting Device

A comprehensive wireless penetration testing tool that provides a web-based dashboard for network reconnaissance, deauthentication attacks, and packet capture analysis.

## Features

- **Web Dashboard**: Clean, intuitive interface accessible via browser
- **Network Scanning**: Discover and analyze nearby wireless networks
- **Deauthentication Attacks**: Targeted deauth packet injection
- **Packet Capture**: Real-time packet sniffing and analysis
- **Portable Design**: Works on Raspberry Pi or any Linux system
- **Auto-startup**: Automatically launches on boot (Pi configuration)

## Hardware Requirements

### Option 1: Raspberry Pi Setup (Recommended for Portability)
- Raspberry Pi 4 (2GB+ RAM recommended)
- MicroSD card (16GB+)
- USB WiFi adapter with monitor mode support (e.g., Alfa AWUS036ACS)
- Power supply/power bank
- Optional: Small display for headless operation

### Option 2: Linux PC Setup
- Any Linux computer/laptop
- USB WiFi adapter with monitor mode support
- Built-in WiFi can be used but external adapter recommended

## Compatible WiFi Adapters

Ensure your WiFi adapter supports **monitor mode** and **packet injection**:
- Alfa AWUS036ACS (Recommended)
- Alfa AWUS036ACH
- Panda PAU09
- TP-Link AC600 T2U Plus
- Any adapter with Realtek RTL8812AU/RTL8811AU chipset

## Installation

### Prerequisites

Update your system:
```bash
sudo apt update && sudo apt upgrade -y
```

Install required packages:
```bash
sudo apt install -y python3 python3-pip git aircrack-ng hostapd dhcp-helper bridge-utils
```

Install Python dependencies:
```bash
pip3 install flask flask-socketio scapy psutil threading subprocess
```

### Clone Repository

```bash
git clone https://github.com/yourusername/portable-pentesting-device.git
cd portable-pentesting-device
```

### Setup Instructions

#### For Raspberry Pi

1. **Enable SSH and configure headless setup** (optional):
```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

2. **Set up auto-start service**:
```bash
sudo cp pentesting-device.service /etc/systemd/system/
sudo systemctl enable pentesting-device.service
sudo systemctl daemon-reload
```

3. **Configure network interfaces**:
```bash
sudo cp interfaces /etc/dhcpcd.conf.backup
# Edit /etc/dhcpcd.conf to configure static IP if needed
```

#### For Linux PC

1. **Install additional dependencies** if needed:
```bash
# For Ubuntu/Debian
sudo apt install -y wireless-tools wpasupplicant

# For Arch Linux
sudo pacman -S wireless_tools wpa_supplicant

# For CentOS/RHEL
sudo yum install -y wireless-tools wpa_supplicant
```

2. **Set up permissions**:
```bash
sudo usermod -a -G netdev $USER
# Logout and login again for changes to take effect
```

## Configuration

### 1. Configure WiFi Adapter

Identify your wireless adapter:
```bash
iwconfig
# or
ip link show
```

Edit `config.py` and update the interface name:
```python
WIFI_INTERFACE = "wlan1"  # Replace with your adapter name
```

### 2. Set Monitor Mode

The application will automatically set monitor mode, but you can manually test:
```bash
sudo airmon-ng start wlan1
# Your interface might become wlan1mon
```

### 3. Configure Dashboard Settings

Edit `config.py` for custom settings:
```python
# Dashboard settings
DASHBOARD_HOST = "0.0.0.0"  # Listen on all interfaces
DASHBOARD_PORT = 8080
DEBUG_MODE = False

# Security settings
REQUIRE_AUTH = True  # Set to False for open access
DEFAULT_PASSWORD = "pentesting123"  # Change this!
```

## Usage

### Starting the Application

#### Method 1: Direct Python Execution
```bash
cd portable-pentesting-device
sudo python3 app.py
```

#### Method 2: Using the Service (Raspberry Pi)
```bash
sudo systemctl start pentesting-device
sudo systemctl status pentesting-device  # Check status
```

### Accessing the Dashboard

1. **Find the device IP address**:
```bash
hostname -I
# or
ip addr show
```

2. **Open web browser** and navigate to:
```
http://[DEVICE_IP]:8080
```
Example: `http://192.168.1.100:8080`

3. **For Raspberry Pi headless setup**, you can also try:
```
http://raspberrypi.local:8080
```

### Using the Interface

1. **Network Scan**: Click "Scan Networks" to discover nearby WiFi networks
2. **Select Target**: Choose a network from the discovered list
3. **Deauth Attack**: Click "Start Deauth" to begin deauthentication
4. **Packet Capture**: Use "Start Capture" to begin packet sniffing
5. **View Results**: Monitor real-time results in the dashboard

## File Structure

```
portable-pentesting-device/
├── app.py                 # Main application
├── config.py             # Configuration settings
├── static/
│   ├── css/
│   │   └── style.css     # Dashboard styling
│   └── js/
│       └── main.js       # Frontend JavaScript
├── templates/
│   └── index.html        # Web interface template
├── utils/
│   ├── network_scanner.py # Network scanning utilities
│   ├── deauth_attack.py   # Deauthentication attack tools
│   └── packet_capture.py # Packet capture functionality
├── logs/                 # Application logs
├── captures/             # Captured packets storage
├── pentesting-device.service # Systemd service file
└── README.md            # This file
```

## Troubleshooting

### Common Issues

**"No wireless interface found"**
- Check if your WiFi adapter is connected and recognized: `lsusb`
- Verify driver installation: `dmesg | grep -i wifi`
- Try different USB port

**"Permission denied"**
- Run with sudo: `sudo python3 app.py`
- Check user permissions: `groups $USER`

**"Monitor mode not supported"**
- Verify your adapter supports monitor mode
- Install proper drivers for your chipset
- Try: `sudo airmon-ng check kill` before starting

**Dashboard not accessible**
- Check if service is running: `sudo systemctl status pentesting-device`
- Verify firewall settings: `sudo ufw status`
- Check IP address: `hostname -I`

**Raspberry Pi won't start automatically**
- Check service status: `sudo systemctl status pentesting-device`
- View logs: `sudo journalctl -u pentesting-device -f`
- Verify service file permissions

### Performance Optimization

**For Raspberry Pi:**
- Use Class 10 SD card or better
- Ensure adequate power supply (2.5A+)
- Consider active cooling for extended use

**For Linux PC:**
- Close unnecessary applications
- Use dedicated USB 3.0 port for WiFi adapter
- Monitor CPU and memory usage

## Security Considerations

⚠️ **IMPORTANT**: This tool is for educational and authorized testing purposes only.

- Only use on networks you own or have explicit permission to test
- Ensure compliance with local laws and regulations
- Change default passwords before deployment
- Use in controlled environments
- Monitor for unintended network disruption

## Development

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Custom Modules
Add custom pentesting modules in the `modules/` directory following the existing pattern.

## License

This project is intended for educational purposes. Users are responsible for compliance with applicable laws.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review system logs: `sudo journalctl -u pentesting-device`
3. Open an issue on GitHub with system details and error logs

## Changelog

### v1.0.0
- Initial release
- Basic network scanning
- Deauthentication attacks
- Web dashboard interface
- Raspberry Pi auto-startup support