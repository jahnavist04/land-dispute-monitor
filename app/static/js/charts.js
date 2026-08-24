// Enterprise Chart.js rendering functions for LandWatch Dashboard

const LUXURY_PALETTE = {
    critical: '#dc2626',
    high: '#ea580c',
    medium: '#d97706',
    low: '#16a34a',
    informational: '#64748b',
    active: '#16a34a',
    monitoring: '#4f46e5',
    resolved: '#64748b'
};

const dashboardCharts = {};

function replaceChart(canvasId, config) {
    if (dashboardCharts[canvasId]) dashboardCharts[canvasId].destroy();
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    dashboardCharts[canvasId] = new Chart(canvas, config);
}

function renderSeverityChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const labels = data.labels || [];
    const values = data.values || [];
    const colors = labels.map(l => LUXURY_PALETTE[l.toLowerCase()] || '#cbd5e1');

    replaceChart(canvasId, {
        type: 'doughnut',
        data: {
            labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1) + ' Risk'),
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 3,
                borderColor: '#ffffff',
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 15,
                        font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' }
                    }
                },
                tooltip: {
                    backgroundColor: '#0f172a',
                    padding: 10,
                    cornerRadius: 8,
                    bodyFont: { family: 'Plus Jakarta Sans', size: 12 }
                }
            },
            cutout: '70%'
        }
    });
}

function renderTimelineChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    // Generate gradient background
    const chartContext = ctx.getContext('2d');
    const gradient = chartContext.createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, 'rgba(37, 99, 235, 0.25)');
    gradient.addColorStop(1, 'rgba(37, 99, 235, 0.00)');

    replaceChart(canvasId, {
        type: 'line',
        data: {
            labels: data.labels && data.labels.length ? data.labels : ['Day 1', 'Day 5', 'Day 10', 'Day 15', 'Day 20', 'Day 25', 'Today'],
            datasets: [{
                label: 'Public Notices Parsed',
                data: data.values && data.values.length ? data.values : [2, 4, 7, 5, 9, 8, 12],
                borderColor: '#2563eb',
                backgroundColor: gradient,
                borderWidth: 2.5,
                fill: true,
                tension: 0.35,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#2563eb',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0f172a',
                    padding: 10,
                    cornerRadius: 8,
                    bodyFont: { family: 'Plus Jakarta Sans', size: 12 }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0, font: { family: 'JetBrains Mono', size: 10 } },
                    grid: { color: '#f1f5f9' },
                    border: { dash: [4, 4] }
                },
                x: {
                    ticks: { font: { family: 'Plus Jakarta Sans', size: 10 } },
                    grid: { display: false }
                }
            }
        }
    });
}

function renderLocationsChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    replaceChart(canvasId, {
        type: 'bar',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: 'Active Disputes',
                data: data.values || [],
                backgroundColor: '#2563eb',
                hoverBackgroundColor: '#1d4ed8',
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0f172a',
                    padding: 10,
                    cornerRadius: 8,
                    bodyFont: { family: 'Plus Jakarta Sans', size: 12 }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { precision: 0, font: { family: 'JetBrains Mono', size: 10 } },
                    grid: { color: '#f1f5f9' },
                    border: { dash: [4, 4] }
                },
                y: {
                    ticks: { font: { family: 'Plus Jakarta Sans', size: 10, weight: '500' } },
                    grid: { display: false }
                }
            }
        }
    });
}

function renderStatusChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const labels = data.labels || [];
    const values = data.values || [];
    const colors = labels.map(l => LUXURY_PALETTE[l.toLowerCase()] || '#cbd5e1');

    replaceChart(canvasId, {
        type: 'doughnut',
        data: {
            labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 3,
                borderColor: '#ffffff',
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 15,
                        font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' }
                    }
                },
                tooltip: {
                    backgroundColor: '#0f172a',
                    padding: 10,
                    cornerRadius: 8,
                    bodyFont: { family: 'Plus Jakarta Sans', size: 12 }
                }
            },
            cutout: '70%'
        }
    });
}
