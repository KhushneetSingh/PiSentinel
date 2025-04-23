const socket = io("http://<raspberry-pi-ip>:5000");

document.addEventListener("DOMContentLoaded", () => {
    const statusElement = document.getElementById("status");
    const logBoxElement = document.getElementById("log-box");

    socket.on("status_update", (data) => {
        statusElement.innerText = data.status;
    });

    socket.on("log_update", (data) => {
        logBoxElement.innerText = data.logs.join("\n");
    });

    document.getElementById("start-monitoring-btn").addEventListener("click", () => {
        socket.emit("start_monitoring", { interface: "wlan1mon" });
    });

    document.getElementById("stop-monitoring-btn").addEventListener("click", () => {
        socket.emit("stop_monitoring");
    });

    document.getElementById("send-deauth-btn").addEventListener("click", () => {
        const targetAp = prompt("Enter target AP MAC address:");
        const targetClient = prompt("Enter target client MAC address (or leave blank for broadcast):");
        if (targetAp) {
            socket.emit("send_deauth", { target_ap: targetAp, target_client: targetClient || "FF:FF:FF:FF:FF:FF" });
        }
    });
});