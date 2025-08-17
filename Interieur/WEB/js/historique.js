const apiUrl = `/data`;
let allData = [];

// --- Graphique Température ---
const temperatureChart = new Chart(
    document.getElementById("temperatureChart").getContext("2d"),
    {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: "Température (°C)",
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.4, // Ligne lissée
                fill: true,   // Zone colorée
                pointRadius: 0,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            animation: {
                duration: 800,
                easing: 'easeOutBounce'
            },
            elements: {
                point: {
                    radius: 0,
                    hoverRadius: 5
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 10
                    },
                    title: {
                        display: true,
                        text: "Temps"
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: "Température (°C)"
                    }
                }
            }
        }
    }
);

// --- Graphique Humidité ---
const humidityChart = new Chart(
    document.getElementById("humidityChart").getContext("2d"),
    {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: "Humidité (%)",
                data: [],
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                tension: 0.4, // Ligne lissée
                fill: true,   // Zone colorée
                pointRadius: 0,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            animation: {
                duration: 800,
                easing: 'easeOutBounce'
            },
            elements: {
                point: {
                    radius: 0,
                    hoverRadius: 5
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 10
                    },
                    title: {
                        display: true,
                        text: "Temps"
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: "Humidité (%)"
                    }
                }
            }
        }
    }
);

function parseCustomDate(dateStr) {
    // Format attendu : "19/07/2025 14:32:10"
    const [datePart, timePart] = dateStr.split(' ');
    const [day, month, year] = datePart.split('/').map(Number);
    const [hours, minutes, seconds] = timePart.split(':').map(Number);
    return new Date(year, month - 1, day, hours, minutes, seconds);
}

function updateCharts(filteredData) {
    const labels = filteredData.map(entry => entry.time);
    const temps = filteredData.map(entry => entry.temperature);
    const humidities = filteredData.map(entry => entry.humidity);
    temperatureChart.data.labels = labels;
    temperatureChart.data.datasets[0].data = temps;
    temperatureChart.update();
    humidityChart.data.labels = labels;
    humidityChart.data.datasets[0].data = humidities;
    humidityChart.update();
}

function filterDataByDateRange(startDate, endDate) {
    const filtered = allData.filter(entry => {
        const entryDate = entry.timestamp;
        return entryDate >= startDate && entryDate <= endDate;
    });
    updateCharts(filtered);
}
async function loadData() {
    try {
        const response = await fetch(apiUrl);
        const jsonData = await response.json();
        allData = jsonData.map(entry => ({
            time: entry.time,
            timestamp: parseCustomDate(entry.time),
            temperature: parseFloat(entry.temperature),
            humidity: parseFloat(entry.humidity)
        }));
        allData.sort((a, b) => a.timestamp - b.timestamp);
    } catch (error) {
        console.error("Erreur lors du chargement des données :", error);
    }
}
document.getElementById("filterBtn").addEventListener("click", () => {
    const startInput = document.getElementById("startDateTime").value;
    const endInput = document.getElementById("endDateTime").value;
    if (!startInput || !endInput) {
        alert("Veuillez sélectionner une plage de date et heure.");
        return;
    }
    const startDate = new Date(startInput);
    const endDate = new Date(endInput);
    if (startDate > endDate) {
        alert("La date de début doit être antérieure à la date de fin.");
        return;
    }
    filterDataByDateRange(startDate, endDate);
});
document.getElementById("toggleDarkMode").addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
    const isDark = document.body.classList.contains("dark-mode");
    const button = document.getElementById("toggleDarkMode");
    button.innerHTML = isDark ? '<i class="fas fa-sun"></i> Désactiver le mode sombre' : '<i class="fas fa-moon"></i> Activer le mode sombre';
});
loadData();
document.getElementById("downloadCSV").addEventListener("click", () => {
    const startInput = document.getElementById("startDateTime").value;
    const endInput = document.getElementById("endDateTime").value;
    if (!startInput || !endInput) {
        alert("Veuillez sélectionner une plage de dates valide.");
        return;
    }
    const start = new Date(startInput);
    const end = new Date(endInput);
    const filtered = allData.filter(entry => {
        return entry.timestamp >= start && entry.timestamp <= end;
    });
    if (filtered.length === 0) {
        alert("Aucune donnée disponible pour cette plage.");
        return;
    }
    let csv = "Date/Heure,Température (°C),Humidité (%)\n";
    filtered.forEach(row => {
        csv += `${row.time},${row.temperature},${row.humidity}\n`;
    });
    const blob = new Blob([csv], {
        type: "text/csv"
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    // Nom dynamique basé sur la date du jour
    const now = new Date();
    const pad = n => n.toString().padStart(2, '0');
    const filename = `donnees_${pad(now.getDate())}-${pad(now.getMonth()+1)}-${now.getFullYear()}.csv`;
    a.download = filename;
    document.body.appendChild(a); // nécessaire pour Firefox
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});