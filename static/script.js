document.addEventListener("DOMContentLoaded", () => {
    // Connect to the same server that served this page
    const socket = io();
    
    // Elements
    const statusElement = document.getElementById("status");
    const logBoxElement = document.getElementById("log-box");
    const filesBoxElement = document.getElementById("files-box");
    const interfaceSelect = document.getElementById("interface-select");
    const serverIpElement = document.getElementById("server-ip");
    const connectionStatus = document.getElementById("connection-status");
    
    // Connection management
    socket.on("connect", () => {
        connectionStatus.textContent = "Connected";
        connectionStatus.className = "connected";
        fetchSystemInfo();
    });
    
    socket.on("disconnect", () => {
        connectionStatus.textContent = "Disconnected";
        connectionStatus.className = "disconnected";
    });
    
    // Status updates
    socket.on("status_update", (data) => {
        statusElement.innerText = data.status;
        fetchSystemInfo(); // Refresh info after status changes
    });
    
    // Log updates
    socket.on("log_update", (data) => {
        if (Array.isArray(data.logs)) {
            filesBoxElement.innerHTML = data.logs.length > 0 
                ? data.logs.map(file => `<div class="file-item">${file}</div>`).join("")
                : "No capture files yet...";
        } else {
            // Format and display the log content
            logBoxElement.innerText = data.logs || "No log data available";
        }
    });
    
    // Interface updates
    socket.on("interface_update", (data) => {
        // Update interface dropdown
        interfaceSelect.innerHTML = "";
        if (data.interfaces && data.interfaces.length > 0) {
            data.interfaces.forEach(iface => {
                const option = document.createElement("option");
                option.value = iface;
                option.textContent = iface;
                interfaceSelect.appendChild(option);
            });
        } else {
            const option = document.createElement("option");
            option.value = "";
            option.textContent = "No interfaces found";
            interfaceSelect.appendChild(option);
        }
        
        // Update server IP display
        if (data.server_ip) {
            serverIpElement.textContent = data.server_ip;
        }
    });
    
    // Fetch system info
    function fetchSystemInfo() {
        fetch('/system_info')
            .then(response => response.json())
            .then(data => {
                // Update interface dropdown
                interfaceSelect.innerHTML = "";
                if (data.interfaces && data.interfaces.length > 0) {
                    data.interfaces.forEach(iface => {
                        const option = document.createElement("option");
                        option.value = iface;
                        option.textContent = iface;
                        interfaceSelect.appendChild(option);
                    });
                } else {
                    const option = document.createElement("option");
                    option.value = "";
                    option.textContent = "No interfaces found";
                    interfaceSelect.appendChild(option);
                }
                
                // Update server IP display
                serverIpElement.textContent = data.server_ip;
                
                // Update monitoring status
                if (data.monitoring_active) {
                    statusElement.textContent = "Monitoring Active";
                }
            })
            .catch(error => {
                console.error("Error fetching system info:", error);
            });
    }
    
    // Button events
    document.getElementById("start-monitoring-btn").addEventListener("click", () => {
        const interface = interfaceSelect.value;
        if (!interface) {
            alert("Please select a wireless interface");
            return;
        }
        
        statusElement.textContent = "Starting monitoring...";
        socket.emit("start_monitoring", { interface: interface });
    });
    
    document.getElementById("stop-monitoring-btn").addEventListener("click", () => {
        statusElement.textContent = "Stopping monitoring...";
        socket.emit("stop_monitoring");
    });
    
    document.getElementById("refresh-info-btn").addEventListener("click", () => {
        fetchSystemInfo();
        socket.emit("fetch_logs");
    });
    
    document.getElementById("send-deauth-btn").addEventListener("click", () => {
        const targetAp = prompt("Enter target AP MAC address:");
        if (!targetAp) return;
        
        const targetClient = prompt("Enter target client MAC address (or leave blank for broadcast):");
        socket.emit("send_deauth", { 
            target_ap: targetAp,
            target_client: targetClient || "FF:FF:FF:FF:FF:FF" 
        });
    });
    
    document.getElementById("clear-logs-btn").addEventListener("click", () => {
        logBoxElement.innerText = "Logs cleared...";
    });
    
    // Initial data fetch
    socket.emit("fetch_logs");
});