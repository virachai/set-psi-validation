async function loadDashboard() {
    try {
        const response = await fetch('../reports/metrics.json');
        if (!response.ok) throw new Error('Failed to load metrics.json');
        const data = await response.json();

        updateKPIs(data);
        renderAccuracyChart(data.history);
        renderHitRateChart(data.metrics.hit_rates);
        renderConfusionMatrix(data.confusion_matrix);
        renderHistoryTable(data.history);

        document.getElementById('last-updated').innerText = `Last updated: ${data.datePublished || 'N/A'}`;
    } catch (err) {
        console.error('Dashboard error:', err);
        alert('Could not load dashboard data. Ensure reports/metrics.json exists.');
    }
}

function updateKPIs(data) {
    const metrics = data.metrics;
    document.getElementById('accuracy-value').innerText = `${(metrics.overall_accuracy * 100).toFixed(1)}%`;
    document.getElementById('rolling-7d').innerText = `${(metrics.rolling_7d * 100).toFixed(1)}%`;
    document.getElementById('rolling-30d').innerText = `${(metrics.rolling_30d * 100).toFixed(1)}%`;
    document.getElementById('total-samples').innerText = metrics.total_count;
}

function renderAccuracyChart(history) {
    const ctx = document.getElementById('accuracyChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: history.map(h => h.date),
            datasets: [
                {
                    label: '7D Rolling Accuracy',
                    data: history.map(h => h.rolling_7d),
                    borderColor: '#3498db',
                    fill: false,
                    tension: 0.1
                },
                {
                    label: '30D Rolling Accuracy',
                    data: history.map(h => h.rolling_30d),
                    borderColor: '#2ecc71',
                    fill: false,
                    tension: 0.1
                }
            ]
        },
        options: {
            scales: {
                y: { min: 0, max: 1 }
            }
        }
    });
}

function renderHitRateChart(hitRates) {
    const ctx = document.getElementById('hitRateChart').getContext('2d');
    const labels = Object.keys(hitRates);
    const values = Object.values(hitRates).map(v => v === null ? 0 : v);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Recall (Hit Rate)',
                data: values,
                backgroundColor: '#3498db'
            }]
        },
        options: {
            scales: {
                y: { min: 0, max: 1 }
            }
        }
    });
}

function renderConfusionMatrix(matrix) {
    const container = document.getElementById('confusion-matrix-grid');
    const regimes = Object.keys(matrix);

    // Header row
    container.innerHTML = '<div class="matrix-cell matrix-header">Pred \\ Act</div>';
    regimes.forEach(r => {
        container.innerHTML += `<div class="matrix-cell matrix-header">${r}</div>`;
    });

    // Matrix rows
    regimes.forEach(pred => {
        container.innerHTML += `<div class="matrix-cell matrix-header">${pred}</div>`;
        regimes.forEach(act => {
            const val = matrix[pred][act] || 0;
            let heatClass = 'low';
            if (val > 5) heatClass = 'high';
            else if (val > 0) heatClass = 'mid';

            container.innerHTML += `<div class="matrix-cell matrix-value ${heatClass}">${val}</div>`;
        });
    });
}

function renderHistoryTable(history) {
    const tbody = document.querySelector('#history-table tbody');
    tbody.innerHTML = history.reverse().slice(0, 10).map(row => `
        <tr>
            <td>${row.date}</td>
            <td>${row.predicted}</td>
            <td>${row.actual}</td>
            <td class="${row.correct ? 'match' : 'mismatch'}">${row.correct ? 'MATCH' : 'MISMATCH'}</td>
        </tr>
    `).join('');
}

document.addEventListener('DOMContentLoaded', loadDashboard);
