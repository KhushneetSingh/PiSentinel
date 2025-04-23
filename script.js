// Simulated data for demonstration purposes
document.addEventListener("DOMContentLoaded", () => {
    const statusElement = document.getElementById("status");
    const logBoxElement = document.getElementById("log-box");

    // Update status
    statusElement.innerText = "Monitoring (Simulated)";

    // Update logs
    logBoxElement.innerText = `
[10:30:01] Monitor mode started on wlan1mon
[10:30:05] Beacon frame detected from 11:22:33:44:55:66
[10:30:10] Station 7C:D1:C3:34:AB:EF connected to AP 11:22:33:44:55:66
[10:31:22] Deauth attack initiated on 11:22:33:44:55:66
[10:31:25] Packets captured and saved to hacknet-01.cap
    `;
});