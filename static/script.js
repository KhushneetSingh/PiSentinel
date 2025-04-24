document.addEventListener("DOMContentLoaded", () => {
    // Connect to the same server that served this page
    const socket = io();
    
    const statusElement = document.getElementById("status");
    const logBoxElement = document.getElementById("log-box");

    // Update system status dynamically
    socket.on("status_update", (data) => {
        statusElement.innerText = data.status;
        statusElement.style.color = data.status === "Connected" ? "#4CAF50" : "#f44336";
    });

    // Update logs dynamically
    socket.on("log_update", (data) => {
        if (Array.isArray(data.logs)) {
            logBoxElement.innerText = data.logs.join("\n");
        } else {
            logBoxElement.innerText = data.logs;
        }
    });

    // Start monitoring button
    document.getElementById("start-monitoring-btn").addEventListener("click", () => {
        socket.emit("start_monitoring", { interface: "wlan1" });
    });

    // Stop monitoring button
    document.getElementById("stop-monitoring-btn").addEventListener("click", () => {
        socket.emit("stop_monitoring");
    });

    // Send deauth request button
    document.getElementById("send-deauth-btn").addEventListener("click", () => {
        const targetAp = prompt("Enter target AP MAC address:");
        const targetClient = prompt("Enter target client MAC address (or leave blank for broadcast):");
        if (targetAp) {
            socket.emit("send_deauth", { target_ap: targetAp, target_client: targetClient || "FF:FF:FF:FF:FF:FF" });
        }
    });

    // Fetch logs on page load
    socket.emit("fetch_logs");
});