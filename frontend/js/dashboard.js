// API endpoints
const API_BASE = 'http://localhost:8000';
const ENDPOINTS = {
    devices: `${API_BASE}/devices`,
    count: `${API_BASE}/count`,
    manufacturers: `${API_BASE}/manufacturers`,
    scan: `${API_BASE}/scan`
};

// Chart instance
let manufacturerChart = null;

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeChart();
    setupEventListeners();
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

// Set up event listeners for scan control buttons
function setupEventListeners() {
    document.getElementById('startScan').addEventListener('click', startScan);
    document.getElementById('stopScan').addEventListener('click', stopScan);
}

// Update all dashboard components
async function updateDashboard() {
    try {
        await Promise.all([
            updateDeviceCount(),
            updateDeviceList(),
            updateManufacturerData()
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

// Start scanning
async function startScan() {
    try {
        const response = await fetch(ENDPOINTS.scan, { method: 'POST' });
        const data = await response.json();
        document.getElementById('scanStatus').textContent = 'Scanning';
        document.getElementById('scanStatus').classList.add('text-green-600');
    } catch (error) {
        console.error('Error starting scan:', error);
    }
}

// Stop scanning
async function stopScan() {
    try {
        const response = await fetch(ENDPOINTS.scan, { method: 'DELETE' });
        const data = await response.json();
        document.getElementById('scanStatus').textContent = 'Stopped';
        document.getElementById('scanStatus').classList.remove('text-green-600');
    } catch (error) {
        console.error('Error stopping scan:', error);
    }
}