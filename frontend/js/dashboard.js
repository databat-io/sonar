// API endpoints
const API_BASE = 'http://localhost:8000';
const ENDPOINTS = {
    devices: `${API_BASE}/devices`,
    count: `${API_BASE}/count`,
    manufacturers: `${API_BASE}/manufacturers`,
    latest: `${API_BASE}/latest`
};

// Chart instance
let manufacturerChart = null;

// Scan interval (should match backend SCAN_INTERVAL_SECONDS)
const SCAN_INTERVAL_SECONDS = 30; // Adjust if your backend uses a different value

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeChart();
    updateDashboard();
    // Update every 5 seconds
    setInterval(updateDashboard, 5000);
});

// Initialize the manufacturer distribution chart
function initializeChart() {
    const ctx = document.getElementById('manufacturerChart').getContext('2d');
    manufacturerChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#3B82F6', // blue-500
                    '#10B981', // emerald-500
                    '#F59E0B', // amber-500
                    '#EF4444', // red-500
                    '#8B5CF6', // violet-500
                    '#EC4899', // pink-500
                    '#14B8A6', // teal-500
                    '#F97316', // orange-500
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// Update all dashboard components
async function updateDashboard() {
    try {
        await Promise.all([
            updateDeviceCount(),
            updateDeviceList(),
            updateManufacturerData(),
            updateScanStatus()
        ]);
    } catch (error) {
        console.error('Error updating dashboard:', error);
    }
}

// Update device count
async function updateDeviceCount() {
    try {
        const response = await fetch(ENDPOINTS.count);
        const data = await response.json();
        document.getElementById('deviceCount').textContent = data.count;
    } catch (error) {
        console.error('Error updating device count:', error);
    }
}

// Update device list
async function updateDeviceList() {
    try {
        const response = await fetch(ENDPOINTS.devices);
        const devices = await response.json();
        const deviceList = document.getElementById('deviceList');

        deviceList.innerHTML = devices.map(device => `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${device.address}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${device.manufacturer || 'Unknown'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${device.rssi} dBm</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error updating device list:', error);
    }
}

// Update manufacturer data and chart
async function updateManufacturerData() {
    try {
        const response = await fetch(ENDPOINTS.manufacturers);
        const manufacturers = await response.json();

        // Update manufacturer count
        document.getElementById('manufacturerCount').textContent = manufacturers.length;

        // Update chart
        manufacturerChart.data.labels = manufacturers.map(m => m.name || 'Unknown');
        manufacturerChart.data.datasets[0].data = manufacturers.map(m => m.count);
        manufacturerChart.update();
    } catch (error) {
        console.error('Error updating manufacturer data:', error);
    }
}

// Update scan status by checking the timestamp of the latest scan
async function updateScanStatus() {
    try {
        const response = await fetch(ENDPOINTS.latest);
        const data = await response.json();
        const scanStatusElem = document.getElementById('scanStatus');
        let status = 'Unknown';
        let colorClass = 'text-gray-900';
        if (data.current_scan && data.current_scan.session_stats) {
            // Check if the latest scan is recent
            const now = new Date();
            const lastScan = data.current_scan.timestamp || null;
            let isScanning = false;
            if (lastScan) {
                const lastScanDate = new Date(lastScan);
                const secondsAgo = (now - lastScanDate) / 1000;
                if (secondsAgo < SCAN_INTERVAL_SECONDS * 2) {
                    isScanning = true;
                }
            }
            status = isScanning ? 'Scanning' : 'Idle';
            colorClass = isScanning ? 'text-green-600' : 'text-yellow-600';
        }
        scanStatusElem.textContent = status;
        scanStatusElem.className = `text-2xl font-semibold ${colorClass}`;
    } catch (error) {
        document.getElementById('scanStatus').textContent = 'Unknown';
        document.getElementById('scanStatus').className = 'text-2xl font-semibold text-gray-900';
        console.error('Error updating scan status:', error);
    }
}